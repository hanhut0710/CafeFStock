import React from 'react';
import { Clock, AlertTriangle } from 'lucide-react';

export default function StatusBanner({ lastUpdated, isStale, warningMessage, totalObservations = 100 }) {
  const formatDate = (isoString) => {
    if (!isoString) return 'Chưa cập nhật';
    const date = new Date(isoString);
    return date.toLocaleString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className={`status-banner ${isStale ? 'stale' : ''}`}>
      <div className="status-banner-info">
        {isStale ? (
          <AlertTriangle size={18} />
        ) : (
          <span className="status-dot"></span>
        )}
        <span>
          <strong>
            {isStale ? 'Cảnh báo cập nhật:' : 'Đã nạp dữ liệu CafeF gần nhất:'}
          </strong>{' '}
          {formatDate(lastUpdated)}
          {totalObservations > 0 && ` • ${totalObservations} điểm dữ liệu`}
        </span>
      </div>

      {warningMessage && (
        <span style={{ fontSize: '0.8rem', opacity: 0.9 }}>
          ({warningMessage})
        </span>
      )}
    </div>
  );
}
