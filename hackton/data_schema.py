from pydantic import BaseModel, Field
from typing import List

# 캘린더에 들어갈 상세 일정 정보를 위한 구조
class NextSchedule(BaseModel):
    """다음 회의 또는 후속 일정에 대한 상세 정보"""
    next_schedule_date: str = Field(
        ...,
        description="다음 회의 또는 후속 일정의 날짜. 반드시 YYYY-MM-DD 형식으로 추출할 것."
    )
    start_time: str = Field(
        "10:00", # 회의록에 시간이 없으면 오전 10시로 기본 설정
        description="일정 시작 시간. HH:MM 형식 (24시간)."
    )
    event_title: str = Field(
        ...,
        description="추출된 다음 회의 또는 후속 일정의 구글 캘린더 제목(Title/Summary)."
    )
    event_content: str = Field(
        ...,
        description="추출된 다음 회의 또는 후속 일정의 구글 캘린더 내용/본문(Content/Description). 2~3줄로 작성."
    )

# 회의록 전체 분석 결과를 위한 최종 JSON 구조
class MeetingAnalysisResult(BaseModel):
    """회의록 분석 최종 결과"""
    meeting_summary: str = Field(
        ...,
        description="회의록 전체 내용에 대한 3~4줄 핵심 요약."
    )
    next_schedules: List[NextSchedule] = Field(
        ...,
        description="회의에서 결정된 다음 회의 또는 일정 정보 리스트."
    )
