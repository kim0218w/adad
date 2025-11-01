import os
import sys

# ----------------------------------------------------
# 1. WHISPER 라이브러리 및 모델 로드
# ----------------------------------------------------

# NOTE: 이 모듈을 사용하기 전, 'pip install openai-whisper'와 FFmpeg 설치가 필수입니다.
try:
    import whisper
except ImportError:
    # 라이브러리 설치가 안 된 경우 실행을 중단하고 사용자에게 안내합니다.
    print("❌ [STT Error] 'openai-whisper' 라이브러리가 설치되지 않았습니다.")
    print("      설치를 위해 VS Code 터미널에서 'pip install openai-whisper'를 실행하세요.")
    sys.exit(1)

WHISPER_MODEL = None
try:
    # 모델은 모듈 로드 시점에 한 번만 로드하여 성능을 최적화합니다.
    # 한국어 처리에 적합한 'small' 모델을 로드합니다.
    WHISPER_MODEL = whisper.load_model("small")
    print("✅ [STT Module] Whisper 모델 로드 완료: small (최초 실행 시 다운로드될 수 있음)")
except Exception as e:
    # FFmpeg 경로 설정 오류 등 환경 문제를 포착합니다.
    print(f"❌ [STT Error] Whisper 모델 로드 실패. FFmpeg PATH 및 라이브러리 설치 확인 필요.")
    print(f"      오류 상세: {e}")
    # FFmpeg 오류로 인해 모델 로드 자체가 안되면, STT 기능을 사용할 수 없으므로 종료합니다.
    sys.exit(1)

# ----------------------------------------------------
# 2. STT 실행 함수
# ----------------------------------------------------

def run_stt_conversion(audio_file_path: str) -> str:
    """
    오디오 파일 경로를 받아 Whisper를 사용하여 텍스트로 변환합니다.

    이 함수는 FFmpeg와 Whisper가 올바르게 설정되었다고 가정하고 실행됩니다.

    :param audio_file_path: 오디오 파일의 절대 또는 상대 경로
    :return: 변환된 회의록 텍스트 (실패 시 빈 문자열)
    """
    if not os.path.exists(audio_file_path):
        print(f"❌ [STT Error] 오디오 파일 경로를 찾을 수 없습니다: {audio_file_path}")
        return ""
        
    if WHISPER_MODEL is None:
        print("❌ [STT Error] Whisper 모델이 초기화되지 않아 STT를 실행할 수 없습니다.")
        return ""

    print(f"🔊 [STT Module] 오디오 파일 변환 시작: {audio_file_path}")
    try:
        # 한국어 (ko) 지정 및 처리 (정확도 향상)
        result = WHISPER_MODEL.transcribe(audio_file_path, language="ko")
        print("✅ [STT Module] Whisper 변환 성공.")
        return result["text"]
    except Exception as e:
        # 변환 중 발생할 수 있는 오류를 처리합니다.
        print(f"❌ [STT Error] Whisper 변환 중 치명적인 오류 발생: {e}")
        return ""