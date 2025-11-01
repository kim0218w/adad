import os
import json
from datetime import datetime # 파일명에 사용할 타임스탬프를 위해 추가
# STT 모듈에서 텍스트 변환 함수를 임포트합니다.
from stt_module import run_stt_conversion 

# Gemini API 클라이언트 및 타입 임포트
from google.genai import Client, types
from pydantic import ValidationError
from data_schema import MeetingAnalysisResult # Pydantic 클래스 임포트

# ----------------------------------------------------
# 1. GEMINI 구조화 분석 로직
# ----------------------------------------------------

# API 클라이언트 초기화 (환경 변수 GEMINI_API_KEY 사용)
try:
    # 환경 변수가 설정되지 않은 경우 오류를 발생시키고 종료합니다.
    if not os.getenv("GEMINI_API_KEY"):
         raise EnvironmentError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. 시스템 환경 변수를 확인하세요.")
         
    client = Client()
    print("✅ Gemini Client 초기화 완료.")
except Exception as e:
    print(f"❌ 클라이언트 초기화 오류: {e}")
    exit()


def extract_meeting_data(meeting_text: str) -> dict:
    """
    STT 결과를 받아 구조화된 JSON 데이터를 추출합니다.
    """
    # 2. 프롬프트 정의
    prompt = f"""
    당신은 전문 회의록 분석가입니다. 다음 회의록 텍스트를 분석하여,
    제공된 **MeetingAnalysisResult** JSON 스키마에 따라 데이터를 정확하게 추출하세요.

    **[추출 지시 사항]**
    1. **'meeting_summary'**: 회의록 전체 내용에 대한 간결하고 핵심적인 요약(3~4줄)을 작성하세요.
    2. **'next_schedules'**: 다음 회의 또는 후속 일정에 대한 상세 정보 객체를 구성해야 합니다.
        a. **next_schedule_date**: 후속 일정의 날짜를 **YYYY-MM-DD** 형식으로 추출하세요.
        b. **start_time**: 후속 일정의 시간을 **HH:MM** 형식으로 추출하세요. 시간이 명시되지 않았다면, **기본값 '10:00'**을 사용해야 합니다.
        c. **event_title**: 구글 캘린더 이벤트의 **제목 (Title/Summary)**에 들어갈 핵심 제목을 추출하세요.
        d. **event_content**: 구글 캘린더 이벤트의 **내용/본문 (Content/Description)**에 들어갈 상세 설명을 **2~3줄**로 작성하세요. 이 내용은 해당 후속 조치가 필요한 배경과 목표를 설명해야 합니다.
    
    분석 결과는 반드시 제공된 JSON 스키마의 중첩 구조를 따라야 합니다.
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
        
        # 4. JSON 문자열을 파이썬 딕셔너리로 변환 및 Pydantic 유효성 검사
        json_data = response.text.strip()
        parsed_data = MeetingAnalysisResult.model_validate_json(json_data).model_dump()
        return parsed_data
    
    except ValidationError as e:
        print(f"❌ Pydantic 유효성 검사 오류: 모델이 스키마를 따르지 않았습니다. 오류 상세: {e}")
        return None
    except Exception as e:
        print(f"❌ Gemini API 호출 중 오류 발생: {e}")
        return None

# ----------------------------------------------------
# 5. 메인 실행 로직
# ----------------------------------------------------

# TODO: ⭐️⭐️⭐️ 오디오 파일 경로를 여기에 실제 파일명으로 수정하세요.
AUDIO_FILE = "voice.m4a"

print(f"--- 1단계: STT 모듈 호출 및 텍스트 추출 ({AUDIO_FILE}) ---")
# stt_module.py의 함수를 호출하여 텍스트를 받습니다.
meeting_transcript = run_stt_conversion(AUDIO_FILE) 

# STT 결과가 비어있으면, Gemini 분석을 위해 시뮬레이션 텍스트로 대체
if not meeting_transcript:
    print("⚠️ STT 변환 실패. Gemini 분석을 위해 시뮬레이션 텍스트로 대체하여 진행합니다.")
    # 시뮬레이션 텍스트 (실제 회의록 내용과 유사한 샘플)
    meeting_transcript = """
    아, 네. 이번 주차 마케팅 회의 시작할게요. 지난주에 우리가 광고 성과를 분석했잖아요. 
    보니까 A 채널 효율이 좀 떨어져서 다음 달 예산을 조정해야 할 것 같습니다. 
    김 팀장님, 다음 주 화요일에 최종 예산안을 정리해서 보고해 주시고요, 
    시간은 오전 10시로 잡겠습니다. 장소는 그냥 회의실에서 간단하게 해요. 
    그리고 이 문제에 대한 팀원들의 의견을 수렴해서 예산 삭감의 배경과 
    앞으로의 대체 전략을 구체적으로 문서에 담아주세요. 날짜는 2025년 11월 12일로 정했어요. 
    다른 안건 없으시면 회의 마칠게요.
    """


print("\n--- 2단계: Gemini API로 텍스트 분석 및 구조화 ---")
extracted_data = extract_meeting_data(meeting_transcript)

if extracted_data:
    # ----------------------------------------------------
    # JSON 파일 저장 로직 추가
    # ----------------------------------------------------
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"analysis_output_{timestamp}.json"
    
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        print(f"✅ JSON 파일 저장 성공: {output_filename}")
    except IOError as e:
        print(f"❌ JSON 파일 저장 오류: {e}")

    print("\n✅ 성공적으로 추출된 최종 JSON 데이터 (Gemini Output):")
    # 최종 JSON 데이터를 보기 좋게 출력
    print(json.dumps(extracted_data, indent=2, ensure_ascii=False))
else:
    print("❌ 데이터 추출에 실패했습니다. (Pydantic 유효성 검사 또는 API 오류 확인)")