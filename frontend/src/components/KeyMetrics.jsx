import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

export default function KeyMetrics({ latestMetrics }) {
  if (!latestMetrics) {
    return null;
  }

  const { close_price, open_price, high_price, low_price, volume } = latestMetrics;
  
  const priceChange = close_price - open_price;
  const percentChange = open_price > 0 ? (priceChange / open_price) * 100 : 0;
  const isPositive = priceChange >= 0;

  return (
    <div className="metrics-row">
      {/* Close Price */}
      <div className="metric-card">
        <span className="metric-title">Close</span>
        <span className="metric-value">{close_price.toFixed(2)}</span>
        <span className={`metric-sub ${isPositive ? 'positive' : 'negative'}`}>
          {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          {isPositive ? '+' : ''}{priceChange.toFixed(2)} ({isPositive ? '+' : ''}{percentChange.toFixed(2)}%)
        </span>
      </div>

      {/* Open Price */}
      <div className="metric-card">
        <span className="metric-title">Open</span>
        <span className="metric-value">{open_price.toFixed(2)}</span>
      </div>

      {/* High Price */}
      <div className="metric-card">
        <span className="metric-title">High</span>
        <span className="metric-value">{high_price.toFixed(2)}</span>
      </div>

      {/* Low Price */}
      <div className="metric-card">
        <span className="metric-title">Low</span>
        <span className="metric-value">{low_price.toFixed(2)}</span>
      </div>

      {/* Volume */}
      <div className="metric-card">
        <span className="metric-title">Volume</span>
        <span className="metric-value">{volume.toLocaleString('vi-VN')}</span>
      </div>
    </div>
  );
}
