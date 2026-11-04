import React, { useState, useEffect, useRef, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import AnomalyMonitoring from './pages/AnomalyMonitoring';
import TrafficExplorer from './pages/TrafficExplorer';
import ModelInformation from './pages/ModelInformation';
import TestPredictionModal from './components/modals/TestPredictionModal';
import { getHealth, getStatistics, getTraffic, getAnomalies } from './services/api';

export default function App() {
  const [stats, setStats] = useState(null);
  const [traffic, setTraffic] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [isHealthy, setIsHealthy] = useState(true);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [pollInterval, setPollInterval] = useState(
    Number(import.meta.env.VITE_POLLING_INTERVAL_MS) || 12000
  );
  const [isTestModalOpen, setIsTestModalOpen] = useState(false);

  // Prevent overlapping asynchronous requests
  const isFetchingRef = useRef(false);

  const fetchTelemetry = useCallback(async (isBackground = false) => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;

    if (!isBackground) {
      setIsRefreshing(true);
    }

    try {
      // Parallel execution of real backend queries
      const [healthData, statsData, trafficData, anomaliesData] = await Promise.all([
        getHealth().catch(() => ({ status: 'offline', model_loaded: false })),
        getStatistics(),
        getTraffic({ limit: 100, offset: 0 }),
        getAnomalies({ limit: 100, offset: 0 }),
      ]);

      setIsHealthy(healthData.status === 'online' || healthData.status === 'healthy');
      setStats(statsData);
      setTraffic(trafficData);
      setAnomalies(anomaliesData);
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('[AegisAPI Telemetry Error]', err);
      setIsHealthy(false);
      setError(err.message || 'Cannot synchronize with AegisAPI backend.');
    } finally {
      isFetchingRef.current = false;
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchTelemetry(false);
  }, [fetchTelemetry]);

  // Polling interval timer
  useEffect(() => {
    if (!pollInterval || pollInterval <= 0) return;

    const timer = setInterval(() => {
      fetchTelemetry(true);
    }, pollInterval);

    return () => clearInterval(timer);
  }, [pollInterval, fetchTelemetry]);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <Layout
              lastUpdated={lastUpdated}
              isRefreshing={isRefreshing}
              onRefresh={() => fetchTelemetry(false)}
              pollInterval={pollInterval}
              onPollIntervalChange={setPollInterval}
              isHealthy={isHealthy}
              onOpenTestModal={() => setIsTestModalOpen(true)}
            />
          }
        >
          <Route
            index
            element={
              <Dashboard
                stats={stats}
                traffic={traffic}
                anomalies={anomalies}
                loading={loading}
                error={error}
                onRetry={() => fetchTelemetry(false)}
              />
            }
          />
          <Route
            path="anomalies"
            element={
              <AnomalyMonitoring
                anomalies={anomalies}
                loading={loading}
                error={error}
                onRefresh={() => fetchTelemetry(false)}
              />
            }
          />
          <Route
            path="traffic"
            element={
              <TrafficExplorer
                traffic={traffic}
                loading={loading}
                error={error}
                onRefresh={() => fetchTelemetry(false)}
              />
            }
          />
          <Route path="model-info" element={<ModelInformation />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>

      {/* Interactive Live Traffic Simulation Modal */}
      <TestPredictionModal
        isOpen={isTestModalOpen}
        onClose={() => setIsTestModalOpen(false)}
        onSuccess={() => fetchTelemetry(false)}
      />
    </BrowserRouter>
  );
}

