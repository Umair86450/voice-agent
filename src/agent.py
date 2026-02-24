import logging
from pathlib import Path

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    room_io,
)
from livekit.plugins import silero
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
    proc.userdata["vad"] = silero.VAD.load()
    
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
        
        # Use Deepgram STT + Groq LLM + Piper TTS
        session = AgentSession(
            stt=inference.STT(model="deepgram/nova-3", language="de"),
            llm=inference.LLM(model="groq/llama-3.1-8b-instant"),
            tts=tts_plugin,  # Local Piper TTS
            turn_detection=MultilingualModel(),
            vad=ctx.proc.userdata["vad"],
            preemptive_generation=True,
        )
    else:
        # Fallback to Cartesia TTS (cloud)
        logger.warning("Piper TTS not found, using Cartesia TTS")
        
        session = AgentSession(
            stt=inference.STT(model="deepgram/nova-3", language="multi"),
            llm=inference.LLM(model="openai/gpt-4.1-mini"),
            tts=inference.TTS(
                model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
            ),
            turn_detection=MultilingualModel(),
            vad=ctx.proc.userdata["vad"],
            preemptive_generation=True,
        )

    # Start the session
    await session.start(
        agent=Assistant(),
        room=ctx.room,
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
