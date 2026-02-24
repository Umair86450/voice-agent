"""
Download Piper TTS German models for low-latency local TTS.
Usage:
    uv run python src/download_piper_models.py
"""

import os
import urllib.request
import hashlib
from pathlib import Path

# Piper TTS German model - Thorsten (low latency, good quality)
# This is a small, fast model perfect for demos
MODEL_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx"
CONFIG_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json"

# Expected file sizes for verification
MODEL_SIZE = 52428800  # ~50MB (approximate)
CONFIG_SIZE = 10240    # ~10KB (approximate)

def get_model_dir():
    """Get the directory where models are stored."""
    # Use same directory as other LiveKit models
    base_dir = Path.home() / ".cache" / "livekit" / "piper"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def download_file(url, dest_path, description):
    """Download a file with progress."""
    print(f"Downloading {description}...")
    print(f"  URL: {url}")
    print(f"  Destination: {dest_path}")
    
    if dest_path.exists():
        print(f"  ✓ Already exists, skipping...")
        return True
    
    try:
        # Download with progress
        def reporthook(blocknum, blocksize, totalsize):
                    readsofar = blocknum * blocksize
                    if totalsize > 0:
                        percent = readsofar * 100 / totalsize
                        print(f"\r  Progress: {percent:.1f}%", end='')
        
        urllib.request.urlretrieve(url, dest_path, reporthook)
        print(f"\r  ✓ Download complete!")
        return True
    except Exception as e:
        print(f"\n  ✗ Download failed: {e}")
        return False

def verify_file(path, min_size):
    """Verify file was downloaded correctly."""
    if not path.exists():
        return False
    
    actual_size = path.stat().st_size
    print(f"  File size: {actual_size / 1024 / 1024:.2f} MB")
    
    # Basic size check (allow some variance)
    if actual_size < min_size * 0.5:
        print(f"  ✗ File seems too small, may be corrupted")
        return False
    
    return True

def main():
    print("=" * 60)
    print("Piper TTS German Model Downloader")
    print("=" * 60)
    print()
    
    model_dir = get_model_dir()
    model_path = model_dir / "de_DE-thorsten-medium.onnx"
    config_path = model_dir / "de_DE-thorsten-medium.onnx.json"
    
    print(f"Model directory: {model_dir}")
    print()
    
    # Download model
    model_ok = download_file(MODEL_URL, model_path, "German TTS model (ONNX)")
    if model_ok:
        model_ok = verify_file(model_path, 10 * 1024 * 1024)  # At least 10MB
    
    print()
    
    # Download config
    config_ok = download_file(CONFIG_URL, config_path, "German TTS config")
    if config_ok:
        config_ok = verify_file(config_path, 1024)  # At least 1KB
    
    print()
    
    # Summary
    print("=" * 60)
    if model_ok and config_ok:
        print("✓ SUCCESS! Piper TTS models downloaded successfully.")
        print()
        print(f"Model:  {model_path}")
        print(f"Config: {config_path}")
        print()
        print("You can now use Piper TTS in your agent:")
        print('  tts=piper.TTS(')
        print(f'      model_path="{model_path}",')
        print(f'      config_path="{config_path}"')
        print('  )')
    else:
        print("✗ FAILED! Some downloads failed.")
        print("Please check your internet connection and try again.")
    print("=" * 60)

if __name__ == "__main__":
    main()
