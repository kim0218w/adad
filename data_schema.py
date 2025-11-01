from pydantic import BaseModel, Field

# '사건/일정' 정보 구성을 위한 구조
class ScheduleEvent(BaseModel):
    """회의에서 결정된 후속 조치 또는 일정을 위한 상세 정보"""
    
    # 1. 시간에 대한 내용
    event_date: str = Field(
        ...,
        description="일정의 날짜 또는 마감일. 구어체 표현을 반드시 YYYY-MM-DD 형식으로 계산하여 추출할 것."
    )
    event_time: str = Field(
        "10:00", # 기본값 지정 (시간이 명시되지 않으면 오전 10시 활용)
        description="일정의 시작 시간. HH:MM 형식 (24시간)."
    )
    
    # 2. 사건 (해야 하는 일, 약속 등 일정 내용)
    event_subject: str = Field(
        ...,
        description="일정의 주제나 사건 내용. (예: 마케팅 전략 최종 검토 회의, 김철수 고객 미팅 준비)"
    )

# 회의록 전체 분석 결과를 위한 최종 JSON 구조
class MeetingAnalysisResult(BaseModel):
    """회의록 분석 최종 결과"""
    
    event_details: ScheduleEvent = Field(
        ...,
        description="회의록에서 추출한 가장 중요하고 명확한 하나의 후속 일정 또는 사건 정보."
    )
    
    # 3. 전체 내용 요약본
    meeting_summary: str = Field(
        ...,
        description="요청하신 회의록 전체 내용에 대한 3~4줄 핵심 요약."
    )