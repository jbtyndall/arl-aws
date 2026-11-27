"""Collector function: runs the probe on a schedule and publishes the results as CloudWatch metrics.

The probe function lives in the its-mgmt-vpc and cannot call AWS APIs. This function is outside any VPC,
so it can invoke the probe and publish metrics. CloudWatch alarms on those metrics handle thresholds and
duplicate suppression. If this function or the probe stops working, the metrics go missing and the
alarms fire, because they treat missing data as a failure.
"""

import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import boto3

METRIC_NAMESPACE = "ARL/FirewallMonitor"
METRIC_NAME = "ManagementReachable"


def log(level, run_id, message):
    """Write one log line in the standard ARL format.

    Args:
        level: Severity label, for example INFO or ERROR.
        run_id: Short identifier that ties together all lines from one invocation.
        message: Text to log.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level:<5}] [{run_id}] {message}")


def parse_targets(raw_targets, port):
    """Convert the TARGETS setting into the list the probe expects.

    Args:
        raw_targets: Comma-separated name=host pairs, for example fw1=10.251.253.4,fw2=10.251.253.5.
        port: TCP port to probe on every target.

    Returns:
        A list of dictionaries with name, host, and port.

    Raises:
        ValueError: If an entry is not in name=host form.
    """
    targets = []
    for entry in raw_targets.split(","):
        name, separator, host = entry.strip().partition("=")
        if not separator or not name or not host:
            raise ValueError(f"Invalid TARGETS entry '{entry}'. Expected name=host.")
        targets.append({"name": name, "host": host, "port": port})
    return targets


def build_metric_data(results):
    """Turn probe results into CloudWatch metric data points.

    Args:
        results: The results list returned by the probe function.

    Returns:
        A list of MetricData dictionaries. Value is 1 when the port answered and 0 when it did not.
    """
    return [
        {
            "MetricName": METRIC_NAME,
            "Dimensions": [{"Name": "Firewall", "Value": result["name"]}],
            "Value": 1.0 if result["reachable"] else 0.0,
            "Unit": "Count",
        }
        for result in results
    ]


def handler(event, context):
    """Lambda entry point. Invoke the probe and publish its results.

    Args:
        event: Scheduler event. Not used.
        context: Lambda context object. Not used.

    Returns:
        A dictionary summarizing which firewalls answered.

    Raises:
        RuntimeError: If the probe function fails. No metrics are published in that case, so the
            alarms see missing data and fire.
    """
    run_id = uuid4().hex[:6].upper()
    targets = parse_targets(os.environ["TARGETS"], int(os.environ["PROBE_PORT"]))

    response = boto3.client("lambda").invoke(
        FunctionName=os.environ["PROBE_FUNCTION_NAME"],
        InvocationType="RequestResponse",
        Payload=json.dumps({"targets": targets}).encode("utf-8"),
    )
    payload = json.loads(response["Payload"].read())
    if "FunctionError" in response:
        log("ERROR", run_id, f"The probe function failed. Detail={payload}")
        raise RuntimeError(f"Probe function failed: {payload}")

    boto3.client("cloudwatch").put_metric_data(
        Namespace=METRIC_NAMESPACE, MetricData=build_metric_data(payload["results"])
    )
    summary = {result["name"]: result["reachable"] for result in payload["results"]}
    log("INFO", run_id, f"Published firewall management reachability metrics. Namespace={METRIC_NAMESPACE} "
                        f"Metric={METRIC_NAME} Values={summary}")
    return summary
