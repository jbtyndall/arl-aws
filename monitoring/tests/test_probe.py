"""Unit tests for the probe function."""

import socket
import threading
import unittest

from loader import load_handler

probe = load_handler("probe")


class ProbeTests(unittest.TestCase):
    """Tests for check_tcp and handler using a local listener."""

    def setUp(self):
        """Start a throwaway TCP listener on a free local port."""
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(5)
        self.port = self.listener.getsockname()[1]
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def tearDown(self):
        """Close the listener."""
        self.listener.close()

    def _accept_loop(self):
        """Accept and immediately close connections until the listener is closed."""
        while True:
            try:
                connection, _ = self.listener.accept()
                connection.close()
            except OSError:
                return

    def test_open_port_is_reachable(self):
        """An open port reports reachable."""
        self.assertTrue(probe.check_tcp("127.0.0.1", self.port, 2)["reachable"])

    def test_closed_port_is_not_reachable(self):
        """A closed port reports not reachable with a detail message."""
        self.listener.close()
        outcome = probe.check_tcp("127.0.0.1", self.port, 2)
        self.assertFalse(outcome["reachable"])
        self.assertTrue(outcome["detail"])

    def test_handler_returns_one_result_per_target(self):
        """The handler echoes target fields and adds the outcome."""
        event = {"targets": [{"name": "fw1", "host": "127.0.0.1", "port": self.port}]}
        result = probe.handler(event, None)["results"][0]
        self.assertEqual(result["name"], "fw1")
        self.assertTrue(result["reachable"])


if __name__ == "__main__":
    unittest.main()
