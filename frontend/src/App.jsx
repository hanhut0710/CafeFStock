import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import { fetchCompanies, fetchStockData, addCompany } from './services/api';

export default function App() {
  const [companies, setCompanies] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState('A32');
  const [stockData, setStockData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Toggle states for chart
  const [showVolume, setShowVolume] = useState(true);
  const [showSMA, setShowSMA] = useState(true);

  // Load companies list on mount
  useEffect(() => {
    loadCompanies();
  }, []);

  // Load stock data whenever selectedSymbol changes
  useEffect(() => {
    if (selectedSymbol) {
      loadStockData(selectedSymbol, false);
    }
  }, [selectedSymbol]);

  const loadCompanies = async () => {
    try {
      const data = await fetchCompanies();
      if (data.companies && data.companies.length > 0) {
        setCompanies(data.companies);
        // Default to A32 if present, otherwise first company
        const hasA32 = data.companies.some((c) => c.symbol === 'A32');
        if (!hasA32) {
          setSelectedSymbol(data.companies[0].symbol);
        }
      }
    } catch (err) {
      console.error('Failed to load companies:', err);
    }
  };

  const loadStockData = async (symbol, forceRefresh = false) => {
    if (forceRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const data = await fetchStockData(symbol, forceRefresh);
      setStockData(data);
    } catch (err) {
      console.error(`Error loading data for ${symbol}:`, err);
      setError(err.message || 'Lỗi kết nối server');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleSelectSymbol = (symbol) => {
    setSelectedSymbol(symbol);
  };

  const handleRefresh = () => {
    if (selectedSymbol) {
      loadStockData(selectedSymbol, true);
    }
  };

  const handleAddCompany = async (symbol) => {
    try {
      await addCompany(symbol);
      await loadCompanies();
      setSelectedSymbol(symbol);
    } catch (err) {
      alert(`Không thể thêm mã cổ phiếu ${symbol}: ${err.message}`);
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        companies={companies}
        selectedSymbol={selectedSymbol}
        onSelectSymbol={handleSelectSymbol}
        onAddCompany={handleAddCompany}
        onRefresh={handleRefresh}
        isRefreshing={isRefreshing}
        showVolume={showVolume}
        setShowVolume={setShowVolume}
        showSMA={showSMA}
        setShowSMA={setShowSMA}
      />
      <Dashboard
        stockData={stockData}
        isLoading={isLoading}
        error={error}
        showVolume={showVolume}
        showSMA={showSMA}
      />
    </div>
  );
}
