from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class RemediationAction:
    key: str
    target_service: str
    compose_service: str
    description: str
    risk_level: str


REMEDIATION_CATALOG = {
    "restart_benchmark_redis": RemediationAction(
        key="restart_benchmark_redis",
        target_service="benchmark-redis",
        compose_service="benchmark-redis",
        description="Restart the benchmark Redis container",
        risk_level="MEDIUM",
    ),
    "restart_benchmark_postgresql": RemediationAction(
        key="restart_benchmark_postgresql",
        target_service="benchmark-postgresql",
        compose_service="benchmark-db",
        description="Restart the benchmark PostgreSQL container",
        risk_level="HIGH",
    ),
    "restart_benchmark_api": RemediationAction(
        key="restart_benchmark_api",
        target_service="benchmark-api",
        compose_service="benchmark-api",
        description="Restart the benchmark API container",
        risk_level="MEDIUM",
    ),
}

def execute_remediation_action(action_key: str) -> dict:
    action = REMEDIATION_CATALOG.get(action_key)

    if action is None:
        raise ValueError(
            f"Unsupported remediation action: {action_key}"
        )

    repo_root = Path(__file__).resolve().parents[2]

    command = [
        "docker",
        "compose",
        "--project-directory",
        str(repo_root),
        "restart",
        action.compose_service,
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "Docker remediation timed out.",
        }

    except OSError as exc:
        return {
            "success": False,
            "exit_code": None,
            "stdout": "",
            "stderr": str(exc),
        }

    return {
        "success": completed.returncode == 0,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }