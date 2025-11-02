import json
import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, redirect, request, session
from flask_cors import CORS
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests as google_requests
from jose import JWTError, jwt
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)

    app.config.update(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32)),
        SESSION_COOKIE_NAME=os.getenv("SESSION_COOKIE_NAME", "hack_bluebird_session"),
        JSON_AS_ASCII=False,
    )

    raw_origins = os.getenv("CLIENT_ORIGINS", "")
    allowed_origins = [
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip()
    ]
    if not allowed_origins:
        allowed_origins = [
            "http://localhost:8081",
            "http://127.0.0.1:8081",
            "http://localhost:19006",
            "http://127.0.0.1:19006",
        ]

    CORS(
        app,
        supports_credentials=True,
        resources={r"/*": {"origins": allowed_origins}},
    )

    database_path = os.getenv(
        "DATABASE_URL", os.path.join(os.path.dirname(__file__), "app.db")
    )
    jwt_secret = os.getenv("JWT_SECRET", app.config["SECRET_KEY"])
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    token_ttl_seconds = int(os.getenv("JWT_TTL_SECONDS", "3600"))

    google_redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/google/callback"
    )
    google_scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]
    google_userinfo_endpoint = "https://openidconnect.googleapis.com/v1/userinfo"
    success_redirect = os.getenv("GOOGLE_OAUTH_SUCCESS_REDIRECT")
    client_section_key = "app"

    def get_db() -> sqlite3.Connection:
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db() -> None:
        with get_db() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    nickname TEXT,
                    google_id TEXT UNIQUE,
                    google_picture TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    init_db()

    def to_user_dict(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "email": row["email"],
            "nickname": row["nickname"],
            "google_picture": row["google_picture"],
        }

    def issue_token(user: sqlite3.Row) -> str:
        now = datetime.utcnow()
        payload = {
            "sub": str(user["id"]),
            "email": user["email"],
            "nickname": user["nickname"],
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=token_ttl_seconds)).timestamp()),
        }
        return jwt.encode(payload, jwt_secret, algorithm=jwt_algorithm)

    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        try:
            return jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
        except JWTError:
            return None

    def sync_google_user(
        email: str,
        google_id: str,
        nickname: Optional[str],
        picture: Optional[str],
    ) -> sqlite3.Row:
        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE google_id = ? OR email = ?",
                (google_id, email),
            ).fetchone()

            if user:
                conn.execute(
                    """
                    UPDATE users
                    SET google_id = ?, google_picture = ?, nickname = COALESCE(?, nickname)
                    WHERE id = ?
                    """,
                    (google_id, picture, nickname, user["id"]),
                )
            else:
                created_at = datetime.utcnow().isoformat()
                conn.execute(
                    """
                    INSERT INTO users (email, nickname, google_id, google_picture, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (email, nickname, google_id, picture, created_at),
                )
            conn.commit()
            user = conn.execute(
                "SELECT * FROM users WHERE google_id = ?", (google_id,)
            ).fetchone()

        if not user:
            raise RuntimeError("Failed to synchronize Google user information.")
        return user

    def require_google_config() -> Dict[str, Any]:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        project_id = os.getenv("GOOGLE_PROJECT_ID")
        redirect_uris: list[str] = []

        secrets_locations = [
            os.getenv("GOOGLE_CLIENT_SECRETS_FILE"),
            os.path.join(os.path.dirname(__file__), "client_secret.json"),
            os.path.join(os.path.dirname(__file__), "Calendar", "client_secret.json"),
        ]

        def load_from_section(section: Dict[str, Any]) -> None:
            nonlocal client_id, client_secret, project_id, redirect_uris
            client_id = client_id or section.get("client_id")
            client_secret = client_secret or section.get("client_secret")
            project_id = project_id or section.get("project_id")
            redirect_candidates = section.get("redirect_uris") or section.get(
                "redirectUris"
            )
            if redirect_candidates:
                redirect_uris = list({*redirect_uris, *redirect_candidates})

        for path in secrets_locations:
            if not path:
                continue
            if not os.path.exists(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as file:
                    raw_config = json.load(file)
            except (OSError, json.JSONDecodeError):
                continue

            if isinstance(raw_config, dict):
                for key in (client_section_key, "web", "installed"):
                    section = raw_config.get(key)
                    if isinstance(section, dict):
                        load_from_section(section)
                        if client_id:
                            break
            if client_id:
                break

        if not client_id:
            raise RuntimeError("Google OAuth is not configured. Set GOOGLE_CLIENT_ID.")

        project_id = project_id or "hack-bluebird"
        if not redirect_uris:
            redirect_uris = [google_redirect_uri]
        elif google_redirect_uri not in redirect_uris:
            redirect_uris.append(google_redirect_uri)

        config = {
            client_section_key: {
                "client_id": client_id,
                "project_id": project_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": redirect_uris,
                "userinfo_endpoint": google_userinfo_endpoint,
            }
        }
        if client_secret:
            config[client_section_key]["client_secret"] = client_secret
        return config

    @app.get("/")
    def index() -> Response:
        return jsonify({"status": "ok", "service": "Hack BlueBird API"})

    @app.post("/auth/register")
    def register() -> Response:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        nickname = (data.get("nickname") or "").strip()

        if not email or not password or not nickname:
            return jsonify({"error": "필수 항목이 누락되었습니다"}), 400

        if len(password) < 6:
            return jsonify({"error": "비밀번호는 6자 이상이어야 합니다"}), 400

        password_hash = generate_password_hash(password)
        created_at = datetime.utcnow().isoformat()

        with get_db() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO users (email, password_hash, nickname, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (email, password_hash, nickname, created_at),
                )
                conn.commit()
            except sqlite3.IntegrityError:
                return jsonify({"error": "이미 사용 중인 이메일입니다"}), 409

            user = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

        token = issue_token(user)
        return (
            jsonify(
                {
                    "message": "회원가입이 완료되었습니다",
                    "token": token,
                    "user": to_user_dict(user),
                }
            ),
            201,
        )

    @app.post("/auth/login")
    def login() -> Response:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        if not email or not password:
            return jsonify({"error": "이메일과 비밀번호를 모두 입력해주세요"}), 400

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

        if not user or not user["password_hash"]:
            return jsonify({"error": "이메일 또는 비밀번호가 올바르지 않습니다"}), 401

        if not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "이메일 또는 비밀번호가 올바르지 않습니다"}), 401

        token = issue_token(user)
        return jsonify({"message": "로그인에 성공했습니다", "token": token, "user": to_user_dict(user)})

    @app.get("/auth/me")
    def me() -> Response:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "인증 토큰이 필요합니다"}), 401
        token = auth_header.split(" ", 1)[1]
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "유효하지 않은 토큰입니다"}), 401

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE id = ?", (payload["sub"],)
            ).fetchone()

        if not user:
            return jsonify({"error": "사용자를 찾을 수 없습니다"}), 404

        return jsonify({"user": to_user_dict(user)})

    def wants_json_response() -> bool:
        format_hint = (
            request.args.get("format")
            or request.args.get("response_type")
            or ""
        ).lower()
        if format_hint == "json":
            return True
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return True
        accept = request.headers.get("Accept") or ""
        if "application/json" in accept and "text/html" not in accept:
            return True
        return False

    client_section_key = "app"

    @app.get("/auth/google/login")
    def google_login() -> Response:
        client_config = require_google_config()
        client_section = client_config.get(client_section_key, {})
        if "client_secret" not in client_section:
            return (
                jsonify(
                    {
                        "error": "서버에서 Google OAuth 코드를 처리하려면 GOOGLE_CLIENT_SECRET이 필요합니다.",
                        "hint": "모바일 앱에서는 POST /auth/google/token 엔드포인트에 ID 토큰을 전달하세요.",
                    }
                ),
                501,
            )
        flow = Flow.from_client_config(
            client_config,
            scopes=google_scopes,
            redirect_uri=google_redirect_uri,
            client_type=client_section_key,
        )

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        session["google_oauth_state"] = state
        redirect_to = request.args.get("redirect_to")
        if redirect_to:
            session["google_oauth_redirect_to"] = redirect_to
        if wants_json_response():
            return jsonify({"authorization_url": authorization_url, "state": state})

        return redirect(authorization_url)

    @app.get("/auth/google/callback")
    def google_callback() -> Response:
        state = session.get("google_oauth_state")
        if not state:
            return jsonify({"error": "OAuth 세션이 만료되었습니다"}), 400

        client_config = require_google_config()
        client_section = client_config.get(client_section_key, {})
        if "client_secret" not in client_section:
            return (
                jsonify(
                    {
                        "error": "GOOGLE_CLIENT_SECRET이 없어 OAuth 코드를 처리할 수 없습니다.",
                        "hint": "대신 POST /auth/google/token 엔드포인트를 사용하세요.",
                    }
                ),
                501,
            )
        flow = Flow.from_client_config(
            client_config,
            scopes=google_scopes,
            state=state,
            redirect_uri=google_redirect_uri,
            client_type=client_section_key,
        )

        try:
            flow.fetch_token(authorization_response=request.url)
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": "토큰을 가져오지 못했습니다", "detail": str(exc)}), 400

        session.pop("google_oauth_state", None)

        credentials = flow.credentials
        if not credentials.id_token:
            return jsonify({"error": "ID 토큰을 확인할 수 없습니다"}), 400

        try:
            google_profile = id_token.verify_oauth2_token(
                credentials.id_token,
                google_requests.Request(),
                audience=client_section["client_id"],
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": "ID 토큰 검증에 실패했습니다", "detail": str(exc)}), 400

        email = google_profile.get("email", "").lower()
        google_id = google_profile.get("sub")
        nickname = google_profile.get("name") or (email.split("@")[0] if email else None)
        picture = google_profile.get("picture")

        if not email or not google_id:
            return jsonify({"error": "Google 계정 정보를 가져오지 못했습니다"}), 400

        user = sync_google_user(email, google_id, nickname, picture)

        token = issue_token(user)
        result = {
            "message": "Google OAuth 로그인에 성공했습니다",
            "token": token,
            "user": to_user_dict(user),
        }

        if wants_json_response():
            return jsonify(result)

        redirect_to = session.pop("google_oauth_redirect_to", None) or success_redirect
        if redirect_to:
            separator = "&" if "?" in redirect_to else "?"
            return redirect(f"{redirect_to}{separator}token={token}")

        payload = json.dumps(result)
        script = f"""
        <!doctype html>
        <html lang="ko">
        <head>
            <meta charset="utf-8" />
            <title>Google OAuth 완료</title>
        </head>
        <body>
            <script>
                (function () {{
                    var payload = {payload!r};
                    try {{
                        var data = JSON.parse(payload);
                        if (window.opener) {{
                            window.opener.postMessage(data, "*");
                        }} else if (window.parent && window.parent !== window) {{
                            window.parent.postMessage(data, "*");
                        }}
                    }} catch (err) {{
                        console.error("Failed to postMessage", err);
                    }}
                    window.close();
                }})();
            </script>
            <p>로그인이 완료되었습니다. 이 창을 닫아주세요.</p>
        </body>
        </html>
        """
        return Response(script, mimetype="text/html")

    @app.post("/auth/google/token")
    def google_token_login() -> Response:
        client_config = require_google_config()
        client_section = client_config.get(client_section_key, {})
        client_id = client_section["client_id"]

        data = request.get_json(silent=True) or {}
        raw_id_token = (data.get("id_token") or "").strip()
        if not raw_id_token:
            return jsonify({"error": "id_token 필드가 필요합니다"}), 400

        try:
            google_profile = id_token.verify_oauth2_token(
                raw_id_token,
                google_requests.Request(),
                audience=client_id,
            )
        except Exception as exc:  # noqa: BLE001
            return jsonify({"error": "ID 토큰 검증에 실패했습니다", "detail": str(exc)}), 400

        email = (google_profile.get("email") or "").lower()
        google_id = google_profile.get("sub")
        nickname = google_profile.get("name") or (email.split("@")[0] if email else None)
        picture = google_profile.get("picture")

        if not email or not google_id:
            return jsonify({"error": "Google 계정 정보를 가져오지 못했습니다"}), 400

        user = sync_google_user(email, google_id, nickname, picture)
        token = issue_token(user)
        return jsonify(
            {
                "message": "Google OAuth 로그인에 성공했습니다",
                "token": token,
                "user": to_user_dict(user),
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() in {"1", "true", "yes"}
    app.run(host="0.0.0.0", port=port, debug=debug)
