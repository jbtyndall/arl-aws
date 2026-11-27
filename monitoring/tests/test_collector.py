"""Unit tests for the collector function."""

import io
import json
import os
import unittest
from unittest import mock

from loader import load_handler

collector = load_handler("collector")


class CollectorTests(unittest.TestCase):
    """Tests for target parsing, metric building, and the handler."""

    def test_parse_targets(self):
        """Name=host pairs become target dictionaries."""
        targets = collector.parse_targets("fw1=10.0.0.4, fw2=10.0.0.5", 443)
        self.assertEqual(targets, [{"name": "fw1", "host": "10.0.0.4", "port": 443},
                                   {"name": "fw2", "host": "10.0.0.5", "port": 443}])

    def test_parse_targets_rejects_bad_entry(self):
        """An entry without = raises ValueError."""
        with self.assertRaises(ValueError):
            collector.parse_targets("fw1", 443)

    def test_build_metric_data(self):
        """Reachable maps to 1 and unreachable to 0, per firewall dimension."""
        data = collector.build_metric_data([{"name": "fw1", "reachable": True}, {"name": "fw2", "reachable": False}])
        self.assertEqual([d["Value"] for d in data], [1.0, 0.0])
        self.assertEqual(data[1]["Dimensions"], [{"Name": "Firewall", "Value": "fw2"}])

    def _run_handler(self, probe_payload, function_error=False):
        """Run the handler with mocked AWS clients.

        Args:
            probe_payload: JSON-serializable object the fake probe returns.
            function_error: Whether the fake invoke response carries FunctionError.

        Returns:
            A tuple of (handler result, cloudwatch mock).
        """
        response = {"Payload": io.BytesIO(json.dumps(probe_payload).encode())}
        if function_error:
            response["FunctionError"] = "Unhandled"
        lambda_client, cloudwatch = mock.Mock(), mock.Mock()
        lambda_client.invoke.return_value = response
        env = {"TARGETS": "fw1=10.0.0.4", "PROBE_PORT": "443", "PROBE_FUNCTION_NAME": "probe"}
        clients = {"lambda": lambda_client, "cloudwatch": cloudwatch}
        with mock.patch.dict(os.environ, env), mock.patch.object(
                collector.boto3, "client", side_effect=lambda name: clients[name]):
            result = collector.handler({}, None)
        return result, cloudwatch

    def test_handler_publishes_metrics(self):
        """A good probe response publishes metrics and returns a summary."""
        result, cloudwatch = self._run_handler({"results": [{"name": "fw1", "reachable": True}]})
        self.assertEqual(result, {"fw1": True})
        cloudwatch.put_metric_data.assert_called_once()

    def test_handler_raises_when_probe_fails(self):
        """A probe FunctionError raises and publishes nothing."""
        with self.assertRaises(RuntimeError):
            self._run_handler({"errorMessage": "boom"}, function_error=True)


if __name__ == "__main__":
    unittest.main()
