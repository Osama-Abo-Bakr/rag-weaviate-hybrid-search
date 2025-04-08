import os
import logging
import json
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_database_url():
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    if None in [db_user, db_password, db_host, db_port, db_name]:
        raise ValueError("❌ Missing database environment variables!")

    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Database configuration
DATABASE_URL = get_database_url()

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # Helps with dropped connections
)

# Create session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db_connection():
    """
    Provides a new database session from the connection pool.
    """
    try:
        db = SessionLocal()
        logging.info("✅ PostgreSQL database session acquired")
        return db
    except Exception as e:
        logging.error(f"❌ Error acquiring database session: {e}")
        return None

def create_chat_history_table():
    """
    Creates the chat_history table if it does not exist (PostgreSQL version with JSONB).
    """
    db = get_db_connection()
    if not db:
        logging.error("❌ Database session failed. Cannot create table.")
        return
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                vector_id TEXT NOT NULL UNIQUE,
                chat_history JSONB NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.commit()
        logging.info("✅ Table 'chat_history' created successfully (PostgreSQL with JSONB).")
    except Exception as e:
        logging.error(f"❌ Error creating table: {e}")
    finally:
        db.close()

def delete_chat_history_table():
    """
    Drops the chat_history table if it exists.
    """
    db = get_db_connection()
    if not db:
        logging.error("❌ Database session failed. Cannot delete table.")
        return
    try:
        db.execute(text("DROP TABLE IF EXISTS chat_history"))
        db.commit()
        logging.info("✅ Table 'chat_history' deleted successfully (PostgreSQL).")
    except Exception as e:
        logging.error(f"❌ Error deleting table: {e}")
    finally:
        db.close()

def get_chat_history(vector_id):
    """
    Retrieve the chat history for a given vector_id.
    """
    db = get_db_connection()
    if not db:
        logging.error("❌ Database session failed. Cannot retrieve chat history.")
        return []
    try:
        result = db.execute(
            text("""
                SELECT chat_history
                FROM chat_history
                WHERE vector_id = :vector_id
                ORDER BY timestamp DESC
            """),
            {"vector_id": vector_id}
        ).fetchone()
        
        # return json.loads(result[0]) if result else []
        return result[0] if result else []
    except Exception as e:
        logging.error(f"❌ Error retrieving chat history: {e}")
        return []
    finally:
        db.close()

def save_chat_history(chat_history, user_id, project_id, vector_id):
    """
    Save a user's query and the chatbot's response to the chat history table using JSONB.
    """
    db = get_db_connection()
    if not db:
        logging.error("❌ Database session failed. Chat history not saved.")
        return
    try:        
        db.execute(
            text("""
                INSERT INTO chat_history (user_id, project_id, vector_id, chat_history)
                VALUES (:user_id, :project_id, :vector_id, :chat_history)
                ON CONFLICT (vector_id) 
                DO UPDATE SET chat_history = EXCLUDED.chat_history
            """),
            {"user_id": user_id, "project_id": project_id, "vector_id": vector_id, "chat_history": json.dumps(chat_history)}
        )
        db.commit()
        logging.info("✅ Chat history saved successfully (PostgreSQL with JSONB).")
    except Exception as e:
        logging.error(f"❌ Error saving chat history: {e}")
        db.rollback()
    finally:
        db.close()