"""LiveKit Voice Agent - Multilingual voice calling agent."""


def main():
    """Entry point for the livekit-voice-agent command."""
    from livekit.agents import cli

    # Import agent server from agent.py
    from .. import agent

    cli.run_app(agent.server)


if __name__ == "__main__":
    main()
