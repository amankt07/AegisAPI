"""
AegisAPI - Database Configuration & Session Management
Configures SQLite engine, declarative base, session generator,
and automatic table schema initialization for production and testing.
"""
import json
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Resolve default database file path inside backend/aegisapi.db
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
DEFAULT_DB_PATH = os.path.join(BACKEND_DIR, "aegisapi.db")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite in multi-threaded FastAPI
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session per request
    and guarantees safe closure upon completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(custom_engine=None):
    """
    Initializes database tables and synchronizes active model metadata.
    Avoids duplicate model records on subsequent application restarts.
    """
    from app import models  # Ensure all model tables are registered with Base.metadata

    target_engine = custom_engine or engine
    Base.metadata.create_all(bind=target_engine)

    # Automatically register active champion model metadata if not present
    target_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)
    db = target_session_factory()
    try:
        # Load model_metadata.json from models directory
        env_models_dir = os.getenv("MODELS_DIR")
        if env_models_dir and os.path.exists(env_models_dir):
            models_dir = os.path.abspath(env_models_dir)
        else:
            models_dir = os.path.abspath(os.path.join(BACKEND_DIR, "..", "models"))
        meta_path = os.path.join(models_dir, "model_metadata.json")

        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                metadata = json.load(f)

            model_name = metadata.get("model_name", "Isolation Forest")
            algorithm = metadata.get("algorithm", "sklearn.ensemble._iforest.IsolationForest")

            existing = (
                db.query(models.ModelInformation)
                .filter(
                    models.ModelInformation.model_name == model_name,
                    models.ModelInformation.algorithm == algorithm,
                )
                .first()
            )

            if not existing:
                eval_metrics = metadata.get("evaluation_metrics", {})
                training_records = metadata.get("dataset", {}).get("train_records", 24000)
                feature_count = metadata.get("dataset", {}).get("feature_count", 42)
                training_date = metadata.get("training_date", "")

                new_model_info = models.ModelInformation(
                    model_name=model_name,
                    algorithm=algorithm,
                    training_date=training_date,
                    training_records=training_records,
                    feature_count=feature_count,
                    evaluation_metrics=eval_metrics,
                    is_active=True,
                )
                db.add(new_model_info)
                db.commit()
    except Exception as e:
        db.rollback()
        # Non-fatal during test/custom setup
        print(f"[Database Init Warning] Could not sync model metadata: {e}")
    finally:
        db.close()
