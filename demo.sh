# #!/bin/bash
# # ─────────────────────────────────────────────
# #  demo.sh — ek command se sab kuch start karo
# #  Usage: ./demo.sh
# # ─────────────────────────────────────────────

# set -e

# # Colors
# GREEN='\033[0;32m'
# CYAN='\033[0;36m'
# YELLOW='\033[1;33m'
# RED='\033[0;31m'
# BOLD='\033[1m'
# NC='\033[0m'

# SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# LOG_DIR="$SCRIPT_DIR/.demo-logs"
# mkdir -p "$LOG_DIR"

# echo ""
# echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
# echo -e "${BOLD}║        Voice Assistant — Demo            ║${NC}"
# echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
# echo ""

# # ── Cleanup pehle se chal rahe processes ──────────────────────────
# cleanup() {
#   echo ""
#   echo -e "${YELLOW}Shutting down...${NC}"
#   if [ -n "$AGENT_PID" ];    then kill "$AGENT_PID"    2>/dev/null; fi
#   if [ -n "$FRONTEND_PID" ]; then kill "$FRONTEND_PID" 2>/dev/null; fi
#   if [ -n "$NGROK_PID" ];    then kill "$NGROK_PID"    2>/dev/null; fi
#   echo -e "${GREEN}Done. Goodbye!${NC}"
#   exit 0
# }
# trap cleanup SIGINT SIGTERM

# # Pehle se chal rahe ngrok, frontend, aur port sab band karo
# echo -e "${YELLOW}Cleanup: pehle se chal rahe processes band kar raha hoon...${NC}"

# # Koi bhi ngrok process band karo
# pkill -9 -f ngrok 2>/dev/null || true

# # Port 3001 force kill
# PIDS_3001=$(lsof -ti:3001 2>/dev/null || true)
# if [ -n "$PIDS_3001" ]; then
#   echo "$PIDS_3001" | xargs kill -9 2>/dev/null || true
# fi

# # Port 4040 (ngrok UI) force kill
# PIDS_4040=$(lsof -ti:4040 2>/dev/null || true)
# if [ -n "$PIDS_4040" ]; then
#   echo "$PIDS_4040" | xargs kill -9 2>/dev/null || true
# fi

# sleep 2

# # ── Step 1: Python Agent start karo ──────────────────────────────
# echo -e "${CYAN}[1/3] Python agent start kar raha hoon...${NC}"
# cd "$SCRIPT_DIR"
# uv run python src/agent.py dev > "$LOG_DIR/agent.log" 2>&1 &
# AGENT_PID=$!
# echo -e "      Agent PID: $AGENT_PID (log: .demo-logs/agent.log)"

# # Agent thoda warm-up time do
# sleep 2

# if ! kill -0 "$AGENT_PID" 2>/dev/null; then
#   echo -e "${RED}Agent start nahi hua! Log dekho: .demo-logs/agent.log${NC}"
#   tail -20 "$LOG_DIR/agent.log"
#   exit 1
# fi
# echo -e "      ${GREEN}✓ Agent running${NC}"

# # ── Step 2: Frontend server start karo ───────────────────────────
# echo -e "${CYAN}[2/3] Frontend server start kar raha hoon (port 3001)...${NC}"
# node "$SCRIPT_DIR/frontend-server.js" > "$LOG_DIR/frontend.log" 2>&1 &
# FRONTEND_PID=$!
# sleep 1

# if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
#   echo -e "${RED}Frontend server start nahi hua! Log dekho: .demo-logs/frontend.log${NC}"
#   tail -10 "$LOG_DIR/frontend.log"
#   cleanup
#   exit 1
# fi
# echo -e "      ${GREEN}✓ Frontend server running${NC}"

# # ── Step 3: Ngrok tunnel start karo ──────────────────────────────
# echo -e "${CYAN}[3/3] Ngrok tunnel bana raha hoon...${NC}"
# ngrok http 3001 --log=stdout > "$LOG_DIR/ngrok.log" 2>&1 &
# NGROK_PID=$!
# sleep 3

