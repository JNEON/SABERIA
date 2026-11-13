import importlib.util
import os
import unittest

from saberia.config.settings import Settings, load_settings
from saberia.persistence.database import (
    MIN_MARIADB_VERSION,
    MIN_MYSQL_VERSION,
    ErrorKind,
    build_url,
    check_connection,
    parse_mysql_version,
)

SETTINGS = Settings(db_password="clave-super-secreta")


class FakeDriverError(Exception):
    """Imita las excepciones de SQLAlchemy/PyMySQL: el código va en ``orig.args[0]``."""

    def __init__(self, code):
        super().__init__(f"error {code} con clave-super-secreta")
        self.orig = type("Orig", (), {"args": (code, "mensaje del servidor")})()


def fetching(version):
    return lambda _settings: version


def failing(exc):
    def _fetch(_settings):
        raise exc

    return _fetch


class ParseVersionTests(unittest.TestCase):
    def test_known_formats(self):
        self.assertEqual(parse_mysql_version("8.0.36"), (8, 0, 36))
        self.assertEqual(parse_mysql_version("8.0.36-0ubuntu0.22.04.1"), (8, 0, 36))
        self.assertEqual(parse_mysql_version("8.4.0"), (8, 4, 0))
        self.assertEqual(parse_mysql_version("10.11.6-MariaDB"), (10, 11, 6))

    def test_unparseable(self):
        self.assertIsNone(parse_mysql_version("desconocida"))
        self.assertIsNone(parse_mysql_version(""))

    def test_minimum_mariadb_version_constant(self):
        self.assertEqual(MIN_MARIADB_VERSION, (10, 2, 1))
        self.assertEqual(MIN_MYSQL_VERSION, (8, 0, 16))


class CheckConnectionVersionTests(unittest.TestCase):
    def test_supported_mariadb_versions(self):
        for version in (
            "10.2.1-MariaDB",
            "10.4.32-MariaDB",
            "10.11.6-MariaDB",
        ):
            with self.subTest(version=version):
                result = check_connection(SETTINGS, fetching(version))
                self.assertTrue(result.ok)
                self.assertEqual(result.server_version, version)
                self.assertIsNone(result.error_kind)
                self.assertIn("MariaDB", result.message)

    def test_old_mariadb_versions_are_rejected(self):
        for version in ("10.2.0-MariaDB", "10.1.48-MariaDB"):
            with self.subTest(version=version):
                result = check_connection(SETTINGS, fetching(version))
                self.assertFalse(result.ok)
                self.assertEqual(
                    result.error_kind,
                    ErrorKind.UNSUPPORTED_SERVER,
                )

    def test_unparseable_version(self):
        result = check_connection(SETTINGS, fetching("???"))
        self.assertFalse(result.ok)
        self.assertEqual(result.error_kind, ErrorKind.UNSUPPORTED_SERVER)


class CheckConnectionFailureTests(unittest.TestCase):
    def test_error_codes_are_classified(self):
        cases = {
            1045: ErrorKind.AUTH_FAILED,
            1044: ErrorKind.AUTH_FAILED,
            1049: ErrorKind.UNKNOWN_DATABASE,
            2003: ErrorKind.SERVER_UNREACHABLE,
            2002: ErrorKind.SERVER_UNREACHABLE,
        }
        for code, kind in cases.items():
            with self.subTest(code=code):
                result = check_connection(SETTINGS, failing(FakeDriverError(code)))
                self.assertFalse(result.ok)
                self.assertEqual(result.error_kind, kind)

    def test_os_errors_mean_unreachable(self):
        result = check_connection(SETTINGS, failing(ConnectionRefusedError()))
        self.assertEqual(result.error_kind, ErrorKind.SERVER_UNREACHABLE)
        self.assertIn("127.0.0.1:3306", result.message)

    def test_missing_driver(self):
        result = check_connection(SETTINGS, failing(ModuleNotFoundError("x", name="pymysql")))
        self.assertEqual(result.error_kind, ErrorKind.DRIVER_MISSING)
        self.assertIn("pymysql", result.message)

    def test_unexpected_error_never_raises_and_never_leaks_password(self):
        result = check_connection(SETTINGS, failing(RuntimeError("clave-super-secreta")))
        self.assertFalse(result.ok)
        self.assertEqual(result.error_kind, ErrorKind.UNKNOWN)
        for code in (1045, 1049, 2003, None):
            with self.subTest(code=code):
                exc = FakeDriverError(code) if code else RuntimeError("clave-super-secreta")
                self.assertNotIn(
                    "clave-super-secreta", check_connection(SETTINGS, failing(exc)).message
                )


@unittest.skipUnless(importlib.util.find_spec("sqlalchemy"), "SQLAlchemy no está instalado")
class BuildUrlTests(unittest.TestCase):
    def test_url_uses_pymysql_and_utf8mb4_and_hides_password(self):
        rendered = build_url(SETTINGS).render_as_string(hide_password=True)
        self.assertEqual(
            rendered, "mysql+pymysql://saberia_app:***@127.0.0.1:3306/saberiadb?charset=utf8mb4"
        )

    def test_special_characters_in_password_are_preserved(self):
        url = build_url(Settings(db_password="p@ss:w/rd#1"))
        self.assertEqual(url.password, "p@ss:w/rd#1")
        self.assertNotIn("p@ss:w/rd#1", url.render_as_string(hide_password=False))  # escapada


@unittest.skipUnless(
    os.environ.get("SABERIA_TEST_MYSQL") == "1",
    "Prueba de integración: exporta SABERIA_TEST_MYSQL=1 con un MySQL local configurado",
)
class RealMySqlIntegrationTests(unittest.TestCase):
    def test_real_connection(self):
        result = check_connection(load_settings())
        self.assertTrue(result.ok, result.message)


if __name__ == "__main__":
    unittest.main()
