# CI/CD Guardian Agent Logs

This directory contains structured logs from the agent.

Log file: `agent.log`

The log file is automatically created when the agent starts and includes:
- Info: Normal operations and successful actions
- Warning: Non-critical issues
- Error: Critical errors with full stack traces
- Debug: Detailed debugging information

Logs are formatted as:
```
TIMESTAMP - MODULE - LEVEL - MESSAGE
```

Example:
```
2025-11-29 10:30:45,123 - src.agent - INFO - CI/CD Guardian Agent starting up...
2025-11-29 10:30:45,456 - src.policy_enforcer - INFO - PolicyEnforcer initialized with config
2025-11-29 10:30:50,789 - src.agent - INFO - Analyzing pipeline: build-12345
```