# # Ngrok API se public URL nikalo
# PUBLIC_URL=""
# for i in 1 2 3 4 5; do
#   PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null \
#     | grep -o '"public_url":"https://[^"]*"' \
#     | head -1 \
#     | sed 's/"public_url":"//;s/"//')
#   if [ -n "$PUBLIC_URL" ]; then
#     break
#   fi
#   sleep 1
# done

# if [ -z "$PUBLIC_URL" ]; then
#   echo -e "${RED}Ngrok URL nahi mila. Log dekho: .demo-logs/ngrok.log${NC}"
#   tail -10 "$LOG_DIR/ngrok.log"
#   cleanup
#   exit 1
# fi

# # ── Success — URL show karo ───────────────────────────────────────
# echo ""
# echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
# echo -e "${BOLD}║                  DEMO READY!                            ║${NC}"
# echo -e "${BOLD}╠══════════════════════════════════════════════════════════╣${NC}"
# echo -e "${BOLD}║${NC}  ${GREEN}Public URL:${NC}  ${BOLD}${PUBLIC_URL}${NC}"
# echo -e "${BOLD}║${NC}  Local URL:   http://localhost:3001"
# echo -e "${BOLD}║${NC}  Ngrok UI:    http://localhost:4040"
# echo -e "${BOLD}╠══════════════════════════════════════════════════════════╣${NC}"
# echo -e "${BOLD}║${NC}  Yeh URL kisi ko bhi share karo — browser mein khulega  ${BOLD}║${NC}"
# echo -e "${BOLD}║${NC}  Band karne ke liye: ${YELLOW}Ctrl+C${NC}                           ${BOLD}║${NC}"
# echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
# echo ""

# # URL clipboard mein copy karo (macOS)
# echo "$PUBLIC_URL" | pbcopy 2>/dev/null && \
#   echo -e "  ${CYAN}(URL clipboard mein copy ho gaya!)${NC}" || true

# echo ""
# echo -e "  ${YELLOW}Logs:${NC}"
# echo -e "  Agent:    tail -f .demo-logs/agent.log"
# echo -e "  Frontend: tail -f .demo-logs/frontend.log"
# echo -e "  Ngrok:    tail -f .demo-logs/ngrok.log"
# echo ""

# # Processes ko monitor karo
# while true; do
#   if ! kill -0 "$AGENT_PID" 2>/dev/null; then
#     echo -e "${RED}Agent crash ho gaya! Restart kar raha hoon...${NC}"
#     uv run python src/agent.py dev > "$LOG_DIR/agent.log" 2>&1 &
#     AGENT_PID=$!
#   fi
#   if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
#     echo -e "${RED}Frontend crash ho gaya! Restart kar raha hoon...${NC}"
#     node "$SCRIPT_DIR/frontend-server.js" > "$LOG_DIR/frontend.log" 2>&1 &
#     FRONTEND_PID=$!
#   fi
#   sleep 5
# done

# ------------------



#!/bin/bash
# ─────────────────────────────────────────────
#  demo.sh — Start everything with one command
#  Usage: ./demo.sh
# ─────────────────────────────────────────────

set -e

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SCRIPT_DIR/.demo-logs"
mkdir -p "$LOG_DIR"

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║        Voice Assistant — Demo            ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── Cleanup already running processes ──────────────────────────
cleanup() {
  echo ""
  echo -e "${YELLOW}Shutting down...${NC}"
  if [ -n "$AGENT_PID" ];    then kill "$AGENT_PID"    2>/dev/null; fi
  if [ -n "$FRONTEND_PID" ]; then kill "$FRONTEND_PID" 2>/dev/null; fi
  if [ -n "$NGROK_PID" ];    then kill "$NGROK_PID"    2>/dev/null; fi
  echo -e "${GREEN}Done. Goodbye!${NC}"
  exit 0
}
trap cleanup SIGINT SIGTERM

# Stop any previously running services
echo -e "${YELLOW}Cleanup: Stopping previously running processes...${NC}"

# Kill any ngrok process
pkill -9 -f ngrok 2>/dev/null || true

# Force kill port 3001
PIDS_3001=$(lsof -ti:3001 2>/dev/null || true)
if [ -n "$PIDS_3001" ]; then
  echo "$PIDS_3001" | xargs kill -9 2>/dev/null || true
fi

