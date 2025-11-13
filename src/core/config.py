from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    OPEN_API_KEY: str

    STT_PROVIDER: str = "naver"
    TTS_PROVIDER: str = "naver"

    class Config:
        env_file = ".env"