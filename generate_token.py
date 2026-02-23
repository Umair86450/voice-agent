"""
Client ke liye simple token generate karo.
Usage:
    uv run python generate_token.py
"""

import os
from dotenv import load_dotenv
from livekit.api import AccessToken, VideoGrants

load_dotenv(".env.local")

token = (
    AccessToken(
        api_key=os.environ["LIVEKIT_API_KEY"],
        api_secret=os.environ["LIVEKIT_API_SECRET"],
    )
    .with_identity("client-user")
    .with_name("Demo Client")
    .with_grants(VideoGrants(room_join=True, room="demo-room"))
    .to_jwt()
)

print("\n=== Playground mein paste karo ===")
print(f"URL:   {os.environ['LIVEKIT_URL']}")
print(f"Token: {token}\n")
