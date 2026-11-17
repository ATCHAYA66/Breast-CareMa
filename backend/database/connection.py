from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def run_migrations():
    """
    Ensures newly added columns (such as patient_id) exist in SQLite tables.
    """
    with engine.connect() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(diagnoses)"))
            columns = [row[1] for row in res.fetchall()]
            if columns and "patient_id" not in columns:
                conn.execute(text("ALTER TABLE diagnoses ADD COLUMN patient_id VARCHAR(50)"))
                conn.commit()
                print("[Database Migration] Added 'patient_id' column to 'diagnoses' table.")
        except Exception as e:
            print(f"[Database Migration] Notice: {e}")
