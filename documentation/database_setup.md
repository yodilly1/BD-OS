# 🐘 Setting Up a Persistent Database on Render

Your data is resetting because **Render wipes the hard drive every time you deploy**.
To keep your data safe, you need a **PostgreSQL Database**.

## Step 1: Create the Database
1.  Go to your [Render Dashboard](https://dashboard.render.com/).
2.  Click **New +** -> **PostgreSQL**.
3.  **Name:** `bd-os-db` (or anything you like).
4.  **Region:** Choose the same region as your Web Service (e.g., Oregon, Frankfurt).
5.  **Plan:** Select **Free** (good for testing) or **Starter** (for production).
6.  Click **Create Database**.

## Step 2: Get the Connection String
1.  Wait for the database to be created (it takes a minute).
2.  Look for the **"Internal Database URL"** section.
3.  Click **Copy** to copy the URL. It looks like:
    `postgres://bd_os_user:password@hostname/bd_os`

## Step 3: Connect Your App
1.  Go back to your **Web Service** (the BD-OS backend) in the Render Dashboard.
2.  Click on **Environment**.
3.  Click **Add Environment Variable**.
4.  **Key:** `DATABASE_URL`
5.  **Value:** Paste the URL you copied in Step 2.
6.  Click **Save Changes**.

## Step 4: Redeploy
Render usually redeploys automatically when you save environment variables. If not, click **Manual Deploy** -> **Deploy latest commit**.

**That's it!** 🎉
Your data will now live in a secure database and will **never** be lost when you update the code.
