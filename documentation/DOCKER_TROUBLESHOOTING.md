# Docker Troubleshooting Guide 🐳

You are encountering a persistent error:
`failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`

This means the Docker Command Line Interface (CLI) cannot talk to the Docker Desktop service running in the background. This is a common issue on Windows.

## 🛠️ Recommended Fixes (Try in Order)

### 1. Restart Docker Desktop

The simplest fix is often the best.

1.  Look for the **Docker Whale icon** in your system tray (bottom right, near the clock).
2.  Right-click it and select **Quit Docker Desktop**.
3.  Wait a moment, then relaunch **Docker Desktop** from your Start Menu.
4.  Wait for the whale icon to stop animating and stabilize.
5.  Try running `docker version` in your terminal to verify.

### 2. Switch Docker Context

Sometimes Docker gets stuck on the wrong "context".
Run this command in your terminal:

```powershell
docker context use default
```

Then try `docker version` again.

### 3. Reset Docker Socket (Advanced)

If restarting doesn't work:

1.  Open **Docker Desktop Dashboard**.
2.  Go to **Settings (Gear Icon)** > **General**.
3.  Ensure **"Expose daemon on tcp://localhost:2375 without TLS"** is CHECKED.
4.  Click **Apply & Restart**.

### 4. Restart WSL2 Service

Since `docker-desktop` runs on WSL2:

1.  Open a **Administrator** PowerShell terminal.
2.  Run: `wsl --shutdown`
3.  Restart Docker Desktop.

### 5. Check for "Comodo" or Antivirus

Some security software (like Comodo Firewall) blocks the named pipes Docker uses. Check if your antivirus is blocking Docker.

---

## ⚠️ While You Fix This...

**Your application is ALREADY RUNNING locally!**
You don't _need_ Docker to work on the app right now.

- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend:** [http://localhost:8000](http://localhost:8000)

You can continue your development work while troubleshooting Docker in the background.
