import React, { useState } from 'react';
import { RefreshCw, Search, Plus, BarChart2, CheckSquare, Square } from 'lucide-react';

export default function Sidebar({
  companies,
  selectedSymbol,
  onSelectSymbol,
  onAddCompany,
  onRefresh,
  isRefreshing,
  showVolume,
  setShowVolume,
  showSMA,
  setShowSMA
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [newSymbol, setNewSymbol] = useState('');

  const filteredCompanies = companies.filter((c) =>
    c.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleAddSubmit = (e) => {
    e.preventDefault();
    if (newSymbol.trim()) {
      onAddCompany(newSymbol.trim().toUpperCase());
      setNewSymbol('');
    }
  };

  return (
    <aside className="sidebar">
      {/* App Header */}
      <div className="sidebar-header">
        <div className="sidebar-logo">CF</div>
        <div>
          <h1 className="sidebar-title">CafeF Stock</h1>
        </div>
      </div>

      {/* Manual Refresh Button */}
      <button 
        className="refresh-btn" 
        onClick={onRefresh} 
        disabled={isRefreshing}
        title="Làm mới dữ liệu từ CafeF"
      >
        <RefreshCw size={14} className={isRefreshing ? 'spinner' : ''} />
        <span>{isRefreshing ? 'Đang nạp...' : 'Refresh CafeF data'}</span>
      </button>

      {/* Symbol List Section */}
      <div className="sidebar-section">
        <div className="section-label">Chart - Mã cổ phiếu</div>
        
        {/* Search */}
        <div className="search-box">
          <Search size={14} color="#6b7280" />
          <input
            type="text"
            placeholder="Search mã cổ phiếu..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        {/* List */}
        <div className="symbol-list">
          {filteredCompanies.map((c) => (
            <div
              key={c.symbol}
              className={`symbol-item ${selectedSymbol === c.symbol ? 'active' : ''}`}
              onClick={() => onSelectSymbol(c.symbol)}
            >
              <span>{c.symbol}</span>
            </div>
          ))}
          {filteredCompanies.length === 0 && (
            <div style={{ color: '#6b7280', fontSize: '0.8rem', padding: '0.5rem' }}>
              Không tìm thấy mã cổ phiếu.
            </div>
          )}
        </div>

        {/* Add Company */}
        <form onSubmit={handleAddSubmit} className="add-company-form">
          <input
            type="text"
            placeholder="Thêm mã (VD: VNM)..."
            value={newSymbol}
            onChange={(e) => setNewSymbol(e.target.value)}
          />
          <button type="submit" title="Thêm mã cổ phiếu mới">
            <Plus size={16} />
          </button>
        </form>
      </div>

      {/* Display Options Section */}
      <div className="sidebar-section">
        <div className="section-label">Tùy chọn hiển thị</div>
        <div className="indicator-toggles">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showVolume}
              onChange={(e) => setShowVolume(e.target.checked)}
            />
            <span>Khối lượng (Volume)</span>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={showSMA}
              onChange={(e) => setShowSMA(e.target.checked)}
            />
            <span>Đường trung bình (SMA 20)</span>
          </label>
        </div>
      </div>
    </aside>
  );
}
