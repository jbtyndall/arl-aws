"""Remediator function: stops and starts a hung firewall when a high-confidence CloudWatch alarm fires.

Subscribed to the same SNS topic as the notifier. It only acts on ALARM notifications for the alarms listed
in the RULES setting. A mode stored in SSM Parameter Store acts as a kill switch:

    enabled   stop and start the instance
    dry-run   email what would have been done and change nothing
    disabled  do nothing

The decision logic is in decide() and has no AWS calls so it can be tested directly.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import boto3

MINIMUM_MINUTES_BETWEEN_RESTARTS = 60
ACTIVE_FIREWALL_MINIMUM_ENIS = 3
PEER_STATES_THAT_BLOCK_RESTART = {"pending", "stopping", "stopped", "shutting-down"}
STOP_WAIT_DELAY_SECONDS = 5
STOP_WAIT_MAX_ATTEMPTS = 150


def log(level, run_id, message):
    """Write one log line in the standard ARL format.

    Args:
        level: Severity label, for example INFO or ERROR.
        run_id: Short identifier that ties together all lines from one invocation.
        message: Text to log.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level:<5}] [{run_id}] {message}")


def parse_alarm(sns_record):
    """Extract the CloudWatch alarm details from one SNS record.

    Args:
        sns_record: One entry from the Records list of an SNS-triggered Lambda event.

    Returns:
        The alarm notification as a dictionary, or None if the message is not an alarm notification.
    """
    try:
        message = json.loads(sns_record["Sns"]["Message"])
    except (KeyError, TypeError, ValueError):
        return None
    if not isinstance(message, dict) or "AlarmName" not in message or "NewStateValue" not in message:
        return None
    return message


def describe_instance(ec2_client, instance_id):
    """Read the fields the decision needs from EC2.

    Args:
        ec2_client: A boto3 EC2 client.
        instance_id: The instance to describe.

    Returns:
        A dictionary with state (str), launch_time (datetime), and eni_count (int).
    """
    instance = ec2_client.describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]
    return {
        "state": instance["State"]["Name"],
        "launch_time": instance["LaunchTime"],
        "eni_count": len(instance.get("NetworkInterfaces", [])),
    }


def decide(rule, instance, peer, mode, now):
    """Decide whether to restart an instance. Pure function with no AWS calls.

    Args:
        rule: Dictionary with trigger ("instance-status" or "management").
        instance: Result of describe_instance for the alarming firewall.
        peer: Result of describe_instance for the other firewall.
        mode: enabled, dry-run, or disabled.
        now: Current time as a timezone-aware datetime.

    Returns:
        A dictionary with action (restart, would-restart, or skip) and reason (str).
    """
    if mode == "disabled":
        return {"action": "skip", "reason": "Auto-restart mode is disabled."}
    if mode not in ("enabled", "dry-run"):
        return {"action": "skip", "reason": f"Unknown auto-restart mode '{mode}'. Treating it as disabled."}
    if instance["state"] != "running":
        return {"action": "skip", "reason": f"Instance is {instance['state']}, not running."}
    if peer["state"] in PEER_STATES_THAT_BLOCK_RESTART:
        return {"action": "skip", "reason": f"The other firewall is {peer['state']}. Another restart may be in progress."}
    age = now - instance["launch_time"]
    if age < timedelta(minutes=MINIMUM_MINUTES_BETWEEN_RESTARTS):
        return {"action": "skip", "reason": f"Instance started {int(age.total_seconds() // 60)} minutes ago. "
                                            f"Minimum is {MINIMUM_MINUTES_BETWEEN_RESTARTS}."}
    is_active = instance["eni_count"] >= ACTIVE_FIREWALL_MINIMUM_ENIS
    if rule["trigger"] == "management" and is_active:
        return {"action": "skip", "reason": "This is the active firewall and the trigger is a management alarm. "
                                            "Alert only. A person decides."}
    action = "restart" if mode == "enabled" else "would-restart"
    role = "active" if is_active else "standby"
    return {"action": action, "reason": f"Trigger {rule['trigger']} on the {role} firewall."}


def restart_instance(ec2_client, run_id, instance_id):
    """Stop an instance, wait until it is stopped, then start it.

    Args:
        ec2_client: A boto3 EC2 client.
        run_id: Identifier for log lines.
        instance_id: The instance to restart.

    Raises:
        botocore.exceptions.WaiterError: If the instance does not stop within the wait limit. It is left
            stopping or stopped and must be started by hand.
    """
    ec2_client.stop_instances(InstanceIds=[instance_id])
    log("INFO", run_id, f"Stopped an EC2 instance. InstanceId={instance_id} Changes=State: running -> stopping")
    ec2_client.get_waiter("instance_stopped").wait(
        InstanceIds=[instance_id],
        WaiterConfig={"Delay": STOP_WAIT_DELAY_SECONDS, "MaxAttempts": STOP_WAIT_MAX_ATTEMPTS},
    )
    ec2_client.start_instances(InstanceIds=[instance_id])
    log("INFO", run_id, f"Started an EC2 instance. InstanceId={instance_id} Changes=State: stopped -> pending")


