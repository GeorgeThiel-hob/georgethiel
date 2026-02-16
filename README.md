# 🏠 Local AI Server

A self-hosted AI assistant running on your home network. Powered by Ollama + Open WebUI on an NVIDIA RTX 3080 12GB.

Built for privacy, sustainability, and zero ongoing costs.

---

## What This Does

- Runs a powerful open-source LLM (Qwen 2.5 14B) locally on your GPU
- Provides a clean ChatGPT-like web interface accessible from any device on your home network
- Pre-configured with a system prompt for coaching & counseling content creation
- Fully offline capable — your data never leaves your home

## Hardware Requirements

- **GPU:** NVIDIA RTX 3080 10GB (or similar with 10GB+ VRAM)
- **RAM:** 16GB+ system RAM recommended
- **Storage:** ~15GB free disk space (for model + Docker images)
- **OS:** Windows 10

---

## Setup Guide (Step by Step)

### Step 1: Enable WSL2

Open **PowerShell as Administrator** (right-click Start → "Windows PowerShell (Admin)") and run:

```powershell
wsl --install
```

This installs Windows Subsystem for Linux with Ubuntu. **Restart your PC** when prompted.

After reboot, a terminal window will open asking you to create a Linux username and password. Pick something simple — you'll need it occasionally.

Verify it works by opening PowerShell and running:

```powershell
wsl --version
```

You should see WSL version 2.x.

### Step 2: Install NVIDIA Drivers for WSL2

Your Windows NVIDIA drivers should already support WSL2 GPU passthrough. Verify by opening PowerShell and running:

```powershell
nvidia-smi
```

