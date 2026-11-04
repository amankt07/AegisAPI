"""
AegisAPI Backend Tests - SQLite Database Integration & Persistence
Tests engine connection, table creation, CRUD operations, foreign key cascades,
aggregations, transaction rollback, and session persistence.
"""
import os
import tempfile
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, init_db
from app.models import TrafficEvent, AnomalyPrediction, ModelInformation
from app.schemas import TrafficRecordInput, PredictionResponse
from app.services.database_service import DatabaseService


@pytest.fixture
def temp_db():
    """
    Creates an isolated file-backed temporary SQLite database for test suites.
    Cleans up the database file upon teardown.
    """
    db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    db_file.close()
    db_path = db_file.name
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Initialize tables
    init_db(custom_engine=engine)

    yield engine, TestingSessionLocal, db_path

    # Teardown
    engine.dispose()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


@pytest.fixture
def db_session(temp_db):
    """Yields a database session bound to the isolated temporary database."""
    _, TestingSessionLocal, _ = temp_db
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# 1. Database Connection Test
# ---------------------------------------------------------------------------
def test_database_connection(temp_db):
    """Verify that the SQLite engine connects successfully and executes queries."""
    engine, _, _ = temp_db
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1


# ---------------------------------------------------------------------------
# 2. Table Creation Test
# ---------------------------------------------------------------------------
def test_table_creation(temp_db):
    """Verify all required tables, columns, and primary keys exist in schema."""
    engine, _, _ = temp_db
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "traffic_events" in tables
    assert "anomaly_predictions" in tables
    assert "model_information" in tables

    # Verify traffic_events columns
    traffic_cols = {col["name"] for col in inspector.get_columns("traffic_events")}
    expected_traffic_cols = {
        "id", "timestamp", "source_ip", "endpoint", "http_method",
        "status_code", "response_time_ms", "request_size_bytes",
        "response_size_bytes", "requests_per_minute", "failed_requests", "user_agent"
    }
    assert expected_traffic_cols.issubset(traffic_cols)

    # Verify anomaly_predictions columns
    pred_cols = {col["name"] for col in inspector.get_columns("anomaly_predictions")}
    expected_pred_cols = {
        "id", "traffic_event_id", "timestamp", "is_anomaly",
        "prediction_label", "anomaly_score", "model_name"
    }
    assert expected_pred_cols.issubset(pred_cols)


# ---------------------------------------------------------------------------
# 3. Save Traffic Record Test
# ---------------------------------------------------------------------------
def test_save_traffic_record(db_session):
    """Verify storing a traffic record generates primary key and persists attributes."""
    service = DatabaseService()
    traffic_in = TrafficRecordInput(
        endpoint="/api/v1/orders",
        http_method="POST",
        status_code=201,
        response_time_ms=120.5,
        request_size_bytes=650,
        response_size_bytes=1024,
        requests_per_minute=22,
        failed_requests=0,
        source_ip="192.168.1.100",
        user_agent="PostmanRuntime/7.32.3",
    )
    pred_in = PredictionResponse(
        is_anomaly=0,
        prediction_label="Normal",
        threat_level="Safe",
        anomaly_score=0.0125,
        model_name="Isolation Forest",
        timestamp=datetime.now(timezone.utc),
    )

    event, pred = service.save_traffic_and_prediction(db_session, traffic_in, pred_in)
    assert event.id is not None
    assert event.endpoint == "/api/v1/orders"
    assert event.http_method == "POST"
    assert event.status_code == 201
    assert event.response_time_ms == 120.5


# ---------------------------------------------------------------------------
# 4. Save Anomaly Prediction Test
# ---------------------------------------------------------------------------
def test_save_anomaly_prediction(db_session):
    """Verify anomaly prediction record links with correct scores and labels."""
    service = DatabaseService()
    traffic_in = TrafficRecordInput(
        endpoint="/api/v1/auth/login",
        http_method="POST",
        status_code=401,
        response_time_ms=45.0,
        request_size_bytes=240,
        response_size_bytes=150,
        requests_per_minute=180,
        failed_requests=70,
        source_ip="10.0.0.99",
        user_agent="Hydra/9.5",
    )
    pred_in = PredictionResponse(
        is_anomaly=1,
        prediction_label="Anomaly",
        threat_level="Critical Threat",
        anomaly_score=0.285,
        model_name="Isolation Forest",
        timestamp=datetime.now(timezone.utc),
    )

    event, pred = service.save_traffic_and_prediction(db_session, traffic_in, pred_in)
    assert pred.id is not None
    assert pred.is_anomaly is True
    assert pred.prediction_label == "Anomaly"
    assert pred.anomaly_score == 0.285
    assert pred.model_name == "Isolation Forest"
    assert event.prediction.id == pred.id


