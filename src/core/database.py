from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "./")))
from config import settings

# 엔진 생성 (echo=True로 하면 실행되는 SQL이 로그에 찍힘 - 디버깅용)
engine = create_engine(
    settings.DATABASE_URL, # 연결 DB 주소
    pool_pre_ping=True, # DB 연결 관리 - 접속 끊김 방지
    echo=True # DB 로그
)

# 세션 로컬 생성 (실제 DB 작업을 수행하는 객체)
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine) # autoflush는 테이블 조회 전 파이선 메모리(session)에 있는 DB 변경 사항을 반영

# ORM 모델들이 상속받을 Base 클래스
Base = declarative_base()
