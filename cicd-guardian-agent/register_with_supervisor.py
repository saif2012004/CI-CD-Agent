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
        
        print("✅ Agent registration successful!")
        print()
        print("=" * 60)
        print("AGENT INFORMATION")
        print("=" * 60)
        print(json.dumps(agent_info, indent=2))
        print("=" * 60)
        print()
        
        # Display key capabilities
        print("🔑 KEY CAPABILITIES:")
        for capability in agent_info.get("capabilities", []):
            print(f"  ✓ {capability}")
        print()
        
        # Display endpoints
        print("🌐 AVAILABLE ENDPOINTS:")
        for name, url in agent_info.get("endpoints", {}).items():
            print(f"  • {name:12} → {url}")
        print()
        
        # Register with supervisor if URL provided
        if supervisor_url:
            print(f"📤 Registering with Supervisor at: {supervisor_url}")
            try:
                supervisor_response = requests.post(
                    f"{supervisor_url}/register_agent",
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
                print("   Agent is running but not connected to Supervisor")
        else:
            print("ℹ️  No Supervisor URL provided")
            print("   Agent is running in standalone mode")
        
        print()
        print("=" * 60)
        print("✨ Registration complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Test the agent with: curl -X POST {}/analyze".format(agent_url))
        print("2. View metrics: curl {}/metrics".format(agent_url))
        print("3. Health check: curl {}/health".format(agent_url))
        print("4. API docs: {}/docs".format(agent_url))
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to agent at {agent_url}")
        print("   Make sure the agent is running:")
        print("   python -m uvicorn src.agent:app --reload")
        sys.exit(1)
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error during registration: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Register CI/CD Guardian Agent with Supervisor"
    )
    parser.add_argument(
        "--agent-url",
        default="http://localhost:8000",
        help="URL of the CI/CD Guardian Agent (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--supervisor-url",
        help="URL of the Supervisor (optional)"
    )
    
    args = parser.parse_args()
    
    register_agent(args.agent_url, args.supervisor_url)


if __name__ == "__main__":
    main()

