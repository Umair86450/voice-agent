"""
Custom Piper TTS plugin for LiveKit Agents.
Provides low-latency local Text-to-Speech for German language.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Optional, List

import numpy as np
from livekit.agents import tts
from piper import PiperVoice

logger = logging.getLogger(__name__)


class PiperTTS(tts.TTS):
    """
    Piper TTS plugin for LiveKit Agents.
    
    Features:
    - Low latency (local inference, no API calls)
    - German language support (Thorsten voice)
    - High quality neural TTS
    - No internet required after download
    """
    
    def __init__(
        self,
        model_path: str,
        config_path: str,
        sample_rate: int = 22050,
        **kwargs,
    ):
        super().__init__(
            capabilities=tts.TTSCapabilities(
                streaming=False,  # Piper doesn't support streaming
            ),
            sample_rate=sample_rate,
            num_channels=1,
        )
        
        self._model_path = model_path
        self._config_path = config_path
        self._sample_rate = sample_rate
        self._voice: Optional[PiperVoice] = None
        
        # Load the model
        self._load_model()
    
    def _load_model(self):
        """Load Piper voice model."""
        try:
            logger.info(f"Loading Piper TTS model from {self._model_path}")
            self._voice = PiperVoice.load(self._model_path)
            logger.info("Piper TTS model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Piper TTS model: {e}")
            raise
    
    def synthesize(self, text: str, **kwargs):
        """Synthesize speech from text."""
        return PiperChunkedStream(
            tts=self,
            input_text=text,
            voice=self._voice,
            sample_rate=self._sample_rate,
        )


class PiperChunkedStream(tts.ChunkedStream):
    """Chunked stream for Piper TTS."""
    
    def __init__(
        self,
        tts: PiperTTS,
        input_text: str,
        voice: Optional[PiperVoice],
        sample_rate: int,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._tts = tts
        self._input_text = input_text
        self._voice = voice
        self._sample_rate = sample_rate
        self._queue: asyncio.Queue[tts.SynthesizedAudio | None] = asyncio.Queue()
        self._main_task = asyncio.create_task(self._main_task_impl())
    
    async def _main_task_impl(self):
        """Main task to synthesize audio."""
        try:
            if not self._voice:
                raise RuntimeError("Piper voice not loaded")
            
            logger.info(f"Synthesizing text: {self._input_text[:50]}...")
            
            # Synthesize audio using Piper
            audio_data = self._voice.synthesize(
                self._input_text,
                noise_scale=0.667,
                length_scale=1.0,
                noise_w=0.8,
            )
            
            # Convert to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Create synthesized audio chunk
            audio = tts.SynthesizedAudio(
                text=self._input_text,
                data=audio_array.tobytes(),
                sample_rate=self._sample_rate,
            )
            
            await self._queue.put(audio)
            logger.info(f"Synthesis complete for: {self._input_text[:50]}...")
            
        except Exception as e:
            logger.error(f"Piper TTS synthesis failed: {e}")
            await self._queue.put(None)
        finally:
            await self._queue.put(None)
    
    async def __anext__(self) -> tts.SynthesizedAudio:
        """Get next audio chunk."""
        result = await self._queue.get()
        if result is None:
            raise StopAsyncIteration
        return result
    
    async def aclose(self):
        """Close the stream."""
        if self._main_task:
            self._main_task.cancel()
            try:
                await self._main_task
            except asyncio.CancelledError:
                pass


# Helper function to create Piper TTS instance
def create_piper_tts(
    model_path: str,
    config_path: str,
    **kwargs,
) -> PiperTTS:
    """
    Create a Piper TTS instance.
    
    Args:
        model_path: Path to .onnx model file
        config_path: Path to .onnx.json config file
        **kwargs: Additional options
    
    Returns:
        PiperTTS instance
    """
    return PiperTTS(
        model_path=model_path,
        config_path=config_path,
        **kwargs,
    )
