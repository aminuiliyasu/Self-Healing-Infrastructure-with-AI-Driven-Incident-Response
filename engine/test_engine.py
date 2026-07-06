import tempfile
import unittest
from pathlib import Path

from incident_log import IncidentLog, summarize_log
from rules import evaluate


class RulesTest(unittest.TestCase):
    def test_target_down(self):
        incidents = evaluate(
            error_rate_per_s=0.0,
            up=0.0,
            latency_p95_s=0.1,
            error_threshold=0.05,
            latency_threshold_s=0.5,
        )
        self.assertEqual(len(incidents), 1)
        self.assertEqual(incidents[0]["type"], "target_down")
        self.assertEqual(incidents[0]["remediation"], "restart_deployment")

    def test_overload_scales(self):
        incidents = evaluate(
            error_rate_per_s=0.2,
            up=1.0,
            latency_p95_s=0.9,
            error_threshold=0.05,
            latency_threshold_s=0.5,
        )
        self.assertEqual(incidents[0]["root_cause"], "overload_high_errors_and_latency")
        self.assertEqual(incidents[0]["remediation"], "scale_deployment")

    def test_errors_without_latency_spike(self):
        incidents = evaluate(
            error_rate_per_s=0.2,
            up=1.0,
            latency_p95_s=0.1,
            error_threshold=0.05,
            latency_threshold_s=0.5,
        )
        self.assertEqual(incidents[0]["root_cause"], "elevated_errors_low_latency")
        self.assertEqual(incidents[0]["remediation"], "investigate_logs")

    def test_latency_only(self):
        incidents = evaluate(
            error_rate_per_s=0.0,
            up=1.0,
            latency_p95_s=0.9,
            error_threshold=0.05,
            latency_threshold_s=0.5,
        )
        self.assertEqual(incidents[0]["type"], "high_latency")
        self.assertEqual(incidents[0]["remediation"], "scale_deployment")

    def test_all_healthy(self):
        incidents = evaluate(
            error_rate_per_s=0.0,
            up=1.0,
            latency_p95_s=0.1,
            error_threshold=0.05,
            latency_threshold_s=0.5,
        )
        self.assertEqual(incidents, [])


class IncidentLogTest(unittest.TestCase):
    def test_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "incidents.jsonl"
            log = IncidentLog(path)
            log.record_incident({"type": "high_error_rate"})
            log.record_incident({"type": "target_down"})
            log.record_remediation(
                incident_type="high_error_rate",
                action="scale_deployment",
                started_at="2026-01-01T00:00:00+00:00",
                finished_at="2026-01-01T00:00:05+00:00",
                success=True,
                detail={},
            )
            log.record_resolution(
                incident_type="high_error_rate",
                opened_at="2026-01-01T00:00:00+00:00",
                resolved_at="2026-01-01T00:02:00+00:00",
                duration_seconds=120.0,
            )

            summary = summarize_log(path)
            self.assertEqual(summary["incidents"], 2)
            self.assertEqual(summary["auto_resolved"], 1)
            self.assertEqual(summary["auto_resolution_pct"], 50.0)
            self.assertEqual(summary["resolved"], 1)
            self.assertEqual(summary["mttr_seconds"], 120.0)

    def test_empty_log(self):
        summary = summarize_log(Path("/nonexistent/incidents.jsonl"))
        self.assertEqual(summary["incidents"], 0)
        self.assertIsNone(summary["mttr_seconds"])


if __name__ == "__main__":
    unittest.main()
