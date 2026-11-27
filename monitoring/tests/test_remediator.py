"""Unit tests for the remediator function."""

import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from loader import load_handler

remediator = load_handler("remediator")

NOW = datetime(2026, 11, 27, 18, 0, tzinfo=timezone.utc)
OLD = NOW - timedelta(hours=5)
STATUS_RULE = {"firewall": "fw1", "instance_id": "i-1", "peer_instance_id": "i-2", "trigger": "instance-status"}
MGMT_RULE = {**STATUS_RULE, "trigger": "management"}


def instance(state="running", launch_time=OLD, eni_count=4):
    """Build a describe_instance style dictionary.

    Args:
        state: EC2 state name.
        launch_time: Launch time.
        eni_count: Number of attached ENIs.

    Returns:
        A dictionary with state, launch_time, and eni_count.
    """
    return {"state": state, "launch_time": launch_time, "eni_count": eni_count}


class DecideTests(unittest.TestCase):
    """Tests for the restart decision."""

    def test_active_instance_status_restarts(self):
        """Instance status on the active firewall restarts when enabled."""
        self.assertEqual(remediator.decide(STATUS_RULE, instance(), instance(eni_count=2), "enabled", NOW)["action"], "restart")

    def test_dry_run_does_not_restart(self):
        """Dry run reports would-restart."""
        self.assertEqual(remediator.decide(STATUS_RULE, instance(), instance(), "dry-run", NOW)["action"], "would-restart")

    def test_disabled_and_unknown_modes_skip(self):
        """Disabled and unrecognized modes skip."""
        for mode in ("disabled", "bogus"):
            self.assertEqual(remediator.decide(STATUS_RULE, instance(), instance(), mode, NOW)["action"], "skip")

    def test_management_on_active_skips(self):
        """A management alarm never restarts the active firewall."""
        self.assertEqual(remediator.decide(MGMT_RULE, instance(eni_count=4), instance(eni_count=2), "enabled", NOW)["action"], "skip")

    def test_management_on_standby_restarts(self):
        """A management alarm restarts the standby firewall."""
        self.assertEqual(remediator.decide(MGMT_RULE, instance(eni_count=2), instance(eni_count=4), "enabled", NOW)["action"], "restart")

    def test_recent_launch_skips(self):
        """An instance started 10 minutes ago is left alone."""
        recent = instance(launch_time=NOW - timedelta(minutes=10))
        self.assertEqual(remediator.decide(STATUS_RULE, recent, instance(), "enabled", NOW)["action"], "skip")

    def test_not_running_skips(self):
        """A stopped instance is left alone."""
        self.assertEqual(remediator.decide(STATUS_RULE, instance(state="stopped"), instance(), "enabled", NOW)["action"], "skip")

    def test_busy_peer_skips(self):
        """A peer that is stopping blocks the restart."""
        self.assertEqual(remediator.decide(STATUS_RULE, instance(), instance(state="stopping"), "enabled", NOW)["action"], "skip")


class HandlerTests(unittest.TestCase):
    """Tests for the handler using mocked AWS clients."""

    def _event(self, alarm_name="its-fw1-instance-status-failed", state="ALARM"):
        """Build an SNS event for an alarm.

        Args:
            alarm_name: Alarm name.
            state: New alarm state.

        Returns:
            An SNS Lambda event.
        """
        message = {"AlarmName": alarm_name, "NewStateValue": state}
        return {"Records": [{"Sns": {"Message": json.dumps(message)}}]}

    def _run(self, event, mode="enabled", fail_stop=False):
        """Run the handler with mocked clients.

        Args:
            event: SNS event.
            mode: Value returned by the SSM parameter.
            fail_stop: Make stop_instances raise.

        Returns:
            A tuple of (ec2 mock, ses mock).
        """
        ec2, ssm, ses = mock.Mock(), mock.Mock(), mock.Mock()
        description = {"Reservations": [{"Instances": [{"State": {"Name": "running"}, "LaunchTime": OLD,
                                                         "NetworkInterfaces": [{}, {}, {}, {}]}]}]}
        ec2.describe_instances.return_value = description
        if fail_stop:
            ec2.stop_instances.side_effect = RuntimeError("denied")
        ssm.get_parameter.return_value = {"Parameter": {"Value": mode}}
        ses.send_email.return_value = {"MessageId": "m1"}
        clients = {"ec2": ec2, "ssm": ssm, "sesv2": ses}
        env = {"RULES": json.dumps({"its-fw1-instance-status-failed": STATUS_RULE}), "ALERT_FROM": "a@x",
               "ALERT_TO": "b@x", "MODE_PARAMETER": "/p"}
        with mock.patch.dict(os.environ, env), mock.patch.object(remediator.boto3, "client", side_effect=lambda n: clients[n]):
            if fail_stop:
                with self.assertRaises(RuntimeError):
                    remediator.handler(event, None)
            else:
                remediator.handler(event, None)
        return ec2, ses

    def test_enabled_stops_and_starts(self):
        """Enabled mode stops, waits, starts, and emails."""
        ec2, ses = self._run(self._event())
        ec2.stop_instances.assert_called_once_with(InstanceIds=["i-1"])
        ec2.start_instances.assert_called_once_with(InstanceIds=["i-1"])
        self.assertIn("[AUTO-RESTART]", ses.send_email.call_args.kwargs["Content"]["Simple"]["Subject"]["Data"])

    def test_dry_run_changes_nothing_but_emails(self):
        """Dry run sends email and never calls stop or start."""
        ec2, ses = self._run(self._event(), mode="dry-run")
        ec2.stop_instances.assert_not_called()
        ses.send_email.assert_called_once()

    def test_ok_state_and_unknown_alarm_are_ignored(self):
        """OK notifications and unlisted alarms do nothing."""
        for event in (self._event(state="OK"), self._event(alarm_name="something-else")):
            ec2, ses = self._run(event)
            ec2.stop_instances.assert_not_called()
            ses.send_email.assert_not_called()

    def test_failed_restart_emails_and_raises(self):
        """A failed stop sends a failure email and re-raises."""
        ec2, ses = self._run(self._event(), fail_stop=True)
        ec2.start_instances.assert_not_called()
        self.assertIn("[AUTO-RESTART FAILED]", ses.send_email.call_args.kwargs["Content"]["Simple"]["Subject"]["Data"])


if __name__ == "__main__":
    unittest.main()
