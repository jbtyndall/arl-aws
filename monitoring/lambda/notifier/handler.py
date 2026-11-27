"""Notifier function: turns CloudWatch alarm notifications from SNS into plain-English emails sent through SES.

The alarm description (set in the CloudFormation template) carries the explanation for each alarm, so this
function stays generic. It sends on both ALARM and OK so operators know when a problem clears.
"""

import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import boto3

STATE_WORDS = {"ALARM": "ALARM", "OK": "OK", "INSUFFICIENT_DATA": "NO DATA"}


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
        The alarm notification as a dictionary.

    Raises:
        ValueError: If the SNS message is not a CloudWatch alarm notification.
    """
    message = json.loads(sns_record["Sns"]["Message"])
    if "AlarmName" not in message or "NewStateValue" not in message:
        raise ValueError("SNS message is not a CloudWatch alarm notification.")
    return message


def build_email(alarm, runbook):
    """Create the email subject and body for an alarm notification.

    Args:
        alarm: The alarm notification dictionary from parse_alarm.
        runbook: Text telling the reader where the troubleshooting steps are.

    Returns:
        A tuple of (subject, body).
    """
    state = STATE_WORDS.get(alarm["NewStateValue"], alarm["NewStateValue"])
    name = alarm["AlarmName"].replace("\r", " ").replace("\n", " ")
    subject = f"[{state}] {name}"
    description = alarm.get("AlarmDescription") or "No description was set on this alarm."
    body = "\n".join([
        f"Alarm:    {alarm['AlarmName']}",
        f"State:    {alarm.get('OldStateValue', '?')} -> {alarm['NewStateValue']}",
        f"Time:     {alarm.get('StateChangeTime', 'unknown')}",
        f"Account:  {alarm.get('AWSAccountId', 'unknown')}  Region: {alarm.get('Region', 'unknown')}",
        "",
        "WHAT THIS MEANS AND WHAT TO DO",
        description,
        "",
        "WHY CLOUDWATCH CHANGED THE STATE",
        alarm.get("NewStateReason", "No reason given."),
        "",
        "RUNBOOK",
        runbook,
        "",
        "This message was sent automatically by the arl-monitoring-firewall stack in the ARL-ITS account.",
    ])
    return subject, body


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
    """Lambda entry point. Email every alarm notification in the SNS event.

    Args:
        event: SNS event with a Records list.
        context: Lambda context object. Not used.

    Raises:
        Exception: Any failure is logged and re-raised so Lambda retries the delivery.
    """
    run_id = uuid4().hex[:6].upper()
    sender = os.environ["ALERT_FROM"]
    recipients = [address.strip() for address in os.environ["ALERT_TO"].split(",") if address.strip()]
    ses_client = boto3.client("sesv2")

    for record in event["Records"]:
        try:
            alarm = parse_alarm(record)
            subject, body = build_email(alarm, os.environ["RUNBOOK_TEXT"])
            message_id = send_email(ses_client, sender, recipients, subject, body)
            log("INFO", run_id, f"Sent an alert email through SES. Alarm={alarm['AlarmName']} "
                                f"State={alarm['NewStateValue']} From={sender} To={','.join(recipients)} "
                                f"MessageId={message_id}")
        except Exception as error:
            log("ERROR", run_id, f"Failed to send an alert email. Error={type(error).__name__}: {error}")
            raise
