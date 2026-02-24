# Voice Agent Demo Setup Guide

## Quick Start for Client Demo

This voice agent uses **Piper TTS** for low-latency German voice synthesis. The TTS runs **locally** on your machine, providing faster response times.

---

## 🚀 Setup Steps

### 1. Install Dependencies

```bash
uv sync
```

### 2. Download AI Models

```bash
uv run python src/agent.py download-files
```

This downloads:
- Piper TTS German model (~60MB)
- Silero VAD model
- Other required models

### 3. Configure Environment

Create `.env.local` file:

```bash
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
GROQ_API_KEY=your_groq_api_key
DEEPGRAM_API_KEY=your_deepgram_api_key
```

---

## 🎯 Running the Demo

### Terminal 1: Start the Agent

```bash
uv run python src/agent.py dev
```

Wait for:
```
✓ Piper TTS model pre-loaded
Agent ready, listening for rooms...
```

### Terminal 2: Start Frontend

```bash
node dev.js
```

You'll see:
```
Dev server ready!
Open: http://localhost:3000
```

### 3. Open Browser

Go to: **http://localhost:3000**

Click **"Start"** and begin speaking!

---

## ⚡ Performance

### Current Configuration:

| Component | Model | Latency |
|-----------|-------|---------|
| **STT** | Groq Whisper-large-v3-turbo | ~300-800ms |
| **LLM** | Groq Llama-3.1-8b-instant | ~500ms-2s |
| **TTS** | Piper TTS (Local) | ~100-300ms |
| **Total** | | **~2-4 seconds** |

### Optimizations Applied:

1. **Local TTS** - No API calls, instant synthesis
2. **Fast LLM** - 8B model instead of 70B
3. **Pre-warming** - Models loaded in advance
4. **German Optimized** - Thorsten voice for natural German

---

## 🎤 Demo Script (German)

Suggested conversation flow:

```
User: "Hallo!"
Agent: "Hallo! Wie kann ich dir helfen?"

User: "Wie ist das Wetter?"
Agent: "Das Wetter ist heute schön. Die Sonne scheint."

User: "Danke!"
Agent: "Gern geschehen!"
```

---

## 🔧 Troubleshooting

### "Piper TTS model not found"

Run the download script:
```bash
uv run python src/download_piper_models.py
```

### "Connection failed"

Check your `.env.local` file and ensure:
- LIVEKIT_URL is correct
- API keys are valid
- Internet connection is stable

### Agent not responding

Check Terminal 1 logs for:
```
[STT] User: <what you said>
[LLM] Agent: <response>
```

If you see STT but no LLM, check Groq API key.

---

## 📊 Monitoring

### Agent Logs (Terminal 1)

```
[STT] User: Vielen Dank.     ← Speech recognized
[LLM] Agent: Gern geschehen  ← LLM response
Synthesis complete           ← TTS generated audio
```

### Browser DevTools (F12)

- **Console**: Check for errors
- **Network → WS**: See LiveKit connection

---

## 🎯 Key Features

✅ **Low Latency** - Local TTS, no API delays
✅ **German Optimized** - Natural German voice (Thorsten)
✅ **Offline Capable** - TTS works without internet
✅ **Auto Fallback** - Uses Deepgram if Piper fails
✅ **Pre-warmed** - Fast startup, no cold delays

---

## 📁 Project Structure

```
agent-starter-python/
├── src/
│   ├── agent.py                 # Main agent code
│   ├── piper_tts_plugin.py      # Custom Piper TTS wrapper
│   ├── download_piper_models.py # Model download script
│   └── test_piper.py            # TTS test script
├── api/
│   └── token.js                 # Token generation (Vercel)
├── index.html                   # Frontend UI
├── dev.js                       # Local dev server
└── .env.local                   # Environment variables
```

---

## 🌐 Deployment

### Vercel (Frontend + Token API)

```bash
git push origin main
```

Vercel auto-deploys from GitHub.

### LiveKit Cloud (Agent)

The agent runs locally and connects to LiveKit Cloud.

For production deployment, use:
```bash
uv run python src/agent.py start
```

---

## 📞 Support

For issues or questions:
1. Check agent logs in Terminal 1
2. Check browser console (F12)
3. Verify `.env.local` configuration
4. Test Piper TTS: `uv run python src/test_piper.py`

---

## 🎉 Demo Checklist

Before client demo:

- [ ] Run `uv sync`
- [ ] Run `uv run python src/agent.py download-files`
- [ ] Create `.env.local` with all keys
- [ ] Test agent locally
- [ ] Test frontend at http://localhost:3000
- [ ] Prepare German demo script
- [ ] Check microphone permissions
- [ ] Close unnecessary applications
- [ ] Test with clear German speech

---

**Ready to demo!** 🚀
