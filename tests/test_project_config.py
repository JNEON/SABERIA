import importlib
import re
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    tomllib = None

from saberia import __version__
from saberia.config.settings import ENV_PREFIX, load_settings, parse_env_file

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(tomllib is None, "tomllib requiere Python 3.11+")
class PyprojectTests(unittest.TestCase):
    def setUp(self):
        with (ROOT / "pyproject.toml").open("rb") as handle:
            self.data = tomllib.load(handle)

    def test_required_dependencies_are_declared_with_upper_bounds(self):
        dependencies = self.data["project"]["dependencies"]
        names = {re.match(r"[A-Za-z0-9_.-]+", dep).group(0).lower() for dep in dependencies}
        self.assertTrue({"flet", "sqlalchemy", "alembic", "pymysql"} <= names)
        for dep in dependencies:
            with self.subTest(dependency=dep):
                self.assertIn(">=", dep)
                self.assertIn("<", dep)

    def test_pymysql_includes_rsa_extra_for_mysql8_auth(self):
        dependencies = self.data["project"]["dependencies"]
        self.assertTrue(any(dep.lower().startswith("pymysql[rsa]") for dep in dependencies))

    def test_python_version_entry_point_and_version(self):
        project = self.data["project"]
        self.assertEqual(project["requires-python"], ">=3.10")
        self.assertEqual(project["scripts"]["saberia"], "saberia.main:run")
        self.assertEqual(project["version"], __version__)


class EnvExampleTests(unittest.TestCase):
    def test_example_is_valid_and_complete(self):
        example = ROOT / ".env.example"
        keys = set(parse_env_file(example))
        self.assertEqual(
            keys,
            {
                ENV_PREFIX + name
                for name in (
                    "DB_HOST",
                    "DB_PORT",
                    "DB_USER",
                    "DB_PASSWORD",
                    "DB_NAME",
                    "DB_CONNECT_TIMEOUT",
                )
            },
        )
        load_settings(env={}, env_file=example)  # no debe lanzar


class StructureTests(unittest.TestCase):
    def test_planned_packages_are_importable_without_flet_or_sqlalchemy(self):
        for name in (
            "saberia",
            "saberia.config",
            "saberia.domain",
            "saberia.engine",
            "saberia.engine.rules",
            "saberia.engine.modes",
            "saberia.analytics",
            "saberia.packages",
            "saberia.persistence",
            "saberia.persistence.repositories",
            "saberia.persistence.database",
            "saberia.ui",
            "saberia.ui.views",
            "saberia.ui.components",
            "saberia.main",
        ):
            with self.subTest(module=name):
                importlib.import_module(name)


if __name__ == "__main__":
    unittest.main()
