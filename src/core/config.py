from pydantic_settings import BaseSettings, SettingsConfigDict

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

    # MySQL
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT:int = 3306
    DB_NAME: str

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # .env에 정의되지 않은 변수가 있어도 무시함 (에러 방지)
    )
try:
    settings = Settings()
except Exception as e:
    print(f"환경 변수 로딩 실패: .env 파일을 확인하세요. 오류: {e}")