# ---------------------------------------------------------------------------
# 5. Foreign Key Relationship & Cascade Delete Test
# ---------------------------------------------------------------------------
def test_foreign_key_relationship_and_cascade(db_session):
    """Verify bidirectional 1-to-1 relationship and cascade delete."""
    service = DatabaseService()
    traffic_in = TrafficRecordInput(
        endpoint="/api/v1/data",
        http_method="GET",
        status_code=200,
        response_time_ms=50.0,
    )
    pred_in = PredictionResponse(
        is_anomaly=0,
        prediction_label="Normal",
        threat_level="Safe",
        anomaly_score=0.01,
        model_name="Isolation Forest",
        timestamp=datetime.now(timezone.utc),
    )

    event, pred = service.save_traffic_and_prediction(db_session, traffic_in, pred_in)
    event_id = event.id
    pred_id = pred.id

    # Test reverse navigation
    prediction_record = db_session.query(AnomalyPrediction).filter_by(id=pred_id).first()
    assert prediction_record.traffic_event.id == event_id

    # Test cascade delete: deleting parent deletes child prediction
    db_session.delete(event)
    db_session.commit()

    assert db_session.query(TrafficEvent).filter_by(id=event_id).first() is None
    assert db_session.query(AnomalyPrediction).filter_by(id=pred_id).first() is None


# ---------------------------------------------------------------------------
# 6. Retrieve Recent Traffic Records Test
# ---------------------------------------------------------------------------
def test_retrieve_recent_traffic(db_session):
    """Verify retrieval of recent traffic events ordered descending with pagination."""
    service = DatabaseService()

    for i in range(10):
        traffic_in = TrafficRecordInput(
            endpoint=f"/api/v1/resource/{i}",
            http_method="GET",
            status_code=200,
            response_time_ms=30.0 + i,
        )
        pred_in = PredictionResponse(
            is_anomaly=0,
            prediction_label="Normal",
            threat_level="Safe",
            anomaly_score=0.01,
            model_name="Isolation Forest",
            timestamp=datetime.now(timezone.utc),
        )
        service.save_traffic_and_prediction(db_session, traffic_in, pred_in)

    # Limit 5, offset 0 -> newest 5
    recent = service.get_recent_traffic(db_session, limit=5, offset=0)
    assert len(recent) == 5
    assert recent[0].endpoint == "/api/v1/resource/9"
    assert recent[4].endpoint == "/api/v1/resource/5"

    # Limit 3, offset 5 -> items 6, 7, 8 in reverse order
    paged = service.get_recent_traffic(db_session, limit=3, offset=5)
    assert len(paged) == 3
    assert paged[0].endpoint == "/api/v1/resource/4"


# ---------------------------------------------------------------------------
# 7. Retrieve Anomalous Traffic Records Test
# ---------------------------------------------------------------------------
def test_retrieve_anomalous_traffic(db_session):
    """Verify retrieval filters only anomalous predictions."""
    service = DatabaseService()

    # Insert 3 normal, 2 anomalous
    for i in range(5):
        is_anom = i % 2 == 1  # i = 1, 3 are anomalous
        traffic_in = TrafficRecordInput(
            endpoint=f"/api/v1/anom_test/{i}",
            http_method="GET" if not is_anom else "POST",
            status_code=200 if not is_anom else 401,
            response_time_ms=50.0,
        )
        pred_in = PredictionResponse(
            is_anomaly=1 if is_anom else 0,
            prediction_label="Anomaly" if is_anom else "Normal",
            threat_level="High Threat" if is_anom else "Safe",
            anomaly_score=0.20 if is_anom else 0.02,
            model_name="Isolation Forest",
            timestamp=datetime.now(timezone.utc),
        )
        service.save_traffic_and_prediction(db_session, traffic_in, pred_in)

    anomalies = service.get_recent_anomalies(db_session, limit=10)
    assert len(anomalies) == 2
    for pred in anomalies:
        assert pred.is_anomaly is True
        assert pred.traffic_event is not None


