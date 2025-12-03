import asyncio

from app.agents.prospector import ProspectorAgent
from app.db import create_db_and_tables


async def main():
    create_db_and_tables()
    prospector = ProspectorAgent()

    print("--- Testing Manual Add ---")
    # Use a known test case
    first = "Derric"
    last = "Lee"
    domain = "snorkel.ai"

    print(f"Adding: {first} {last} @ {domain}")
    prospect = await prospector.manual_prospecting_flow(first, last, domain)

    if prospect:
        print("\n--- Result ---")
        print(f"Name: {prospect.first_name} {prospect.last_name}")
        print(f"Email: {prospect.email}")
        print(f"Phone: {prospect.phone}")
        print(f"LinkedIn: {prospect.linkedin_url}")
        print(f"Status: {prospect.status}")
    else:
        print("No prospect found/created.")


if __name__ == "__main__":
    asyncio.run(main())
