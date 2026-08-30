import os
import unittest
from pathlib import Path
from unittest.mock import patch

from services.dispositivos.runtime import entrypoint


class RuntimeEntrypointTests(unittest.TestCase):
    def test_web_waits_for_database_and_only_runs_gunicorn(self):
        with (
            patch.object(entrypoint, "wait_for_database") as wait_for_database,
            patch.object(entrypoint.subprocess, "run") as run_process,
        ):
            entrypoint.run_web()

        wait_for_database.assert_called_once_with()
        run_process.assert_called_once_with(entrypoint.gunicorn_command(), check=True)

    def test_migrate_uses_only_the_dispositivos_migration_target(self):
        with (
            patch.object(entrypoint, "wait_for_database") as wait_for_database,
            patch.object(entrypoint, "execute_django_command") as execute_command,
        ):
            entrypoint.run_migrations()

        wait_for_database.assert_called_once_with()
        execute_command.assert_called_once_with(
            ["migrate", "dispositivos", "--noinput"]
        )

    def test_main_rejects_unknown_roles(self):
        with self.assertRaisesRegex(ValueError, "no soportado"):
            entrypoint.main(["worker"])

    def test_gunicorn_command_uses_the_runtime_wsgi_module(self):
        previous_port = os.environ.get("DISPOSITIVOS_WEB_PORT")
        self.addCleanup(self._restore_port, previous_port)
        os.environ["DISPOSITIVOS_WEB_PORT"] = "8010"

        command = entrypoint.gunicorn_command()

        self.assertIn("services.dispositivos.runtime.wsgi:application", command)
        self.assertIn("0.0.0.0:8010", command)

    def test_selective_compose_keeps_web_and_migrations_in_distinct_roles(self):
        compose_path = next(
            parent / "compose.dispositivos.yml"
            for parent in Path(__file__).resolve().parents
            if (parent / "compose.dispositivos.yml").is_file()
        )
        compose = compose_path.read_text(encoding="utf-8")

        self.assertIn(
            '"services.dispositivos.runtime.entrypoint", "web"',
            compose,
        )
        self.assertIn(
            '"services.dispositivos.runtime.entrypoint", "migrate"',
            compose,
        )
        self.assertIn("profiles:", compose)

    @staticmethod
    def _restore_port(previous_port):
        if previous_port is None:
            os.environ.pop("DISPOSITIVOS_WEB_PORT", None)
            return
        os.environ["DISPOSITIVOS_WEB_PORT"] = previous_port
