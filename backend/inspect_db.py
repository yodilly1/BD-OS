from sqlmodel import Session, select
from app.db import engine
from app.models.prospect import Prospect
from app.models.company import Company

def inspect_db():
    with Session(engine) as session:
        prospects = session.exec(select(Prospect)).all()
        print(f"Found {len(prospects)} prospects:")
        for p in prospects:
            company = session.get(Company, p.company_id)
            company_name = company.name if company else "Unknown"
            company_domain = company.domain if company else "Unknown"
            print(f"- {p.first_name} {p.last_name} ({p.title}) at {company_name} ({company_domain})")
            print(f"  Email: {p.email}, Phone: {p.phone}")

if __name__ == "__main__":
    inspect_db()
