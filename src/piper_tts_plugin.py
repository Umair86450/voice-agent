"""
Custom Piper TTS plugin for LiveKit Agents.
Provides low-latency local Text-to-Speech for German language.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator, Optional

import numpy as np
from livekit.agents import tts
from piper import PiperVoice

logger = logging.getLogger(__name__)


@dataclass
class PiperTTSOptions:
    """Options for Piper TTS."""
    model_path: str
    config_path: str
    sample_rate: int = 22050
    noise_scale: float = 0.667
    length_scale: float = 1.0
    noise_w: float = 0.8
    sentence_silence: float = 0.2


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
                streaming=False,  # Piper doesn't support streaming yet
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
    
    def synthesize(self, text: str) -> tts.ChunkedStream:
        """Synthesize speech from text."""
        return tts.ChunkedStream(
            tts=self,
            input_text=text,
            conn_options=tts.ChunkedStream.ConnOptions(),
        )
    
    async def _do_synthesize(
        self, text: str
    ) -> AsyncIterator[tts.SynthesizedAudio]:
        """Internal method to synthesize audio."""
        if not self._voice:
            raise RuntimeError("Piper voice not loaded")
        
        logger.info(f"Synthesizing text: {text[:50]}...")
        
        try:
            # Synthesize audio using Piper
            audio_data = self._voice.synthesize(
                text,
                noise_scale=0.667,
                length_scale=1.0,
                noise_w=0.8,
            )
            
            # Convert to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Create synthesized audio chunk
            yield tts.SynthesizedAudio(
                text=text,
                data=audio_array.tobytes(),
                sample_rate=self._sample_rate,
            )
            
            logger.info(f"Synthesis complete for: {text[:50]}...")
            
        except Exception as e:
            logger.error(f"Piper TTS synthesis failed: {e}")
            raise


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
