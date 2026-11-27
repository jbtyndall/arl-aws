"""Unit tests for the notifier function."""

import json
import os
import unittest
from unittest import mock

from loader import load_handler

notifier = load_handler("notifier")

ALARM = {"AlarmName": "its-fw2-management-unreachable", "NewStateValue": "ALARM", "OldStateValue": "OK",
         "AlarmDescription": "FW2 is down. Restart it.", "NewStateReason": "Threshold crossed",
         "StateChangeTime": "2026-11-27T15:00:00.000+0000", "AWSAccountId": "890884507059",
         "Region": "US GovCloud (US-West)"}


def sns_event(message):
    """Wrap a message in an SNS Lambda event.

    Args:
        message: Object to serialize as the SNS message.

    Returns:
        An event dictionary with one record.
    """
    return {"Records": [{"Sns": {"Message": json.dumps(message)}}]}


class NotifierTests(unittest.TestCase):
    """Tests for parsing, formatting, and sending."""

    def test_parse_alarm_rejects_other_messages(self):
        """A non-alarm SNS message raises ValueError."""
        with self.assertRaises(ValueError):
            notifier.parse_alarm(sns_event({"hello": "world"})["Records"][0])

    def test_build_email_alarm(self):
        """Subject carries state and name. Body carries description and runbook."""
        subject, body = notifier.build_email(ALARM, "see runbook")
        self.assertEqual(subject, "[ALARM] its-fw2-management-unreachable")
        self.assertIn("FW2 is down. Restart it.", body)
        self.assertIn("see runbook", body)

    def test_build_email_ok_state(self):
        """An OK transition is labeled OK."""
        subject, _ = notifier.build_email({**ALARM, "NewStateValue": "OK"}, "r")
        self.assertTrue(subject.startswith("[OK]"))

    def test_build_email_strips_newlines_from_subject(self):
        """Newlines in the alarm name cannot break the subject header."""
        subject, _ = notifier.build_email({**ALARM, "AlarmName": "a\nb"}, "r")
        self.assertNotIn("\n", subject)

    def _env(self):
        """Return the environment variables the handler needs."""
        return {"ALERT_FROM": "aws@arl.psu.edu", "ALERT_TO": "a@arl.psu.edu, b@arl.psu.edu", "RUNBOOK_TEXT": "rb"}

    def test_handler_sends_to_all_recipients(self):
        """The handler calls SES once with every recipient."""
        ses = mock.Mock()
        ses.send_email.return_value = {"MessageId": "abc"}
        with mock.patch.dict(os.environ, self._env()), mock.patch.object(notifier.boto3, "client", return_value=ses):
            notifier.handler(sns_event(ALARM), None)
        sent = ses.send_email.call_args.kwargs
        self.assertEqual(sent["Destination"]["ToAddresses"], ["a@arl.psu.edu", "b@arl.psu.edu"])

    def test_handler_raises_on_ses_failure(self):
        """An SES error propagates so Lambda retries."""
        ses = mock.Mock()
        ses.send_email.side_effect = RuntimeError("MessageRejected")
        with mock.patch.dict(os.environ, self._env()), mock.patch.object(notifier.boto3, "client", return_value=ses):
            with self.assertRaises(RuntimeError):
                notifier.handler(sns_event(ALARM), None)


if __name__ == "__main__":
    unittest.main()
