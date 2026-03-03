# 🏠 Local AI Server

A self-hosted AI assistant running on your home network. Powered by Ollama + Open WebUI on an NVIDIA RTX 3080.

Built for privacy, sustainability, and zero ongoing costs.

---

## What This Does

- Runs a powerful open-source LLM (Qwen 3.5 9B) locally on your GPU
- Provides a clean ChatGPT-like web interface accessible from any device on your home network
- Pre-configured with a system prompt for coaching & counseling content creation
- Web search capability via DuckDuckGo integration
- Fully offline capable — your data never leaves your home

## Hardware

| Component | Model |
|-----------|-------|
| CPU | AMD Ryzen 7 3700X (8 cores / 16 threads) |
| GPU | NVIDIA GeForce RTX 3080 (10 GB VRAM) |
| RAM | 16 GB DDR4 3600 MHz (2× G.Skill 8 GB) |
| Motherboard | Gigabyte X570 AORUS MASTER |
| Storage | NVMe + Samsung 860 EVO 1 TB SSD + 1 TB HDD |
| OS | Windows 10 |

### Model Compatibility (10 GB VRAM)

| Model | VRAM Usage | Speed | Notes |
|-------|-----------|-------|-------|
| **qwen3.5:9b** | ~6.6 GB | Fast | **Recommended default** |
| qwen3.5:4b | ~4 GB | Very fast | Lightweight alternative |
| mistral-nemo:12b | ~8 GB | Fast | Creative writing |
| phi4:14b (Q4) | ~9 GB | Moderate | Reasoning tasks |

> Models larger than 14B parameters are not recommended for 10 GB VRAM.

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

> **If WSL2 fails to install:** You may need to enable virtualization in your BIOS. For the Gigabyte X570 AORUS MASTER: enter BIOS (press DEL during boot) → M.I.T. → Advanced Frequency Settings → Advanced CPU Core Settings → set **SVM Mode** to **Enabled**. Save and reboot, then retry `wsl --install`.

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
3. **Important:** During installation, make sure **"Use WSL 2 instead of Hyper-V"** is checked
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
git clone git@github.com:GeorgeThiel-hob/local-ai.git
cd local-ai
```

> If you haven't set up SSH keys for GitHub, you can use HTTPS instead:
> `git clone https://github.com/GeorgeThiel-hob/local-ai.git`

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

Pull the Qwen 3.5 9B model (~6.6 GB VRAM):

```powershell
docker exec ollama ollama pull qwen3.5:9b
```

This downloads once — the model is persisted in a Docker volume.

**Optional:** Also pull the 4B version as a faster/lighter alternative:

```powershell
docker exec ollama ollama pull qwen3.5:4b
```

### Step 8: Access the Web Interface

**On this PC:**

```
http://localhost:3000
```

**From another device on the network** (e.g. a laptop on Wi-Fi), use the PC's Ethernet IP:

```
http://192.168.2.26:3000
```

To find or verify your PC's IP address, run in PowerShell:

```powershell
ipconfig
```

Look for `IPv4 Address` under your **Ethernet** adapter (not Wi-Fi, not WSL virtual adapters).

