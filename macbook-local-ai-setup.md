# Local AI Setup — MacBook Pro M1 Max (32 GB)

A complete guide to running a local AI assistant on your MacBook Pro 16-inch (2021) with Apple M1 Max and 32 GB unified memory.

---

## Hardware Analysis

| Spec | Value |
|------|-------|
| Chip | Apple M1 Max |
| Memory | 32 GB unified (shared CPU + GPU) |
| Memory bandwidth | ~400 GB/s |
| GPU cores | 24 or 32 (depending on config) |
| Available for models | ~26 GB (after macOS ~5-6 GB) |

The M1 Max is one of the best chips for local LLM inference. The 400 GB/s memory bandwidth is exceptional — it's faster than most discrete desktop GPUs — and 32 GB unified memory means models up to ~22 GB can run comfortably with room for context.

---

## Model Recommendations

With 32 GB, you can run significantly larger models than on the RTX 3080 (10 GB VRAM). Here's what fits:

### Recommended Models

| Model | Type | Size (Q4) | Speed (est.) | Best for | Ollama command |
|-------|------|----------|-------------|----------|----------------|
| **Qwen 3.5 9B** | Dense | ~5 GB | ~60–80 t/s | Quick tasks, content coach | `ollama pull qwen3.5:9b` |
| **Qwen 3.5 35B-A3B** | MoE | ~22 GB | ~50–80 t/s | Daily driver — fast + smart | `ollama pull qwen3.5:35b-a3b` |
| **Qwen 3.5 27B** | Dense | ~17 GB | ~15–20 t/s | Deep reasoning, creative work | `ollama pull qwen3.5:27b` |
| Qwen 3.5 4B | Dense | ~2.5 GB | ~100+ t/s | Ultra-lightweight tasks | `ollama pull qwen3.5:4b` |
| Gemma 3 27B QAT | Dense | ~14 GB | ~10–18 t/s | Creative writing, vision | `ollama pull gemma3:27b` |

### My Recommendation

Start with **three models** — they're all from the Qwen 3.5 family (March 2026), natively multimodal (text + images + video), 262K context, Apache 2.0:

1. **Qwen 3.5 9B** — Your content coach / lightweight model. Same as on the PC for a consistent experience. Fast enough for quick Q&A and content drafts.

2. **Qwen 3.5 35B-A3B** — Your daily driver. A sparse MoE with 35B total params but only 3B active per token. This means it runs at 9B-like speeds (~50-80 t/s) while having access to 35B worth of knowledge. Benchmarks rival models 3-4x its size: MMLU-Pro 85.3%, GPQA Diamond 84.2%. The speed-to-intelligence ratio is exceptional — near-instant responses that are genuinely smart.

3. **Qwen 3.5 27B** — Your deep reasoning model. A dense model where all 27B parameters are active on every token. Slower (~15-20 t/s) but more thorough for complex analysis, nuanced writing, and tasks where quality matters more than speed. Ties GPT-5 mini on SWE-bench Verified (72.4).

> **Why not GPT-OSS 20B?** Qwen 3.5 35B-A3B outperforms it on virtually every benchmark while running faster. And the Qwen 3.5 9B already surpasses GPT-OSS 120B (the bigger sibling) on key reasoning benchmarks. The Qwen 3.5 architecture is a full generation ahead.

You can switch between all three freely in Open WebUI — they all stay downloaded and ready. Only one runs at a time, so there's no memory conflict.

---

## Architecture Overview

```
MacBook Pro (M1 Max, 32 GB)
├── Ollama (native macOS app) → Metal GPU acceleration
│   ├── qwen3.5:9b          (content coach, quick tasks)
│   ├── qwen3.5:35b-a3b     (daily driver — fast + smart)
│   └── qwen3.5:27b         (deep reasoning, creative)
└── Docker Desktop for Mac
    └── Open WebUI (port 3000)
        └── connects to Ollama via host.docker.internal:11434
```

> **Why Ollama runs natively (not in Docker):** Docker on macOS cannot access Apple's Metal GPU. Running Ollama as a native macOS app gives you full Metal acceleration, which is critical for performance. Open WebUI runs in Docker since it's just a web app — no GPU needed.