# ---------------------------------------------------------------------------
# 8. Calculate Dashboard Statistics Test
# ---------------------------------------------------------------------------
def test_calculate_dashboard_statistics(db_session):
    """Verify SQL aggregation for dashboard metrics."""
    service = DatabaseService()

    # Seed 3 normal (200 OK, 40ms, 60ms, 50ms) and 1 anomalous (500 Error, 250ms)
    events_data = [
        ("/api/v1/users", "GET", 200, 40.0, 0),
        ("/api/v1/users", "GET", 200, 60.0, 0),
        ("/api/v1/items", "GET", 200, 50.0, 0),
        ("/api/v1/checkout", "POST", 500, 250.0, 1),
    ]

    for ep, meth, sc, lat, anom in events_data:
        traffic_in = TrafficRecordInput(
            endpoint=ep,
            http_method=meth,
            status_code=sc,
            response_time_ms=lat,
        )
        pred_in = PredictionResponse(
            is_anomaly=anom,
            prediction_label="Anomaly" if anom else "Normal",
            threat_level="Critical Threat" if anom else "Safe",
            anomaly_score=0.3 if anom else 0.01,
            model_name="Isolation Forest",
            timestamp=datetime.now(timezone.utc),
        )
        service.save_traffic_and_prediction(db_session, traffic_in, pred_in)

    stats = service.calculate_statistics(db_session)

    assert stats.total_processed_requests == 4
    assert stats.normal_requests == 3
    assert stats.anomalous_requests == 1
    assert stats.anomaly_percentage == 25.0
    # Avg latency = (40 + 60 + 50 + 250) / 4 = 100.0
    assert stats.average_response_time_ms == 100.0
    assert stats.http_error_count == 1  # 500 error
    assert "/api/v1/checkout" in stats.top_anomalous_endpoints
    assert stats.recent_traffic_volume == 4


# ---------------------------------------------------------------------------
# 9. Transaction Rollback on Error Test
# ---------------------------------------------------------------------------
def test_transaction_rollback_on_error(db_session):
    """Verify atomic transaction rollback prevents orphan records on error."""
    service = DatabaseService()

    # First record saves cleanly
    traffic_in = TrafficRecordInput(
        endpoint="/api/v1/good",
        http_method="GET",
        status_code=200,
        response_time_ms=30.0,
    )
    pred_in = PredictionResponse(
        is_anomaly=0,
        prediction_label="Normal",
        threat_level="Safe",
        anomaly_score=0.01,
        model_name="Isolation Forest",
        timestamp=datetime.now(timezone.utc),
    )
    service.save_traffic_and_prediction(db_session, traffic_in, pred_in)

    initial_events = db_session.query(TrafficEvent).count()
    initial_preds = db_session.query(AnomalyPrediction).count()
    assert initial_events == 1
    assert initial_preds == 1

    # Corrupt or trigger DB error inside nested transaction
    with pytest.raises(Exception):
        with db_session.begin_nested():
            bad_pred = AnomalyPrediction(
                traffic_event_id=99999,
                is_anomaly=True,
                prediction_label="Anomaly",
                anomaly_score="NOT_A_FLOAT",
                model_name="Test",
            )
            db_session.add(bad_pred)
            db_session.flush()

    db_session.rollback()

    # Confirm count is unchanged
    assert db_session.query(TrafficEvent).count() == initial_events
    assert db_session.query(AnomalyPrediction).count() == initial_preds


# ---------------------------------------------------------------------------
# 10. Data Persistence Across Reopened Sessions Test
# ---------------------------------------------------------------------------
def test_data_persistence_across_sessions(temp_db):
    """Verify records written to SQLite file persist across engine/session closure."""
    engine, TestingSessionLocal, db_path = temp_db
    service = DatabaseService()

    # Session 1: Write record
    session1 = TestingSessionLocal()
    traffic_in = TrafficRecordInput(
        endpoint="/api/v1/persisted",
        http_method="POST",
        status_code=201,
        response_time_ms=88.0,
        source_ip="192.168.1.200",
    )
    pred_in = PredictionResponse(
        is_anomaly=1,
        prediction_label="Anomaly",
        threat_level="High Threat",
        anomaly_score=0.195,
        model_name="Isolation Forest",
        timestamp=datetime.now(timezone.utc),
    )
    saved_event, _ = service.save_traffic_and_prediction(session1, traffic_in, pred_in)
    saved_id = saved_event.id
    session1.close()

    # Close first engine entirely
    engine.dispose()

    # Reopen fresh engine and session pointing to the same file
    new_engine = create_engine(f"sqlite:///{db_path}")
    NewSession = sessionmaker(bind=new_engine)
    session2 = NewSession()

    try:
        loaded_event = session2.query(TrafficEvent).filter_by(id=saved_id).first()
        assert loaded_event is not None
        assert loaded_event.endpoint == "/api/v1/persisted"
        assert loaded_event.http_method == "POST"
        assert loaded_event.status_code == 201
        assert loaded_event.prediction.is_anomaly is True
        assert loaded_event.prediction.prediction_label == "Anomaly"
        assert round(loaded_event.prediction.anomaly_score, 3) == 0.195
    finally:
        session2.close()
        new_engine.dispose()
