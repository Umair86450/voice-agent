"""
Test Piper TTS locally before running the full agent.
Usage:
    uv run python src/test_piper.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from piper_tts_plugin import create_piper_tts

def test_piper():
    """Test Piper TTS with a simple German sentence."""
    print("=" * 60)
    print("Testing Piper TTS (German)")
    print("=" * 60)
    
    # Get model paths
    model_dir = Path.home() / ".cache" / "livekit" / "piper"
    model_path = model_dir / "de_DE-thorsten-medium.onnx"
    config_path = model_dir / "de_DE-thorsten-medium.onnx.json"
    
    if not model_path.exists():
        print(f"✗ Model not found at {model_path}")
        print("Run: uv run python src/download_piper_models.py")
        return False
    
    if not config_path.exists():
        print(f"✗ Config not found at {config_path}")
        print("Run: uv run python src/download_piper_models.py")
        return False
    
    print(f"✓ Model found: {model_path}")
    print(f"✓ Config found: {config_path}")
    print()
    
    # Create TTS instance
    print("Loading Piper TTS...")
    try:
        tts = create_piper_tts(
            model_path=str(model_path),
            config_path=str(config_path),
        )
        print("✓ Piper TTS loaded successfully!")
        print()
    except Exception as e:
        print(f"✗ Failed to load Piper TTS: {e}")
        return False
    
    # Test synthesis
    test_texts = [
        "Hallo, wie geht es dir?",
        "Gern geschehen, wie kann ich dir helfen?",
        "Vielen Dank!",
    ]
    
    for text in test_texts:
        print(f"Synthesizing: \"{text}\"")
        try:
            stream = tts.synthesize(text)
            chunks = []
            async def collect():
                async for chunk in stream:
                    chunks.append(chunk)
            
            import asyncio
            asyncio.run(collect())
            
            if chunks:
                print(f"  ✓ Generated {len(chunks)} audio chunk(s)")
                print(f"    Sample rate: {chunks[0].sample_rate} Hz")
                print(f"    Data size: {len(chunks[0].data)} bytes")
            else:
                print(f"  ✗ No audio generated")
        except Exception as e:
            print(f"  ✗ Synthesis failed: {e}")
        print()
    
    print("=" * 60)
    print("✓ Piper TTS test completed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_piper()
