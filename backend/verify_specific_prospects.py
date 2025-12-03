import asyncio

from app.agents.prospector import ProspectorAgent
from app.db import create_db_and_tables


async def main():
    create_db_and_tables()
    prospector = ProspectorAgent()

    print("\n--- Debugging Derric Lee (Missing Phone) ---")
    await prospector.manual_prospecting_flow(
        first_name="Derric", last_name="Lee", domain="snorkel.ai"
    )

    print("\n--- Debugging Robert Gibson (Missing Email) ---")
    await prospector.manual_prospecting_flow(
        first_name="Robert", last_name="Gibson", domain="nucleussecurity.com"
    )


if __name__ == "__main__":
    asyncio.run(main())
