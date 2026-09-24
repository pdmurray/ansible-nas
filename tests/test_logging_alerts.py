"""Regression checks for the provisioned Docker log dashboard and alert."""

import json
import re
import unittest
from pathlib import Path

import jinja2
import yaml


ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / "roles" / "logging"
DEFAULTS = yaml.safe_load((ROLE / "defaults" / "main.yml").read_text())


def render(template_name, **overrides):
    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(ROLE / "templates"),
        undefined=jinja2.StrictUndefined,
    )
    environment.filters["bool"] = bool
    environment.filters["regex_escape"] = re.escape
    environment.filters["to_json"] = json.dumps
    return environment.get_template(template_name).render(**(DEFAULTS | overrides))


def logql_quoted_value(expression, prefix):
    match = re.search(re.escape(prefix) + r'("(?:\\.|[^"\\])*")', expression)
    if match is None:
        raise AssertionError(f"Missing quoted value after {prefix!r}: {expression}")
    return json.loads(match.group(1))


class LoggingAlertTests(unittest.TestCase):
    def test_default_pattern_matches_severity_not_incidental_words(self):
        pattern = re.compile(DEFAULTS["logging_error_pattern"])
        matching = [
            'level=error msg="failed"',
            '{"level":"error","msg":"failed"}',
            "severity=critical service failed",
            "[Error] request failed",
            "ERROR: request failed",
            "2026-09-24T20:30:00Z FATAL process exited",
            "error: request failed",
            "java.lang.NullPointerException: request failed",
        ]
        not_matching = [
            'level=info msg="App runner exited without error"',
            'level=info msg="No exception occurred"',
            'level=info query="sum(count_over_time({source=\\"docker\\"} |~ \\"(?i)(error|fatal|panic)\\")"',
            "logger=ngalert.sender.router rule_uid=docker-error-logs level=info",
            "level=errorCode msg=retrying",
        ]
        for line in matching:
            with self.subTest(line=line):
                self.assertIsNotNone(pattern.search(line))
        for line in not_matching:
            with self.subTest(line=line):
                self.assertIsNone(pattern.search(line))

    def test_alert_excludes_stack_and_preserves_other_containers(self):
        config = yaml.safe_load(
            render(
                "grafana-alert-rules.yml.j2",
                logging_alert_excluded_containers=["noisy.app"],
            )
        )
        expression = config["groups"][0]["rules"][0]["data"][0]["model"]["expr"]
        excluded = re.compile(logql_quoted_value(expression, "container!~"))
        for name in ("logging-grafana", "logging-loki", "logging-alloy", "noisy.app"):
            self.assertIsNotNone(excluded.fullmatch(name))
        for name in ("radarr", "logging-grafana-other", "noisyXapp"):
            self.assertIsNone(excluded.fullmatch(name))
        self.assertEqual(logql_quoted_value(expression, "|~ "), DEFAULTS["logging_error_pattern"])

    def test_dashboard_uses_valid_json_and_no_forced_refresh(self):
        dashboard = json.loads(render("docker-logs-dashboard.json.j2"))
        self.assertNotIn("refresh", dashboard)
        graph_expression = dashboard["panels"][0]["targets"][0]["expr"]
        self.assertEqual(logql_quoted_value(graph_expression, "|~ "), DEFAULTS["logging_error_pattern"])
        logs_expression = dashboard["panels"][1]["targets"][0]["expr"]
        self.assertIn("|~ `${search:raw}`", logs_expression)
        search = dashboard["templating"]["list"][1]
        self.assertEqual(search["current"]["value"], DEFAULTS["logging_error_pattern"])
        self.assertEqual(search["query"], DEFAULTS["logging_error_pattern"])

    def test_custom_pattern_is_escaped_in_both_provisioning_files(self):
        custom_pattern = 'level="error"|\\[Error\\]'
        dashboard = json.loads(
            render("docker-logs-dashboard.json.j2", logging_error_pattern=custom_pattern)
        )
        alert = yaml.safe_load(
            render("grafana-alert-rules.yml.j2", logging_error_pattern=custom_pattern)
        )
        dashboard_query = dashboard["panels"][0]["targets"][0]["expr"]
        alert_query = alert["groups"][0]["rules"][0]["data"][0]["model"]["expr"]
        self.assertEqual(logql_quoted_value(dashboard_query, "|~ "), custom_pattern)
        self.assertEqual(logql_quoted_value(alert_query, "|~ "), custom_pattern)

    def test_disabled_alert_removes_provisioned_rule(self):
        config = yaml.safe_load(
            render("grafana-alert-rules.yml.j2", logging_error_alert_enabled=False)
        )
        self.assertEqual(config["deleteRules"], [{"orgId": 1, "uid": "docker-error-logs"}])


if __name__ == "__main__":
    unittest.main()