---

## Setup Guide

### Step 1: Install Homebrew (if not already installed)

Open **Terminal** and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

If Homebrew is already installed, skip this step. Verify with:

```bash
brew --version
```

### Step 2: Install Ollama

```bash
brew install ollama
```

Start the Ollama service:

```bash
ollama serve
```

> **Note:** `ollama serve` runs in the foreground. Open a **new terminal tab** (Cmd+T) for the next steps. Alternatively, you can download the Ollama macOS app from [ollama.com/download](https://ollama.com/download) which runs as a menu bar app and starts automatically — but Homebrew works fine.

Verify Ollama is running:

```bash
ollama --version
```

### Step 3: Pull Your Models

In a new terminal tab (while `ollama serve` is running):

```bash
# Content coach / lightweight model — same as your PC
ollama pull qwen3.5:9b

# Daily driver — fast MoE, benchmarks above its weight
ollama pull qwen3.5:35b-a3b

# Deep reasoning — dense model, slower but more thorough
ollama pull qwen3.5:27b
```

The 9B is ~5 GB, the 35B-A3B is ~22 GB, and the 27B is ~17 GB. They share architecture components so the total download is less than the sum. This only happens once.

**Quick test to verify everything works:**

```bash
ollama run qwen3.5:9b "What is the capital of the Netherlands?"
```

You should get a fast response mentioning Amsterdam. Press Ctrl+D to exit.

### Step 4: Install Docker Desktop

1. Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/) (Apple Silicon version)
2. Open the `.dmg` file and drag Docker to Applications
3. Open Docker Desktop and let it finish initializing
4. Accept the terms when prompted

Verify Docker works:

```bash
docker --version
```

### Step 5: Run Open WebUI

With Ollama running and Docker Desktop started:

```bash
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

**What this does:**
- `-p 3000:8080` — Open WebUI accessible on port 3000
- `--add-host=host.docker.internal:host-gateway` — Lets the Docker container reach your native Ollama
- `-v open-webui:/app/backend/data` — Persists your chats, settings, and user accounts
- `--restart always` — Auto-starts with Docker

Wait about 30 seconds for it to initialize, then open your browser:

```
http://localhost:3000
```

### Step 6: Create Your Account

1. The first account you create becomes the **admin** — create yours first
2. Go to **Admin Panel → Settings → Connections** and verify Ollama is connected (should show `http://host.docker.internal:11434`)
3. All three models (`qwen3.5:9b`, `qwen3.5:35b-a3b`, and `qwen3.5:27b`) should appear in the model dropdown

### Step 7: Enable Web Search (Optional)

Same as on your PC:

1. Go to **Admin Panel → Settings → Web Search**
2. Toggle **Enable Web Search** on
3. Select **"DDGS"** (DuckDuckGo Search) — no API key needed
4. Save

### Step 8: Set Up the Content Coach (Optional)

If you want the same Content Coach setup as your PC:

1. Go to **Workspace → Models**
2. Click **"Create a Model"**
3. Name it **"Content Coach"**
4. Under **Base Model**, select `qwen3.5:9b`
5. Paste the system prompt from your `local-ai` repo: [`prompts/coaching-content-creator.md`](https://github.com/GeorgeThiel-hob/local-ai/blob/main/prompts/coaching-content-creator.md)
6. Save

---

## Daily Usage

### Starting Everything

**Option A: Automatic (recommended)**

1. Set Ollama to start at login:
   - If using the Ollama macOS app: it auto-starts from the menu bar
   - If using Homebrew: add `ollama serve` to your login items, or create a launch agent (see below)

2. Set Docker Desktop to start at login:
   - Docker Desktop → Settings → General → **"Start Docker Desktop when you sign in"**

3. Open WebUI auto-starts with Docker (we used `--restart always`)

**Option B: Manual**

```bash
# Terminal tab 1: Start Ollama
ollama serve

# Terminal tab 2 (if Docker Desktop is running, Open WebUI auto-starts)
# If not, start Docker Desktop from Applications
```

Then open `http://localhost:3000` in your browser.

### Auto-start Ollama via Launch Agent (Homebrew install)

If you installed Ollama via Homebrew and want it to start automatically:

```bash
mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.ollama.serve.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.serve</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/ollama</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.ollama.serve.plist
```

This makes Ollama start automatically on login and restart if it crashes.

### Stopping

```bash
# Stop Open WebUI
docker stop open-webui

# Stop Ollama (if running via terminal)
# Press Ctrl+C in the ollama serve terminal

# Or if using launch agent:
launchctl unload ~/Library/LaunchAgents/com.ollama.serve.plist
```

### Checking Status

```bash
# Check if Ollama is running
ollama list

# Check if Open WebUI is running
docker ps
```

---

## Updating

Same principle as your PC — **always update Ollama before pulling new models**.

### Update Ollama

```bash
brew upgrade ollama
```

Or if using the macOS app, download the latest from [ollama.com/download](https://ollama.com/download).

### Update Open WebUI

```bash
docker pull ghcr.io/open-webui/open-webui:main
docker stop open-webui
docker rm open-webui
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

Your chats, settings, and user accounts are preserved in the Docker volume.

### Pull New Models

```bash
ollama pull <model-name>
```

---

## Adding More Models

With 32 GB, you have room to experiment. Some options worth trying:

```bash
# Ultra-lightweight for instant responses
ollama pull qwen3.5:4b

# Creative writing and vision tasks
ollama pull gemma3:27b
```

> **Note:** Don't run the 35B-A3B and 27B simultaneously — they'd exceed your 32 GB. Ollama loads one model at a time by default, so just pick the right one for the task in Open WebUI.

**To list installed models:**

```bash
ollama list
```

**To remove a model:**

```bash
ollama rm <model-name>
```

---

## Troubleshooting

### Open WebUI shows "Connection failed" or no models

Check that Ollama is running:

```bash
curl http://localhost:11434/api/tags
```

If this returns a JSON list of models, Ollama is fine. The issue is Docker-to-host networking. Try:

```bash
# Stop and remove the container
docker stop open-webui && docker rm open-webui

# Re-run with explicit OLLAMA_BASE_URL
docker run -d \
  -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

### Models are slow

Check how much memory is being used:

```bash
# Check system memory pressure
memory_pressure
```

If the system is under memory pressure, you're running a model that's too large. Switch to a smaller model or close memory-heavy apps.

For M1 Max, expected speeds at Q4 quantization:

| Model | Expected speed |
|-------|---------------|
| qwen3.5:9b | ~60–80 t/s |
| qwen3.5:35b-a3b | ~50–80 t/s (MoE — only 3B active) |
| qwen3.5:27b | ~15–20 t/s (dense — all 27B active) |
| gemma3:27b | ~10–18 t/s |

If speeds are significantly lower, restart Ollama and try again.

### Docker Desktop using too much memory

Docker Desktop → Settings → Resources → set Memory limit to 4 GB (Open WebUI doesn't need much — the heavy lifting is done by native Ollama).

---

## MacBook vs PC: When to Use Which

| Scenario | Best device |
|----------|------------|
| Content creation (Content Coach) | Either — same 9B model, same prompt |
| Fast smart responses | MacBook (35B-A3B — fast MoE) |
| Deep reasoning / nuanced writing | MacBook (27B dense) |
| Fastest 9B response time | PC (RTX 3080 CUDA is faster than M1 Metal for small models) |
| Gaming + AI simultaneously | MacBook for AI, PC for gaming |
| Away from home / portable | MacBook |
| Your girlfriend using AI | PC (LAN access via Open WebUI) |

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start Ollama | `ollama serve` |
| List models | `ollama list` |
| Pull a model | `ollama pull qwen3.5:9b` |
| Remove a model | `ollama rm <model-name>` |
| Quick chat (terminal) | `ollama run qwen3.5:9b` |
| Open WebUI | `http://localhost:3000` |
| Check Open WebUI container | `docker ps` |
| Update Ollama | `brew upgrade ollama` |
| Update Open WebUI | `docker pull ghcr.io/open-webui/open-webui:main` then recreate container |
