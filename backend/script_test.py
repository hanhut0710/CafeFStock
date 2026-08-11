from database import SessionLocal
from models import Company

db = SessionLocal()

company = (
    db.query(Company)
    .filter(Company.symbol == "ACB")
    .first()
)

print("BEFORE API")
print("symbol:", company.symbol)
print("last_updated:", company.last_updated)

db.close()