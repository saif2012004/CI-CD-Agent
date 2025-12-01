"""
Registration script for CI/CD Guardian Agent
Registers the agent with the Supervisor and displays full capabilities
"""
import requests
import json
import sys
from typing import Optional


def register_agent(agent_url: str, supervisor_url: Optional[str] = None) -> None:
    """
    Register CI/CD Guardian Agent with Supervisor

    Args:
        agent_url: URL of the CI/CD Guardian Agent
        supervisor_url: URL of the Supervisor (optional)
    """
    print("🛡️  CI/CD Guardian Agent - Registration")
    print("=" * 60)
    print()

    # Get agent registration information
    try:
        print(f"📡 Connecting to agent at: {agent_url}")
        response = requests.post(f"{agent_url}/register", timeout=10)
        response.raise_for_status()

        agent_info = response.json()

        print("✅ Successfully connected to agent!")
        print()
        print("📋 Agent Information:")
        print("-" * 60)
        print(f"  Agent ID: {agent_info['agent_id']}")
        print(f"  Agent Type: {agent_info['agent_type']}")
        print(f"  Status: {agent_info['status']}")
        print()

        print("🎯 Capabilities:")
        for capability in agent_info['capabilities']:
            print(f"  ✓ {capability}")
        print()

        print("🔌 Endpoints:")
        for endpoint_name, endpoint_url in agent_info['endpoints'].items():
            print(f"  {endpoint_name}: {endpoint_url}")
        print()

        print("📊 Metadata:")
        for key, value in agent_info['metadata'].items():
            if isinstance(value, list):
                print(f"  {key}:")
                for item in value:
                    print(f"    - {item}")
            else:
                print(f"  {key}: {value}")
        print()

        # If supervisor URL provided, send registration to supervisor
        if supervisor_url:
            print(f"🔗 Registering with Supervisor at: {supervisor_url}")
            try:
                supervisor_response = requests.post(
                    f"{supervisor_url}/agents/register",
                    json=agent_info,
                    timeout=10
                )
                supervisor_response.raise_for_status()
                print("✅ Successfully registered with Supervisor!")
                print()
                print("Supervisor Response:")
                print(json.dumps(supervisor_response.json(), indent=2))
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Warning: Could not register with Supervisor: {e}")
                print("   (This is normal if Supervisor is not yet running)")
        else:
            print("ℹ️  No Supervisor URL provided - skipping Supervisor registration")
            print("   To register with Supervisor, run:")
            print(f"   python register_with_supervisor.py {agent_url} <supervisor_url>")

        print()
        print("=" * 60)
        print("🎉 Registration complete!")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to agent: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Ensure the agent is running")
        print("  2. Check the URL is correct")
        print("  3. Verify network connectivity")
        sys.exit(1)


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python register_with_supervisor.py <agent_url> [supervisor_url]")
        print()
        print("Examples:")
        print("  # Local agent")
        print("  python register_with_supervisor.py http://localhost:8000")
        print()
        print("  # Production agent")
        print("  python register_with_supervisor.py https://ci-cd-agent.onrender.com")
        print()
        print("  # With supervisor")
        print("  python register_with_supervisor.py https://ci-cd-agent.onrender.com https://supervisor.example.com")
        sys.exit(1)

    agent_url = sys.argv[1].rstrip('/')
    supervisor_url = sys.argv[2].rstrip('/') if len(sys.argv) > 2 else None

    register_agent(agent_url, supervisor_url)


if __name__ == "__main__":
    main()
