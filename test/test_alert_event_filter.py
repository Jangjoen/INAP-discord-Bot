import unittest

from services.zabbix_service import (
    get_latest_zabbix_event_id,
    is_unresolved_problem_event,
)


class UnresolvedProblemEventTests(unittest.TestCase):
    def test_sends_open_problem_without_recovery_event(self):
        self.assertTrue(
            is_unresolved_problem_event({"value": 1, "r_eventid": 0})
        )

    def test_skips_problem_with_recovery_event(self):
        self.assertFalse(
            is_unresolved_problem_event({"value": 1, "r_eventid": 12345})
        )

    def test_skips_recovery_event(self):
        self.assertFalse(
            is_unresolved_problem_event({"value": 0, "r_eventid": 0})
        )

    def test_startup_baseline_uses_latest_event_including_recovery(self):
        self.assertEqual(
            get_latest_zabbix_event_id([
                {"eventid": 120, "value": 1},
                {"eventid": 121, "value": 0},
            ]),
            121,
        )

    def test_empty_startup_baseline_is_zero(self):
        self.assertEqual(get_latest_zabbix_event_id([]), 0)


if __name__ == "__main__":
    unittest.main()