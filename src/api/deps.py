## 데이터베이스 세션 관리, 사용자 인증 및 권한 관리, 의존성 주입 모듈
from typing import Generator
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from src.core.database import SessionLocal

# DB 세션 생성기 (Dependency)
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


    
