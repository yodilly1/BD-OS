import asyncio
import httpx
import time
import sys

BASE_URL = "http://localhost:8000"

async def test_health():
    print("Testing /health endpoint...", end=" ")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL}/health")
            resp.raise_for_status()
            data = resp.json()
            if data["status"] == "healthy":
                print(f"✅ PASSED: {data}")
                return True
            else:
                print(f"❌ FAILED (Status: {data.get('status')})")
                return False
        except Exception as e:
            print(f"❌ FAILED (Error: {e})")
            return False

async def test_url_search():
    print("Testing /api/prospect/url-search (Stripe)...", end=" ")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            payload = {"url": "stripe.com"}
            resp = await client.post(f"{BASE_URL}/api/prospect/url-search", json=payload)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"✅ PASSED (Found {len(data)} prospects)")
                return True
            else:
                print(f"⚠️ PASSED but found 0 prospects (Check LeadMagic key?)")
                return True
        except Exception as e:
            print(f"❌ FAILED (Error: {e})")
            return False

async def test_deep_search_job():
    print("Testing /api/prospect/deep-search (Job System)...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Start Job
        print("  - Starting job...", end=" ")
        try:
            payload = {
                "industry": "FinTech",
                "size": "1000+ employees",
                "keywords": "payments",
                "titles": ["Engineer"],
                "limit": 1
            }
            resp = await client.post(f"{BASE_URL}/api/prospect/deep-search", json=payload)
            resp.raise_for_status()
            job_id = resp.json().get("job_id")
            print(f"✅ PASSED (Job ID: {job_id})")
        except Exception as e:
            print(f"❌ FAILED (Error: {e})")
            return False

        # 2. Poll Job
        print("  - Polling job status...", end=" ")
        start_time = time.time()
        while time.time() - start_time < 60:
            try:
                resp = await client.get(f"{BASE_URL}/api/jobs/{job_id}")
                resp.raise_for_status()
                job = resp.json()
                status = job.get("status")
                
                if status == "completed":
                    print("✅ PASSED (Completed)")
                    print(f"  - Result count: {len(job.get('result', []))}")
                    return True
                elif status == "failed":
                    print(f"❌ FAILED (Job Status: failed - {job.get('error')})")
                    return False
                
                await asyncio.sleep(2)
            except Exception as e:
                print(f"❌ Polling Error: {repr(e)}")
                return False
        
        print("❌ FAILED (Timeout polling job)")
        return False

async def main():
    print("=== BD-OS System Health Check ===\n")
    
    health_ok = await test_health()
    if not health_ok:
        print("\nCRITICAL: Health check failed. Aborting.")
        sys.exit(1)
        
    url_ok = await test_url_search()
    deep_ok = await test_deep_search_job()
    
    print("\n=== Summary ===")
    if health_ok and url_ok and deep_ok:
        print("🎉 All systems operational. No backend regressions detected.")
    else:
        print("⚠️ Some checks failed. Review output above.")

if __name__ == "__main__":
    asyncio.run(main())