# Force kill port 4040 (ngrok UI)
PIDS_4040=$(lsof -ti:4040 2>/dev/null || true)
if [ -n "$PIDS_4040" ]; then
  echo "$PIDS_4040" | xargs kill -9 2>/dev/null || true
fi

sleep 2

# ── Step 1: Start Python Agent ──────────────────────────────
echo -e "${CYAN}[1/3] Starting Python agent...${NC}"
cd "$SCRIPT_DIR"
uv run python src/agent.py dev > "$LOG_DIR/agent.log" 2>&1 &
AGENT_PID=$!
echo -e "      Agent PID: $AGENT_PID (log: .demo-logs/agent.log)"

# Give agent time to warm up
sleep 2

if ! kill -0 "$AGENT_PID" 2>/dev/null; then
  echo -e "${RED}Agent failed to start! Check log: .demo-logs/agent.log${NC}"
  tail -20 "$LOG_DIR/agent.log"
  exit 1
fi
echo -e "      ${GREEN}✓ Agent running${NC}"

# ── Step 2: Start Frontend server ───────────────────────────
echo -e "${CYAN}[2/3] Starting Frontend server (port 3001)...${NC}"
node "$SCRIPT_DIR/frontend-server.js" > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
sleep 1

if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo -e "${RED}Frontend server failed to start! Check log: .demo-logs/frontend.log${NC}"
  tail -10 "$LOG_DIR/frontend.log"
  cleanup
  exit 1
fi
echo -e "      ${GREEN}✓ Frontend server running${NC}"

# ── Step 3: Start Ngrok tunnel ──────────────────────────────
echo -e "${CYAN}[3/3] Creating Ngrok tunnel...${NC}"
ngrok http 3001 --log=stdout > "$LOG_DIR/ngrok.log" 2>&1 &
NGROK_PID=$!
sleep 3

# Get public URL from Ngrok API
PUBLIC_URL=""
for i in 1 2 3 4 5; do
  PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null \
    | grep -o '"public_url":"https://[^"]*"' \
    | head -1 \
    | sed 's/"public_url":"//;s/"//')
  if [ -n "$PUBLIC_URL" ]; then
    break
  fi
  sleep 1
done

if [ -z "$PUBLIC_URL" ]; then
  echo -e "${RED}Failed to get Ngrok URL. Check log: .demo-logs/ngrok.log${NC}"
  tail -10 "$LOG_DIR/ngrok.log"
  cleanup
  exit 1
fi

# ── Success — Show URLs ───────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║                      DEMO READY!                        ║${NC}"
echo -e "${BOLD}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${BOLD}║${NC}  ${GREEN}Public URL:${NC}  ${BOLD}${PUBLIC_URL}${NC}"
echo -e "${BOLD}║${NC}  Local URL:   http://localhost:3001"
echo -e "${BOLD}║${NC}  Ngrok UI:    http://localhost:4040"
echo -e "${BOLD}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${BOLD}║${NC}  Share this URL with anyone — it will open in browser   ${BOLD}║${NC}"
echo -e "${BOLD}║${NC}  To stop everything: ${YELLOW}Ctrl+C${NC}                         ${BOLD}║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Copy URL to clipboard (macOS)
echo "$PUBLIC_URL" | pbcopy 2>/dev/null && \
  echo -e "  ${CYAN}(URL copied to clipboard!)${NC}" || true

echo ""
echo -e "  ${YELLOW}Logs:${NC}"
echo -e "  Agent:    tail -f .demo-logs/agent.log"
echo -e "  Frontend: tail -f .demo-logs/frontend.log"
echo -e "  Ngrok:    tail -f .demo-logs/ngrok.log"
echo ""

# Monitor processes and auto-restart if needed
while true; do
  if ! kill -0 "$AGENT_PID" 2>/dev/null; then
    echo -e "${RED}Agent crashed! Restarting...${NC}"
    uv run python src/agent.py dev > "$LOG_DIR/agent.log" 2>&1 &
    AGENT_PID=$!
  fi
  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo -e "${RED}Frontend crashed! Restarting...${NC}"
    node "$SCRIPT_DIR/frontend-server.js" > "$LOG_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
  fi
  sleep 5
done