import React, { useMemo } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';

// Helper to compute Simple Moving Average (SMA)
function calculateSMA(data, period = 20) {
  return data.map((item, index) => {
    if (index < period - 1) {
      return { ...item, sma20: null };
    }
    const slice = data.slice(index - period + 1, index + 1);
    const sum = slice.reduce((acc, curr) => acc + curr.close_price, 0);
    return { ...item, sma20: +(sum / period).toFixed(2) };
  });
}

export default function StockChart({ symbol, history, showVolume, showSMA }) {
  const chartData = useMemo(() => {
    if (!history || history.length === 0) return [];
    
    // Process dates for chart X-Axis
    const formatted = history.map((item) => {
      const dt = new Date(item.trading_date);
      const dateStr = dt.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
      return {
        ...item,
        formattedDate: dateStr
      };
    });

    return calculateSMA(formatted, 20);
  }, [history]);

  if (!history || history.length === 0) {
    return (
      <div className="state-box">
        <p>Chưa có dữ liệu lịch sử giá cho mã {symbol}.</p>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <div className="chart-header">
        <h2 className="chart-title">{symbol} - Price History</h2>
        
        <div className="chart-legend-custom">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#3b82f6' }}></div>
            <span>Close</span>
          </div>
          {showSMA && (
            <div className="legend-item">
              <div className="legend-color" style={{ backgroundColor: '#a855f7' }}></div>
              <span>SMA 20</span>
            </div>
          )}
          {showVolume && (
            <div className="legend-item">
              <div className="legend-color" style={{ backgroundColor: 'rgba(34, 197, 94, 0.4)' }}></div>
              <span>Volume</span>
            </div>
          )}
        </div>
      </div>

      <div style={{ width: '100%', height: 400 }}>
        <ResponsiveContainer>
          <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2e3446" vertical={false} />
            <XAxis
              dataKey="formattedDate"
              stroke="#6b7280"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <YAxis
              yAxisId="price"
              domain={['auto', 'auto']}
              stroke="#6b7280"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              orientation="left"
            />
            {showVolume && (
              <YAxis
                yAxisId="volume"
                orientation="right"
                domain={[0, 'auto']}
                hide={true}
              />
            )}

            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2430',
                borderColor: '#2e3446',
                borderRadius: '8px',
                color: '#f3f4f6',
                fontSize: '13px'
              }}
              formatter={(value, name) => {
                if (name === 'close_price') return [value, 'Giá đóng cửa'];
                if (name === 'sma20') return [value, 'SMA (20)'];
                if (name === 'volume') return [value.toLocaleString('vi-VN'), 'Khối lượng'];
                return [value, name];
              }}
            />

            {showVolume && (
              <Bar
                yAxisId="volume"
                dataKey="volume"
                fill="rgba(34, 197, 94, 0.25)"
                barSize={8}
              />
            )}

            <Line
              yAxisId="price"
              type="monotone"
              dataKey="close_price"
              stroke="#3b82f6"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 6, fill: '#3b82f6' }}
            />

            {showSMA && (
              <Line
                yAxisId="price"
                type="monotone"
                dataKey="sma20"
                stroke="#a855f7"
                strokeWidth={1.5}
                strokeDasharray="4 4"
                dot={false}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
