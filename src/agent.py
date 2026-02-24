import logging
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
)
from livekit.plugins import groq, silero
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


server = AgentServer()


def get_piper_model_path() -> str | None:
    """Get path to Piper TTS model."""
    model_path = Path.home() / ".cache" / "livekit" / "piper" / "de_DE-thorsten-medium.onnx"
    if model_path.exists():
        return str(model_path)
    return None


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load(
        min_speech_duration=0.1,
        min_silence_duration=0.3,
        activation_threshold=0.4,
        prefix_padding_duration=0.2,
    )
    
    # Pre-load Piper TTS if available
    model_path = get_piper_model_path()
    if model_path:
        try:
            from piper import PiperVoice
            proc.userdata["piper_voice"] = PiperVoice.load(model_path)
            logger.info("Piper TTS pre-loaded")
        except Exception as e:
            logger.warning(f"Failed to pre-load Piper TTS: {e}")


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Check if Piper TTS is available
    piper_model_path = get_piper_model_path()

    if piper_model_path:
        # Use Piper TTS (local, low latency)
        logger.info(f"Using Piper TTS: {piper_model_path}")

        # Import custom Piper TTS plugin
        from piper_tts_plugin import create_piper_tts
        tts_plugin = create_piper_tts(
            model_path=piper_model_path,
            config_path=piper_model_path + ".json",
        )

        # Use Groq STT + Groq LLM + Piper TTS
        session = AgentSession(
            stt=groq.STT(model="whisper-large-v3-turbo", language="de"),
            llm=groq.LLM(model="llama-3.1-8b-instant"),
            tts=tts_plugin,  # Local Piper TTS
            turn_detection=MultilingualModel(),
            vad=ctx.proc.userdata["vad"],
            preemptive_generation=True,
        )
    else:
        # Fallback to all Groq + Cartesia
        logger.warning("Piper TTS not found, using Cartesia TTS")

        session = AgentSession(
            stt=groq.STT(model="whisper-large-v3-turbo", language="multi"),
            llm=groq.LLM(model="llama-3.1-8b-instant"),
            tts=groq.TTS(model="aura-2-zeus-en"),
            turn_detection=MultilingualModel(),
            vad=ctx.proc.userdata["vad"],
            preemptive_generation=True,
        )

    # Start the session - this automatically connects to the room
    await session.start(
        agent=Assistant(),
        room=ctx.room,
    )

    # Keep the agent running until the room is closed
    await ctx.wait_for_participant()


if __name__ == "__main__":
    cli.run_app(server)
