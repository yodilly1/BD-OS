# Deploying BD-OS to the Web (Railway.app)

This guide explains how to deploy BD-OS to **Railway**, a simple platform that handles hosting, SSL, and databases for you. It is perfect for internal tools.

## Prerequisites
1.  A GitHub account.
2.  This code pushed to a GitHub repository.

## Step 1: Create a Railway Account
1.  Go to [railway.app](https://railway.app/).
2.  Login with GitHub.

## Step 2: Create a New Project
1.  Click **"New Project"**.
2.  Select **"Deploy from GitHub repo"**.
3.  Select your `BD-OS` repository.
4.  Click **"Deploy Now"**.

## Step 3: Configure Services
Railway will detect the `docker-compose.yml` but it's often easier to deploy the Backend and Frontend as two services in the same project.

### Option A: Monorepo Deployment (Recommended)
Railway allows you to deploy multiple services from one repo.

#### 1. Backend Service
1.  In your project canvas, click the repo card.
2.  Go to **Settings** -> **Root Directory**. Set it to `/backend`.
3.  Go to **Variables**. Add your API keys:
    *   `GEMINI_API_KEY`
    *   `CLAUDE_API_KEY`
    *   `SERPER_API_KEY`
    *   `LEADMAGIC_API_KEY`
    *   `PORT`: `8000`
4.  **Add a Database**:
    *   Right-click the canvas -> **Database** -> **PostgreSQL**.
    *   Railway will automatically inject `DATABASE_URL` into your backend service.
    *   *Note: We updated the code to automatically use this Postgres DB instead of SQLite.*

#### 2. Frontend Service
1.  Click **"New"** -> **"GitHub Repo"** -> Select the same repo again.
2.  Go to **Settings** -> **Root Directory**. Set it to `/frontend`.
3.  Go to **Variables**:
    *   `NEXT_PUBLIC_API_URL`: Set this to the **Public Domain** of your Backend service (e.g., `https://backend-production.up.railway.app`).
    *   *You can find the Backend URL in the Backend service -> Settings -> Networking -> Public Networking.*

## Step 4: Verify
1.  Wait for both services to build (green checkmarks).
2.  Click the **Public URL** of your Frontend service.
3.  You should see the BD-OS login/dashboard!

## Troubleshooting
*   **Database Error?** Ensure the Backend service has the `DATABASE_URL` variable (Railway usually adds it automatically when you link the DB).
*   **CORS Error?** In `backend/main.py`, we set `allow_origins=["*"]`, so it should work. If not, update it to your specific frontend URL.
