import unittest
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import Base
from models import Company, StockPrice
from schemas import StockDashboardResponse
import services.stock_service as stock_service

class TestStockBackend(unittest.TestCase):
    def setUp(self):
        # In-memory SQLite for testing
        self.engine = create_engine("sqlite:///:memory:")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = TestingSessionLocal()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)

    def test_company_creation(self):
        company = stock_service.get_or_create_company(self.db, "A32")
        self.assertIsNotNone(company)
        self.assertEqual(company.symbol, "A32")

    def test_update_stock_prices(self):
        company = stock_service.get_or_create_company(self.db, "A32")
        sample_data = [{
            "trading_date": datetime(2026, 8, 11),
            "close_price": 29.70,
            "open_price": 26.00,
            "high_price": 29.70,
            "low_price": 26.00,
            "volume": 400
        }]
        stock_service.update_stock_prices_in_db(self.db, company, sample_data)
        
        saved_price = self.db.query(StockPrice).filter(StockPrice.symbol == "A32").first()
        self.assertIsNotNone(saved_price)
        self.assertEqual(saved_price.close_price, 29.70)
        self.assertEqual(saved_price.volume, 400)
        self.assertIsNotNone(company.last_updated)

    def test_fallback_on_cafef_failure(self):
        # Insert initial stale data
        company = stock_service.get_or_create_company(self.db, "A32")
        stale_time = datetime.utcnow() - timedelta(hours=2)
        company.last_updated = stale_time
        
        sample_data = [{
            "trading_date": datetime(2026, 8, 10),
            "close_price": 29.00,
            "open_price": 25.50,
            "high_price": 29.50,
            "low_price": 25.00,
            "volume": 350
        }]
        stock_service.update_stock_prices_in_db(self.db, company, sample_data)
        company.last_updated = stale_time
        self.db.commit()

        # Query dashboard - should try refresh, and if CafeF fails or returns error, fallback to stale data
        res = stock_service.get_stock_dashboard(self.db, "A32")
        self.assertEqual(res.symbol, "A32")
        self.assertTrue(len(res.history) > 0)
        self.assertEqual(res.history[0].close_price, 29.00)

if __name__ == '__main__':
    unittest.main()
