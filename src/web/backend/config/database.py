import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

database_url = (
    f"singlestoredb://"
    f"{os.getenv('singlestore_user')}:"
    f"{os.getenv('singlestore_password')}@"
    f"{os.getenv('singlestore_host')}:"
    f"{os.getenv('singlestore_port')}/"
    f"{os.getenv('singlestore_db')}"
)

# kiểm tra xem kết nối đến db được không trước khi sử dụng
engine = create_engine(database_url, pool_pre_ping=True) 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        print("Database session closed.")

if __name__ == "__main__":
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("SingleStore connection successful:", result.scalar())
    except Exception as e:
        print("SingleStore connection failed:", str(e))
