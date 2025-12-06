import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add backend to path to ensure we can load env correctly if needed
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
env_path = os.path.join(backend_path, ".env")

print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

database_url = os.getenv("DATABASE_URL")

if not database_url:
    print("❌ ERROR: DATABASE_URL not found in .env")
    sys.exit(1)

# Mask password for display
if "@" in database_url:
    prefix = database_url.split("@")[0]
    suffix = database_url.split("@")[1]
    # Hide password part
    if ":" in prefix:
        user = prefix.split(":")[1].split("//")[1]
        print(f"Checking connection to: postgres://{user}:****@{suffix}")
    else:
        print(f"Checking connection to: {database_url}")
else:
    print(f"Checking connection to: {database_url}")

# Fix for postgres://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(database_url)
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("✅ SUCCESS: Successfully connected to the database!")
except Exception as e:
    print(f"❌ FAILED: Could not connect to database.")
    print(f"Error: {e}")
    sys.exit(1)
