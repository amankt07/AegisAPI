"""
AegisAPI Backend Tests - Model Service Unit Tests
"""
import pytest
from app.schemas import TrafficRecordInput
from app.services.model_service import ModelService, model_service


def test_model_service_is_loaded():
    """Verify production model service is healthy and loaded."""
    assert model_service.is_loaded is True
    assert model_service.model is not None
    assert model_service.scaler is not None
    assert model_service.schema is not None
    assert model_service.schema["total_features"] == 42


def test_model_service_feature_transformation():
    """Verify input records transform into a 42-feature dataframe."""
    record = TrafficRecordInput(
        endpoint="/api/v1/products",
        http_method="GET",
        status_code=200,
        response_time_ms=65.0,
        request_size_bytes=200,
        response_size_bytes=3000,
        requests_per_minute=12,
        failed_requests=0,
    )
    X_df = model_service._transform_records_to_features([record])
    assert X_df.shape == (1, 42)
    assert list(X_df.columns) == model_service.schema["feature_names"]


def test_model_service_missing_directory_failure():
    """Verify safe failure handling when artifacts directory is invalid."""
    bad_service = ModelService(models_dir="/non/existent/path")
    assert bad_service.is_loaded is False
    assert bad_service.error_message is not None

    # Should raise RuntimeError if inference is attempted
    record = TrafficRecordInput(
        endpoint="/api/v1/products",
        http_method="GET",
        status_code=200,
        response_time_ms=50.0,
    )
    with pytest.raises(RuntimeError):
        bad_service.predict_single(record)