def build_email(alarm_name, rule, instance_id, outcome, error=None):
    """Create the subject and body of the action email.

    Args:
        alarm_name: Name of the alarm that triggered the action.
        rule: The rule dictionary for the alarm.
        instance_id: The instance acted on.
        outcome: The decide() result.
        error: Error text if the restart failed, otherwise None.

    Returns:
        A tuple of (subject, body).
    """
    label = {"restart": "AUTO-RESTART", "would-restart": "AUTO-RESTART DRY RUN"}[outcome["action"]]
    if error:
        label = "AUTO-RESTART FAILED"
    subject = f"[{label}] {rule['firewall']} ({instance_id})"
    lines = [
        f"Alarm:     {alarm_name}",
        f"Firewall:  {rule['firewall']}  Instance: {instance_id}",
        f"Reason:    {outcome['reason']}",
        "",
    ]
    if error:
        lines += [
            "THE RESTART FAILED. The instance may be left stopped or stopping.",
            f"Error: {error}",
            "Check it and start it by hand if needed:",
            f"aws ec2 start-instances --profile arl-its-govcloud --region us-gov-west-1 --instance-ids {instance_id}",
        ]
    elif outcome["action"] == "would-restart":
        lines += ["DRY RUN. Nothing was changed. Set the mode to enabled to allow automatic restarts."]
    else:
        lines += ["This firewall was stopped and started automatically. Check that it passes EC2 status checks and",
                  "shows Connected in Panorama. Find out why it hung. An automatic restart does not fix the cause."]
    lines += [
        "",
        "TO STOP AUTOMATIC RESTARTS",
        "aws ssm put-parameter --profile arl-its-govcloud --region us-gov-west-1 --name /arl-monitoring/firewall/auto-restart "
        "--type String --overwrite --value disabled",
        "",
        "Sent automatically by the arl-monitoring-firewall stack in the ARL-ITS account.",
    ]
    return subject, "\n".join(lines)


def send_email(ses_client, sender, recipients, subject, body):
    """Send a plain-text email through SES.

    Args:
        ses_client: A boto3 SESv2 client.
        sender: Verified From address.
        recipients: List of To addresses.
        subject: Email subject.
        body: Plain-text body.

    Returns:
        The SES message ID.
    """
    response = ses_client.send_email(
        FromEmailAddress=sender,
        Destination={"ToAddresses": recipients},
        Content={"Simple": {"Subject": {"Data": subject}, "Body": {"Text": {"Data": body}}}},
    )
    return response["MessageId"]


def handler(event, context):
    """Lambda entry point. Act on firewall alarm notifications.

    Args:
        event: SNS event with a Records list.
        context: Lambda context object. Not used.

    Raises:
        Exception: A failed restart is logged, emailed, and re-raised.
    """
    run_id = uuid4().hex[:6].upper()
    rules = json.loads(os.environ["RULES"])
    sender = os.environ["ALERT_FROM"]
    recipients = [address.strip() for address in os.environ["ALERT_TO"].split(",") if address.strip()]
    ec2_client = boto3.client("ec2")
    ssm_client = boto3.client("ssm")
    ses_client = boto3.client("sesv2")

    for record in event["Records"]:
        alarm = parse_alarm(record)
        if alarm is None or alarm["NewStateValue"] != "ALARM" or alarm["AlarmName"] not in rules:
            log("INFO", run_id, "Ignored a notification that is not an ALARM for a remediation rule.")
            continue

        rule = rules[alarm["AlarmName"]]
        mode = ssm_client.get_parameter(Name=os.environ["MODE_PARAMETER"])["Parameter"]["Value"]
        instance_id = rule["instance_id"]
        instance = describe_instance(ec2_client, instance_id)
        peer = describe_instance(ec2_client, rule["peer_instance_id"])
        outcome = decide(rule, instance, peer, mode, datetime.now(timezone.utc))
        log("INFO", run_id, f"Evaluated a firewall alarm. Alarm={alarm['AlarmName']} InstanceId={instance_id} "
                            f"Mode={mode} Action={outcome['action']} Reason={outcome['reason']}")
        if outcome["action"] == "skip":
            continue

        error = None
        if outcome["action"] == "restart":
            try:
                restart_instance(ec2_client, run_id, instance_id)
            except Exception as failure:
                error = f"{type(failure).__name__}: {failure}"
                log("ERROR", run_id, f"Failed to restart an EC2 instance. InstanceId={instance_id} Error={error}")
        subject, body = build_email(alarm["AlarmName"], rule, instance_id, outcome, error)
        message_id = send_email(ses_client, sender, recipients, subject, body)
        log("INFO", run_id, f"Sent an auto-restart email through SES. InstanceId={instance_id} "
                            f"To={','.join(recipients)} MessageId={message_id}")
        if error:
            raise RuntimeError(error)
