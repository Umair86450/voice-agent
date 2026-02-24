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

# ── Realistic call settings (working agent se liye) ──────────────
MIN_ENDPOINTING_DELAY       = 0.25   # 250ms baad turn complete maano
MAX_ENDPOINTING_DELAY       = 1.5    # zyada wait nahi — jaldi respond karo
ALLOW_INTERRUPTIONS         = True
MIN_INTERRUPTION_DURATION   = 0.5    # 500ms speech = real interruption
MIN_INTERRUPTION_WORDS      = 0      # 0 = koi bhi sound interrupt kare
FALSE_INTERRUPTION_TIMEOUT  = 2.0    # 2s wait karo — false interrupt confirm karo
RESUME_FALSE_INTERRUPTION   = True   # galat interrupt hua to agent resume kare
DISCARD_UNINTERRUPTIBLE     = True


def get_piper_model_path() -> str | None:
    model_path = Path.home() / ".cache" / "livekit" / "piper" / "de_DE-thorsten-medium.onnx"
    if model_path.exists():
        return str(model_path)
    return None


class Assistant(Agent):
    """Agent — settings dono jagah set hain: Agent + AgentSession (working agent pattern)."""

    def __init__(self) -> None:
        super().__init__(
            instructions="""Du bist ein hilfreicher KI-Sprachassistent. Der Benutzer spricht mit dir per Sprache.
            Antworte immer auf Deutsch, egal in welcher Sprache der Benutzer spricht.
            Deine Antworten sind kurz, präzise und ohne komplexe Formatierungen oder Sonderzeichen.
            Du bist freundlich, neugierig und hast einen guten Sinn für Humor.
            Sprich natürlich und fließend wie ein echter deutschsprachiger Assistent.""",
            # Agent pe bhi set karo — working agent ka pattern
            min_endpointing_delay=MIN_ENDPOINTING_DELAY,
            max_endpointing_delay=MAX_ENDPOINTING_DELAY,
            allow_interruptions=ALLOW_INTERRUPTIONS,
        )

    async def on_enter(self) -> None:
        """Agent room join karte hi pehle khud greeting de."""
        await self.session.say("Hallo! Wie kann ich Ihnen helfen?")


server = AgentServer()


def prewarm(proc: JobProcess):
    # VAD — Silero defaults use karo (None = override mat karo)
    # Working agent ne yahi kiya tha — custom values se better results
    proc.userdata["vad"] = silero.VAD.load()

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
    ctx.log_context_fields = {"room": ctx.room.name}

    vad = ctx.proc.userdata["vad"]
    piper_model_path = get_piper_model_path()

    if piper_model_path:
        logger.info(f"Using Piper TTS: {piper_model_path}")
        from piper_tts_plugin import create_piper_tts
        tts_plugin = create_piper_tts(
            model_path=piper_model_path,
            config_path=piper_model_path + ".json",
        )
    else:
        logger.warning("Piper TTS not found, using Groq TTS")
        tts_plugin = groq.TTS(model="aura-2-zeus-en")

    session = AgentSession(
        stt=groq.STT(model="whisper-large-v3-turbo", language="de"),
        llm=groq.LLM(model="llama-3.1-8b-instant"),
        tts=tts_plugin,
        vad=vad,
        turn_detection=MultilingualModel(),
        preemptive_generation=True,
        # Turn detection
        min_endpointing_delay=MIN_ENDPOINTING_DELAY,
        max_endpointing_delay=MAX_ENDPOINTING_DELAY,
        # Interruption — realistic barge-in
        allow_interruptions=ALLOW_INTERRUPTIONS,
        min_interruption_duration=MIN_INTERRUPTION_DURATION,
        min_interruption_words=MIN_INTERRUPTION_WORDS,
        false_interruption_timeout=FALSE_INTERRUPTION_TIMEOUT,
        resume_false_interruption=RESUME_FALSE_INTERRUPTION,
        discard_audio_if_uninterruptible=DISCARD_UNINTERRUPTIBLE,
    )

    @session.on("user_input_transcribed")
    def on_stt(event):
        if event.is_final:
            print(f"\n🎤 USER: {event.transcript}")

    @session.on("conversation_item_added")
    def on_llm(event):
        item = event.item
        if hasattr(item, "role") and item.role == "assistant":
            text = item.text_content
            if text:
                print(f"🤖 AGENT: {text}")

    await session.start(
        agent=Assistant(),
        room=ctx.room,
    )

    await ctx.wait_for_participant()


if __name__ == "__main__":
    cli.run_app(server)
