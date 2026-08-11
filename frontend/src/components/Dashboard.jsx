import React from 'react';
import StatusBanner from './StatusBanner';
import KeyMetrics from './KeyMetrics';
import StockChart from './StockChart';
import { AlertCircle } from 'lucide-react';

export default function Dashboard({ stockData, isLoading, error, showVolume, showSMA }) {
  if (isLoading) {
    return (
      <main className="main-content">
        <div className="state-box">
          <div className="spinner"></div>
          <p style={{ marginTop: '1rem' }}>Đang nạp dữ liệu từ CafeF...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="main-content">
        <div className="state-box" style={{ borderColor: 'rgba(239, 68, 68, 0.4)' }}>
          <AlertCircle size={40} color="#ef4444" />
          <h3 style={{ color: '#ef4444' }}>Không thể tải dữ liệu</h3>
          <p>{error}</p>
        </div>
      </main>
    );
  }

  if (!stockData) {
    return (
      <main className="main-content">
        <div className="state-box">
          <p>Vui lòng chọn một mã cổ phiếu từ danh sách bên trái.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="main-content">
      {/* Prominent Last Updated Banner */}
      <StatusBanner
        lastUpdated={stockData.last_updated}
        isStale={stockData.is_stale}
        warningMessage={stockData.warning_message}
        totalObservations={stockData.history ? stockData.history.length : 0}
      />

      {/* Key Metrics Row */}
      <KeyMetrics latestMetrics={stockData.latest_metrics} />

      {/* Line Chart */}
      <StockChart
        symbol={stockData.symbol}
        history={stockData.history}
        showVolume={showVolume}
        showSMA={showSMA}
      />
    </main>
  );
}