> **Important:** WSL2 binds ports to localhost only. To make Open WebUI accessible from other devices on your network, you need to set up a port proxy — see [LAN Access Setup](#lan-access-setup) below.

### Step 9: Create User Accounts

1. The first account you create becomes the **admin** account — create yours first
2. Then create an account for other users
3. Go to **Admin Panel → Settings → Models** and make sure `qwen3.5:9b` appears

### Step 10: Set Up the Coaching System Prompt

1. Go to **Workspace → Models** in the Open WebUI sidebar
2. Click **"Create a Model"**
3. Name it **"Content Coach"**
4. Under **Base Model**, select `qwen3.5:9b`
5. Paste the system prompt from [`prompts/coaching-content-creator.md`](prompts/coaching-content-creator.md)
6. Save

Now users can select "Content Coach" from the model dropdown and it will always use the coaching-optimized prompt.

### Step 11: Enable Web Search (DuckDuckGo)

1. Go to **Admin Panel → Settings → Web Search**
2. Toggle **Enable Web Search** on
3. Select **"DDGS"** (DuckDuckGo Search) from the provider dropdown — no API key required
4. Save

Users can then toggle the 🌐 web search icon in any chat to let the model search the web for current information.

---

## LAN Access Setup

WSL2 does not expose Docker ports to the local network by default. To allow other devices (like a laptop on Wi-Fi) to access Open WebUI, run these commands in **PowerShell as Administrator**:

**1. Create a port proxy:**

```powershell
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=localhost
```

**2. Add a firewall rule:**

```powershell
New-NetFirewallRule -DisplayName "Open WebUI" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow -Profile Any
```

These settings persist across reboots. Other devices can now access Open WebUI at `http://192.168.2.26:3000`.

**To verify the port proxy is active:**

```powershell
netsh interface portproxy show v4tov4
```

**To remove it later if needed:**

```powershell
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0
```

> **Security note:** Port 3000 is open to all devices on your local network (192.168.2.x). Open WebUI requires login, and your router's NAT/firewall blocks access from the internet. To restrict access to a specific device, add `-RemoteAddress 192.168.2.XX` to the firewall rule.

---

## Updating Ollama and Open WebUI

> **⚠️ Always update before pulling new models.** Newer models often require updated Ollama versions to run correctly. Updating takes under a minute and prevents cryptic errors.

### Quick update (run this regularly)

```powershell
cd ~/local-ai
docker compose pull
docker compose up -d
```

This pulls the latest images for both Ollama and Open WebUI, then recreates only the containers that changed. Your data (models, chat history, user accounts) is stored in Docker volumes and is preserved across updates.

### Then pull your new model

```powershell
docker exec ollama ollama pull <model-name>
```

### Full example — upgrading to a new model

```powershell
# Step 1: Always update containers first
cd ~/local-ai
docker compose pull
docker compose up -d

# Step 2: Pull the new model
docker exec ollama ollama pull qwen3.5:9b

# Step 3 (optional): Remove the old model to free disk space
docker exec ollama ollama rm qwen2.5:14b
```

### After updating Open WebUI

Open WebUI updates may introduce new features or settings. After updating, check:
- **Admin Panel → Settings** for any new configuration options
- **Workspace → Models** to verify your custom models (e.g. Content Coach) are still configured correctly
- The changelog at [github.com/open-webui/open-webui/releases](https://github.com/open-webui/open-webui/releases) for notable changes

### Why update first?

Ollama adds support for new model architectures in each release. The Qwen 3.5 series, for example, uses Gated Delta Networks and sparse MoE — architecture features that older Ollama versions don't understand. If you try to pull a newer model on an outdated Ollama, it may fail to download or produce garbled output. The same applies to Open WebUI, which adds support for new Ollama features and model parameters over time.

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
cd ~/local-ai
docker compose down
```

### Checking Status

```powershell
docker compose ps
docker exec ollama ollama list
```

---

## Auto-Start on Boot

To make everything start automatically when your PC turns on:

1. Open **Docker Desktop → Settings → General**
2. Enable **"Start Docker Desktop when you sign in"**
3. Optionally disable **"Open Docker Dashboard when Docker Desktop starts"** to run silently in the system tray
4. The containers are already configured with `restart: unless-stopped`, so they'll start with Docker

---

## Wake-on-LAN (Optional)

If you sometimes turn the PC off and want to start it remotely from another device:

1. **Enable in BIOS:** Enter your BIOS (press DEL during boot) → look for "Wake on LAN" under Power Management → Enable it
2. **Enable in Windows:** Device Manager → Network Adapters → right-click your Ethernet adapter → Properties → Power Management → check "Allow this device to wake the computer"
3. **Get your MAC address:** Run `ipconfig /all` in PowerShell and note the "Physical Address" of your Ethernet adapter
4. **Install a WoL app** on a phone or laptop (e.g., "Wake On Lan" on iOS/Android), enter your PC's MAC address and local IP

> **Note:** Wake-on-LAN only works over Ethernet (wired connection), not Wi-Fi.

---

## Adding More Models

Browse available models at [ollama.com/library](https://ollama.com/library) and pull them:

```powershell
# Lightweight alternative for quick tasks
docker exec ollama ollama pull qwen3.5:4b

# Good for creative writing
docker exec ollama ollama pull mistral-nemo:12b

# Strong reasoning model (tight VRAM fit at ~9 GB)
docker exec ollama ollama pull phi4:14b
```

All pulled models become available in the Open WebUI model dropdown automatically.

**To list installed models:**

```powershell
docker exec ollama ollama list
```

**To remove a model:**

```powershell
docker exec ollama ollama rm <model-name>
```

> **Important:** Always update Ollama before pulling new models — see [Updating Ollama and Open WebUI](#updating-ollama-and-open-webui).

---

## Portable Setup (macOS)

The Qwen 3.5 9B model also runs well on an Apple Silicon MacBook (M1/M2/M3) with 16 GB+ unified memory. This gives you a portable option when the main PC is off or you're away from home.

### Install Ollama on macOS

```bash
brew install ollama
```

### Start and pull the model

```bash
ollama serve
# In a new terminal:
ollama pull qwen3.5:9b
```

### Chat directly from the terminal

```bash
ollama run qwen3.5:9b
```

### Optional: Add Open WebUI

If you want the browser interface on the MacBook too, install Docker Desktop for Mac and use the same `docker-compose.yml` from this project (remove the `deploy.resources` GPU section — Apple Silicon uses Metal automatically via Ollama).

### Performance expectations

| Device | Speed (approx.) | Notes |
|--------|-----------------|-------|
| RTX 3080 (PC) | ~40–60 tokens/s | CUDA acceleration |
| M1 MacBook Pro 16 GB | ~15–25 tokens/s | Metal acceleration, fully usable |
| M1 MacBook Pro (4B model) | ~30–40 tokens/s | Faster alternative if speed matters |

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

### WSL2 won't install (virtualization error)

You need to enable SVM Mode in BIOS. For Gigabyte X570 AORUS MASTER:

1. Enter BIOS (press DEL during boot)
2. Navigate to **M.I.T. → Advanced Frequency Settings → Advanced CPU Core Settings**
3. Set **SVM Mode** to **Enabled**
4. Save and reboot

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

If memory usage is near 10 GB, switch to the 4B model which runs much faster.

### Access from other devices not working

1. **Check port proxy is active:**
   ```powershell
   netsh interface portproxy show v4tov4
   ```
   If empty, set it up — see [LAN Access Setup](#lan-access-setup).

2. **Check firewall rule exists:**
   ```powershell
   Get-NetFirewallRule -DisplayName "Open WebUI"
   ```

3. **Verify you're using the Ethernet IP** (not Wi-Fi or WSL virtual IP):
   ```powershell
   ipconfig
   ```
   Use the `IPv4 Address` under your Ethernet adapter.

4. **Test basic connectivity** from the other device:
   ```
   ping 192.168.2.26
   ```
   If ping fails, check that both devices are on the same network and that your router doesn't have client isolation enabled.

---

## Project Structure

```
local-ai/
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
