import os
import json
from datetime import date
from google import genai
from google.genai import types
from pydantic import ValidationError
from data_schema import MeetingAnalysisResult 

# 1. API 클라이언트 초기화 및 API 키 설정 확인
try:
    if not os.getenv("GEMINI_API_KEY"):
         raise EnvironmentError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
         
    client = genai.Client()
except Exception as e:
    print(f"❌ 클라이언트 초기화 오류: {e}")
    print("GEMINI_API_KEY 환경 변수가 설정되었는지 확인하세요.")
    exit()

def extract_meeting_data(meeting_text: str, reference_date: str) -> dict:
    """
    회의록 텍스트와 기준 날짜를 기반으로 Gemini API를 호출하여 구조화된 JSON을 추출합니다.
    """
    
    # 2. 프롬프트 정의: '사건(Subject)' 중심으로 지시사항 수정
    prompt = f"""
    당신은 회의록 분석 및 날짜 계산 전문가입니다. 이 회의록 분석의 **기준 날짜는 {reference_date}** 입니다.
    당신의 주 임무는 Google 캘린더에 등록할 **가장 중요하고 명확한 하나의 사건(일정)**을 추출하는 것입니다.

    1.  **사건(event_subject) 추출:** 회의록 내에서 결정된 다음 회의, 마감일, 미팅 준비 등 **가장 핵심적인 하나의 후속 사건의 내용**을 명확하게 추출하세요.
    2.  **날짜 및 시간 계산:** 사건과 관련된 날짜 표현(예: '다음 주 금요일', '모레')을 **기준 날짜를 기반으로 계산**하여 YYYY-MM-DD 형식의 절대 날짜(event_date)로 변환하세요.
    3.  **시간 추출:** 추출된 시간(event_time)은 HH:MM (24시간) 형식으로 합니다. 시간이 없다면 10:00을 사용하세요.
    4.  **요약:** 회의록 전체 내용 중 **결론 및 배경**을 담아 3~4문장으로 요약하여 meeting_summary 필드를 채우세요.

    분석 결과는 반드시 제공된 JSON 스키마(MeetingAnalysisResult)를 따라야 하며, **어떤 추가 설명이나 텍스트도 JSON 외부에 출력해서는 안 됩니다.**

    ---
    회의록 텍스트:
    {meeting_text}
    """
    
    # 3. 모델 설정 및 API 호출
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MeetingAnalysisResult,
            )
        )
        
        # 4. JSON 문자열을 파이썬 딕셔너리로 변환
        json_data = response.text.strip()
        
        # Pydantic을 사용하여 유효성 검사 및 딕셔너리로 변환
        parsed_data = MeetingAnalysisResult.model_validate_json(json_data).model_dump()
        
        return parsed_data
    
    except ValidationError as e:
        # 모델이 스키마를 따르지 못했을 경우의 오류 처리
        print(f"❌ Pydantic 유효성 검사 오류: 모델이 스키마를 따르지 않았습니다.")
        print(f"모델 출력 원본: {json_data}")
        print(f"오류: {e}")
        return None
    except Exception as e:
        print(f"❌ Gemini API 호출 중 오류 발생: {e}")
        return None

# ----------------------------------------------------------------------
# --- 테스트 실행: 오늘 날짜 자동 설정 및 함수 호출 ---
# ----------------------------------------------------------------------

sample_meeting_text = """
음 오늘 미팅 시작하겠습니당
지금 모바일 앱 런칭 관련 진행 상황 공유했고요
로그인 화면 좀 디자인 수정 필요하고 음 API쪽은 어제 테스트했는데 오류 하나 나와서 백엔드에서 다시 확인하기로 했어요

그리고 데이터베이스 구조는 내일 오전까지 초안 보내준다고 햇슴
QA팀은 테스트 케이스 지금 작성중이라 금욜까지 공유할거 같고요

아 그리고 마케팅팀은 베타 유저 모집 플랜 초안 다음주 수요일쯤 공유한다고 했습니다
음 그리고 앱 아이콘 그거 세가지 버전으로 다시 뽑아달라 요청했고 폰트 좀 크게 하는거 반영해야됨

할일 정리하면
프론트는 로그인 화면이랑 회원가입 화면 수정 들어가고
백엔드는 인증 API 문서 정리해서 내일 오전까지
QA는 테스트 케이스 금욜까지

다음 회의는 어 음 다음주 수요일 오후 두시에 잡고요
주제는 로그인 기능 통합테스트 상황 점검하고 UI 최종 확정 그리고 베타 유저 관련 플랜 확정하는걸로 할게요

예 오늘은 여기까지입니당
"""

# 시스템의 오늘 날짜를 가져와 YYYY-MM-DD 형식으로 설정 (기준 날짜)
today = date.today() 
reference_date = today.strftime("%Y-%m-%d") 

print(f"--- 분석 기준 날짜: {reference_date} (시스템 오늘 날짜) ---")
extracted_data = extract_meeting_data(
    meeting_text=sample_meeting_text,
    reference_date=reference_date # <-- 기준 날짜 전달
)

if extracted_data:
    print("\n✅ 성공적으로 추출된 최종 JSON 데이터 (프론트엔드로 전달할 형태):")
    print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
