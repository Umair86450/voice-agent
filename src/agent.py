import logging
import os

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
)
from livekit.plugins import deepgram, groq, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")

load_dotenv(".env.local")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""Du bist ein hilfreicher KI-Sprachassistent. Der Benutzer spricht mit dir per Sprache.
            Antworte immer auf Deutsch, egal in welcher Sprache der Benutzer spricht.
            Deine Antworten sind kurz, präzise und ohne komplexe Formatierungen oder Sonderzeichen.
            Du bist freundlich, neugierig und hast einen guten Sinn für Humor.
            Sprich natürlich und fließend wie ein echter deutschsprachiger Assistent.""",
        )

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.1,
        min_silence_duration=0.3,      # 0.8 → 0.3: turn detector handle karega baaki
        activation_threshold=0.4,
        prefix_padding_duration=0.2,
    )


server.setup_fnc = prewarm


@server.rtc_session()
async def my_agent(ctx: JobContext):
    print("=== AGENT JOB  - room:", ctx.room.name, "===")
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Voice pipeline: Groq STT + Groq LLM + Deepgram TTS
    session = AgentSession(
        stt=groq.STT(model="whisper-large-v3-turbo", language="de"),
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=deepgram.TTS(model="aura-2-zeus-en"),
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
    )

    @session.on("user_input_transcribed")
    def on_stt(event):
        if event.is_final:
            logger.info(f"[STT] User: {event.transcript}")

    @session.on("conversation_item_added")
    def on_llm(event):
        item = event.item
        if hasattr(item, "role") and item.role == "assistant":
            text = item.text_content
            if text:
                logger.info(f"[LLM] Agent: {text}")

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Pehle room join karo
    await ctx.connect()

    # Phir voice pipeline start karo
    await session.start(
        agent=Assistant(),
        room=ctx.room,
    )


if __name__ == "__main__":
    cli.run_app(server)



# --------------


# # syntax=docker/dockerfile:1

# # Use the official UV Python base image with Python 3.13 on Debian Bookworm
# # UV is a fast Python package manager that provides better performance than pip
# # We use the slim variant to keep the image size smaller while still having essential tools
# ARG PYTHON_VERSION=3.13
# FROM ghcr.io/astral-sh/uv:python${PYTHON_VERSION}-bookworm-slim AS base

# # Keeps Python from buffering stdout and stderr to avoid situations where
# # the application crashes without emitting any logs due to buffering.
# ENV PYTHONUNBUFFERED=1

# # Create a non-privileged user that the app will run under.
# # See https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
# ARG UID=10001
# RUN adduser \
#     --disabled-password \
#     --gecos "" \
#     --home "/app" \
#     --shell "/sbin/nologin" \
#     --uid "${UID}" \
#     appuser

# # Install build dependencies required for Python packages with native extensions
# # gcc: C compiler needed for building Python packages with C extensions
# # python3-dev: Python development headers needed for compilation
# # We clean up the apt cache after installation to keep the image size down
# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     python3-dev \
#   && rm -rf /var/lib/apt/lists/*

# # Create a new directory for our application code
# # And set it as the working directory
# WORKDIR /app

# # Copy dependency files and source package for build
# COPY pyproject.toml uv.lock README.md ./
# COPY src/ src/

# # Install Python dependencies using UV's lock file
# # --locked ensures we use exact versions from uv.lock for reproducible builds
# RUN uv sync --locked

# # Copy all remaining application files into the container
# COPY . .

# # Change ownership of all app files to the non-privileged user
# # This ensures the application can read/write files as needed
# RUN chown -R appuser:appuser /app

# # Switch to the non-privileged user for all subsequent operations
# # This improves security by not running as root
# USER appuser

# # Pre-download any ML models or files the agent needs
# # This ensures the container is ready to run immediately without downloading
# # dependencies at runtime, which improves startup time and reliability
# RUN uv run src/agent.py download-files

# # Run the application using UV
# # UV will activate the virtual environment and run the agent.
# # The "start" command tells the worker to connect to LiveKit and begin waiting for jobs.
# CMD ["uv", "run", "src/agent.py", "start"]
