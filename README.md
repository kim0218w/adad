지능형SW codessey 문제 풀이 코드 올리는 곳

data_schema.py
gemini_extractor.py 
환경변수 지정 : 시스템변수 
환경변수명 : GEMINI_API_KEY
본인 gemini_api 사용해서 설정후 실행

#프로잭트 개요 
1. 음성을 텍스트로 변환 -> 2. 텍스트를 Gemini로 데이터 추출( 시간(년/월/일/시), 요약, 장소), 3. 데이터를 Google Calendar에 저장 -> 4. 저장한 데이터 알림 ->  (선택사항) 중요도에 따른 알림 중요도 표시, 시전 조절

#개발환경 맞추기 
python 3.10.0 <= 3.12.0

# STT 모델 
VOSK, Whisper, google stt

# 
