"""Probe function: checks whether TCP ports on the firewall management interfaces accept connections.

This function runs inside the its-mgmt-vpc so it can reach the private management IPs. It has no
route to any AWS API, so it only reports results. The collector function publishes them.
"""

import socket
import time
from datetime import datetime, timezone
from uuid import uuid4

CONNECT_TIMEOUT_SECONDS = 5


def log(level, run_id, message):
    """Write one log line in the standard ARL format.

    Args:
        level: Severity label, for example INFO or ERROR.
        run_id: Short identifier that ties together all lines from one invocation.
        message: Text to log.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level:<5}] [{run_id}] {message}")


def check_tcp(host, port, timeout_seconds=CONNECT_TIMEOUT_SECONDS):
    """Try to open a TCP connection and report whether it succeeded.

    Args:
        host: IP address or host name to connect to.
        port: TCP port number.
        timeout_seconds: How long to wait before giving up.

    Returns:
        A dictionary with keys reachable (bool), detail (str), and elapsed_ms (int).
    """
    started = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            reachable, detail = True, "connected"
    except OSError as error:
        reachable, detail = False, f"{type(error).__name__}: {error}"
    elapsed_ms = int((time.monotonic() - started) * 1000)
    return {"reachable": reachable, "detail": detail, "elapsed_ms": elapsed_ms}


def handler(event, context):
    """Lambda entry point. Probe every target in the event.

    Args:
        event: Dictionary with a targets list. Each target has name, host, and port.
        context: Lambda context object. Not used.

    Returns:
        A dictionary with a results list. Each result has name, host, port, reachable, detail, and elapsed_ms.
    """
    run_id = uuid4().hex[:6].upper()
    results = []
    for target in event["targets"]:
        outcome = check_tcp(target["host"], int(target["port"]))
        level = "INFO" if outcome["reachable"] else "WARN"
        log(level, run_id, f"Probed a firewall management port. Name={target['name']} Host={target['host']} "
                           f"Port={target['port']} Reachable={outcome['reachable']} Detail={outcome['detail']} "
                           f"ElapsedMs={outcome['elapsed_ms']}")
        results.append({**target, **outcome})
    return {"results": results}
