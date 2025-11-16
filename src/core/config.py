from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    서비스의 환경 변수를 관리하는 설정 클래스
    .env 파일로부터 값을 자동으로 로드합니다.
    """
    OPENAI_API_KEY: str


    STT_PROVIDER: str = "naver"
    TTS_PROVIDER: str = "naver"

    OPENAI_API_KEY: str
    LANGSMITH_TRACING: bool
    LANGSMITH_ENDPOINT: str
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str
    
    # Naver Cloud Platform (NCP)
    NCP_CLIENT_ID: str
    NCP_SECRET_KEY: str
    CLOVA_SPEECH_INVOKE_URL: str
    CLOVA_SPEECH_SECRET_KEY: str

    # Google Sheets
    DAILY_NOTES_GOOGLE_SHEET_ID: str
    GOOGLE_SHEETS_CREDENTIALS_PATH: str

    class Config:
        env_file = ".env"
try:
    settings = Settings()
except Exception as e:
    print(f"환경 변수 로딩 실패: .env 파일을 확인하세요. 오류: {e}")
