"""
AegisAPI - Traffic & Telemetry Store Service
Manages real-time log ingestion buffers, stores detected anomaly incidents,
and computes dynamic statistics for security dashboard consumption.
"""
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, List, Optional
import pandas as pd

from app.schemas import (
    AnomalyEvent,
    DashboardStatistics,
    PredictionResponse,
    TrafficEvent,
    TrafficRecordInput,
)


class TrafficService:
    """
    In-memory thread-safe telemetry store maintaining recent traffic events,
    flagged anomalies, and aggregated security KPIs.
    """

    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self._events: deque = deque(maxlen=max_events)
        self._anomalies: deque = deque(maxlen=max_events)
        self._lock = Lock()
        self._counter: int = 0

        # Running KPI accumulators
        self.total_processed: int = 0
        self.normal_count: int = 0
        self.anomalous_count: int = 0
        self.http_error_count: int = 0
        self.total_latency_ms: float = 0.0

        self.threat_counts: Dict[str, int] = {
            "Safe": 0,
            "Low Threat": 0,
            "Medium Threat": 0,
            "High Threat": 0,
            "Critical Threat": 0,
        }
        self.anomalous_endpoints: Dict[str, int] = {}

    def record_event(self, record: TrafficRecordInput, prediction: PredictionResponse) -> TrafficEvent:
        """Record an inspected traffic event and update running aggregations."""
        with self._lock:
            self._counter += 1
            event_id = self._counter

            event = TrafficEvent(
                id=event_id,
                timestamp=prediction.timestamp,
                source_ip=record.source_ip or "127.0.0.1",
                endpoint=record.endpoint,
                http_method=record.http_method,
                status_code=record.status_code,
                response_time_ms=record.response_time_ms,
                request_size_bytes=record.request_size_bytes,
                response_size_bytes=record.response_size_bytes,
                requests_per_minute=record.requests_per_minute,
                failed_requests=record.failed_requests,
                user_agent=record.user_agent or "Unknown",
                is_anomaly=prediction.is_anomaly,
                prediction_label=prediction.prediction_label,
                anomaly_score=prediction.anomaly_score,
                threat_level=prediction.threat_level,
            )

            self._events.append(event)
            self.total_processed += 1
            self.total_latency_ms += record.response_time_ms

            if record.status_code >= 400:
                self.http_error_count += 1

            if prediction.threat_level in self.threat_counts:
                self.threat_counts[prediction.threat_level] += 1
            else:
                self.threat_counts[prediction.threat_level] = 1

            if prediction.is_anomaly == 1:
                self.anomalous_count += 1
                anomaly_evt = AnomalyEvent(
                    id=event_id,
                    timestamp=prediction.timestamp,
                    source_ip=record.source_ip or "127.0.0.1",
                    endpoint=record.endpoint,
                    http_method=record.http_method,
                    status_code=record.status_code,
                    response_time_ms=record.response_time_ms,
                    request_size_bytes=record.request_size_bytes,
                    response_size_bytes=record.response_size_bytes,
                    requests_per_minute=record.requests_per_minute,
                    failed_requests=record.failed_requests,
                    anomaly_score=prediction.anomaly_score,
                    threat_level=prediction.threat_level,
                )
                self._anomalies.append(anomaly_evt)

                # Track endpoint frequency
                ep = record.endpoint
                self.anomalous_endpoints[ep] = self.anomalous_endpoints.get(ep, 0) + 1
            else:
                self.normal_count += 1

            return event

    def record_batch(
        self, records: List[TrafficRecordInput], predictions: List[PredictionResponse]
    ) -> List[TrafficEvent]:
        """Record a batch of inspected events in a single locked transaction."""
        created_events: List[TrafficEvent] = []
        for rec, pred in zip(records, predictions):
            evt = self.record_event(rec, pred)
            created_events.append(evt)
        return created_events

    def get_recent_traffic(self, limit: int = 50, offset: int = 0) -> List[TrafficEvent]:
        """Fetch chronological recent traffic events (most recent first)."""
        with self._lock:
            all_events = list(self._events)
            all_events.reverse()  # Newest first
            return all_events[offset : offset + limit]

    def get_recent_anomalies(self, limit: int = 50, offset: int = 0) -> List[AnomalyEvent]:
        """Fetch chronological recent anomaly events (most recent first)."""
        with self._lock:
            all_anomalies = list(self._anomalies)
            all_anomalies.reverse()  # Newest first
            return all_anomalies[offset : offset + limit]

    def get_statistics(self) -> DashboardStatistics:
        """Compute aggregated dashboard telemetry statistics."""
        with self._lock:
            tot = self.total_processed
            anom = self.anomalous_count
            norm = self.normal_count
            anom_pct = round((anom / tot * 100.0), 2) if tot > 0 else 0.0
            avg_latency = round((self.total_latency_ms / tot), 2) if tot > 0 else 0.0

            # Sort top 5 anomalous endpoints
            sorted_endpoints = dict(
                sorted(self.anomalous_endpoints.items(), key=lambda item: item[1], reverse=True)[:5]
            )

            return DashboardStatistics(
                total_processed_requests=tot,
                normal_requests=norm,
                anomalous_requests=anom,
                anomaly_percentage=anom_pct,
                average_response_time_ms=avg_latency,
                http_error_count=self.http_error_count,
                threat_level_distribution=dict(self.threat_counts),
                top_anomalous_endpoints=sorted_endpoints,
            )

    def clear(self):
        """Reset all in-memory buffers (used for testing)."""
        with self._lock:
            self._events.clear()
            self._anomalies.clear()
            self._counter = 0
            self.total_processed = 0
            self.normal_count = 0
            self.anomalous_count = 0
            self.http_error_count = 0
            self.total_latency_ms = 0.0
            self.threat_counts = {
                "Safe": 0,
                "Low Threat": 0,
                "Medium Threat": 0,
                "High Threat": 0,
                "Critical Threat": 0,
            }
            self.anomalous_endpoints.clear()


# Global traffic service instance
traffic_service = TrafficService()