You should see your RTX 3080 listed. If this command is not recognized, download and install the latest [NVIDIA Game Ready drivers](https://www.nvidia.com/drivers/).

> **Note:** Do NOT install NVIDIA drivers inside WSL/Ubuntu — the Windows drivers handle GPU access for WSL2 automatically.

### Step 3: Install Docker Desktop

1. Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Run the installer
3. **Important:** During installation, make sure "Use WSL 2 instead of Hyper-V" is checked
4. Restart your PC when prompted
5. Open Docker Desktop and let it finish initializing

Verify Docker works by opening PowerShell:

```powershell
docker --version
docker compose version
```

Both should return version numbers.

### Step 4: Install Git

1. Download [Git for Windows](https://git-scm.com/download/win)
2. Run the installer with default settings
3. Verify in PowerShell:

```powershell
git --version
```

### Step 5: Clone This Project

Open PowerShell and navigate to where you want the project:

```powershell
cd ~
git clone https://github.com/YOUR_USERNAME/local-ai-server.git
cd local-ai-server
```

> Replace `YOUR_USERNAME` with your actual GitHub username after you push this repo.

### Step 6: Start the Server

Make sure Docker Desktop is running, then:

```powershell
docker compose up -d
```

This will:
- Download the Ollama image (with GPU support)
- Download the Open WebUI image
- Start both containers

First run takes a few minutes to download everything. Check the status:

```powershell
docker compose ps
```

Both `ollama` and `open-webui` should show as "running".

### Step 7: Download the AI Model

Pull the Qwen 2.5 14B model (quantized to fit in 12GB VRAM):

```powershell
docker exec ollama ollama pull qwen2.5:14b
```

This downloads ~9GB. It only needs to happen once — the model is persisted in a Docker volume.

**Optional:** Also pull the 7B version as a faster alternative:

```powershell
docker exec ollama ollama pull qwen2.5:7b
```

### Step 8: Access the Web Interface

Open a browser on **any device on your home network** and go to:

```
http://localhost:3000
```

Or from another device (like a laptop), use your PC's local IP address:

```
http://192.168.x.x:3000
```

To find your PC's IP address, run in PowerShell:

```powershell
ipconfig
```

Look for `IPv4 Address` under your active network adapter (usually something like `192.168.1.x` or `192.168.178.x`).

### Step 9: Create User Accounts

1. The first account you create becomes the **admin** account — create yours first
2. Then create an account for your girlfriend
3. Go to **Admin Panel → Settings → Models** and make sure `qwen2.5:14b` appears

### Step 10: Set Up the Coaching System Prompt

1. Go to **Workspace → Models** in the Open WebUI sidebar
2. Click **"Create a Model"**
3. Name it something like "Content Coach"
4. Under **Base Model**, select `qwen2.5:14b`
5. Paste the system prompt from [`prompts/coaching-content-creator.md`](prompts/coaching-content-creator.md)
6. Save

Now she can select "Content Coach" from the model dropdown and it will always use the coaching-optimized prompt.

---

## Daily Usage

### Starting the Server

If Docker Desktop is running, the server starts automatically (containers are set to `restart: unless-stopped`).

If the PC was fully shut down:
1. Turn on the PC
2. Docker Desktop auto-starts (configure this in Docker Desktop → Settings → General → "Start Docker Desktop when you sign in")
3. The containers auto-start with Docker
4. Open WebUI is accessible within ~30 seconds

### Stopping the Server

```powershell
cd ~/local-ai-server
docker compose down
```

### Checking Status

```powershell
docker compose ps
docker exec ollama ollama list
```

### Updating Open WebUI

```powershell
cd ~/local-ai-server
docker compose pull
docker compose up -d
```

---

## Auto-Start on Boot

To make everything start automatically when your PC turns on:

1. Open **Docker Desktop → Settings → General**
2. Enable **"Start Docker Desktop when you sign in"**
3. The containers are already configured with `restart: unless-stopped`, so they'll start with Docker

---

## Wake-on-LAN (Optional)

If you sometimes turn the PC off and want your girlfriend to be able to start it remotely:

1. **Enable in BIOS:** Enter your BIOS (press DEL or F2 during boot) → look for "Wake on LAN" under Power Management → Enable it
2. **Enable in Windows:** Device Manager → Network Adapters → right-click your Ethernet adapter → Properties → Power Management → check "Allow this device to wake the computer"
3. **Get your MAC address:** Run `ipconfig /all` in PowerShell and note the "Physical Address" of your Ethernet adapter
4. **Install a WoL app** on her phone (e.g., "Wake On Lan" on iOS/Android), enter your PC's MAC address and local IP

> **Note:** Wake-on-LAN only works over Ethernet (wired connection), not Wi-Fi.

---

## Adding More Models

Browse available models at [ollama.com/library](https://ollama.com/library) and pull them:

```powershell
# Smaller/faster model for quick tasks
docker exec ollama ollama pull qwen2.5:7b

# Strong reasoning model
docker exec ollama ollama pull phi4:14b

# Good for creative writing
docker exec ollama ollama pull mistral-nemo:12b
```

All pulled models become available in the Open WebUI model dropdown automatically.

---

## Troubleshooting

### GPU not detected by Ollama

Check that your NVIDIA drivers support WSL2:
```powershell
# In PowerShell
nvidia-smi
```

Check GPU access inside the container:
```powershell
docker exec ollama nvidia-smi
```

If the second command fails, make sure Docker Desktop has WSL2 backend enabled (Settings → General → "Use the WSL 2 based engine").

### Open WebUI can't connect to Ollama

Both containers are on the same Docker network. If issues persist:
```powershell
docker compose down
docker compose up -d
```

### Model is slow

If generation feels slow, you may be running a model too large for your VRAM. Check VRAM usage:
```powershell
nvidia-smi
```

If memory usage is near 12GB, switch to the 7B model which runs much faster.

### Access from other devices not working

Make sure Windows Firewall allows connections on port 3000:
1. Open **Windows Defender Firewall**
2. Click **"Allow an app or feature through Windows Defender Firewall"**
3. Click **"Change Settings"** → **"Allow another app"**
4. Add a rule for **port 3000** (TCP, Private network)

Or run in PowerShell (Admin):
```powershell
New-NetFirewallRule -DisplayName "Open WebUI" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow -Profile Private
```

---

## Project Structure

```
local-ai-server/
├── docker-compose.yml          # Container orchestration
├── prompts/
│   └── coaching-content-creator.md  # System prompt for coaching content
├── .gitignore
├── LICENSE
└── README.md                   # This file
```

---

## Environment & Sustainability

This setup is designed to be more environmentally sustainable than cloud AI:

- **GPU only draws power during active inference** — idle consumption is minimal
- **No data center overhead** — no cooling systems, no network hops, no redundant infrastructure
- **Zero data transmission** — everything runs locally, saving network energy
- **Reuses existing hardware** — your gaming GPU doubles as an AI server

---

## License

MIT — See [LICENSE](LICENSE) for details.
