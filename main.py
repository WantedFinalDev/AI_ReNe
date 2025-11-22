from sqlalchemy import text
from src.core.database import engine

def test_db_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"\n✅ 데이터베이스 연결 성공! (MySQL Response: {result.scalar()}")

            db_name = conn.execute(text("SELECT DATABASE()")).scalar()
            print(f"\n✅ 데이터베이스 연결 성공! (Database Name: {db_name}")

    except Exception as e:
        print("\n❌ 데이터베이스 연결 실패...")
        print(f"에러 메시지: {e}\n")

if __name__ == "__main__":
    test_db_connection()