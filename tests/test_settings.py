import tempfile
import unittest
from pathlib import Path

from saberia.config.settings import Settings, SettingsError, load_settings, parse_env_file


class LoadSettingsTests(unittest.TestCase):
    def test_defaults_when_nothing_is_configured(self):
        settings = load_settings(env={}, env_file=None)
        self.assertEqual(settings, Settings())
        self.assertEqual(settings.db_host, "127.0.0.1")
        self.assertEqual(settings.db_port, 3306)
        self.assertEqual(settings.db_name, "saberiadb")
        self.assertEqual(settings.db_connect_timeout, 5)

    def test_environment_overrides_defaults(self):
        env = {
            "SABERIA_DB_HOST": "localhost",
            "SABERIA_DB_PORT": "3307",
            "SABERIA_DB_USER": "otro",
            "SABERIA_DB_PASSWORD": "clave",
            "SABERIA_DB_NAME": "saberia_test",
            "SABERIA_DB_CONNECT_TIMEOUT": "10",
        }
        settings = load_settings(env=env, env_file=None)
        self.assertEqual(
            (
                settings.db_host,
                settings.db_port,
                settings.db_user,
                settings.db_password,
                settings.db_name,
                settings.db_connect_timeout,
            ),
            ("localhost", 3307, "otro", "clave", "saberia_test", 10),
        )

    def test_variables_without_prefix_are_ignored(self):
        settings = load_settings(env={"DB_HOST": "ejemplo.com", "HOME": "/x"}, env_file=None)
        self.assertEqual(settings.db_host, "127.0.0.1")

    def test_env_file_is_read_and_environment_wins(self):
        with tempfile.TemporaryDirectory() as folder:
            env_file = Path(folder) / ".env"
            env_file.write_text(
                "SABERIA_DB_HOST=desde-archivo\nSABERIA_DB_USER=usuario-archivo\n",
                encoding="utf-8",
            )
            settings = load_settings(env={"SABERIA_DB_HOST": "desde-entorno"}, env_file=env_file)
        self.assertEqual(settings.db_host, "desde-entorno")
        self.assertEqual(settings.db_user, "usuario-archivo")

    def test_missing_env_file_is_not_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = load_settings(env={}, env_file=Path(folder) / "no-existe.env")
        self.assertEqual(settings, Settings())

    def test_invalid_port_is_reported(self):
        for bad in ("abc", "0", "70000", ""):
            with self.subTest(port=bad):
                with self.assertRaises(SettingsError) as ctx:
                    load_settings(env={"SABERIA_DB_PORT": bad}, env_file=None)
                self.assertIn("SABERIA_DB_PORT", str(ctx.exception))

    def test_all_errors_are_reported_together(self):
        env = {"SABERIA_DB_PORT": "x", "SABERIA_DB_NAME": "nombre-inválido", "SABERIA_DB_HOST": ""}
        with self.assertRaises(SettingsError) as ctx:
            load_settings(env=env, env_file=None)
        message = str(ctx.exception)
        for key in ("SABERIA_DB_PORT", "SABERIA_DB_NAME", "SABERIA_DB_HOST"):
            self.assertIn(key, message)

    def test_password_never_leaks_in_errors_or_repr(self):
        env = {"SABERIA_DB_PASSWORD": "secreto123", "SABERIA_DB_PORT": "mal"}
        with self.assertRaises(SettingsError) as ctx:
            load_settings(env=env, env_file=None)
        self.assertNotIn("secreto123", str(ctx.exception))
        valid = load_settings(env={"SABERIA_DB_PASSWORD": "secreto123"}, env_file=None)
        self.assertNotIn("secreto123", repr(valid))
        self.assertEqual(valid.db_password, "secreto123")


class ParseEnvFileTests(unittest.TestCase):
    def _parse(self, content):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text(content, encoding="utf-8")
            return parse_env_file(path)

    def test_comments_blank_lines_export_and_quotes(self):
        values = self._parse(
            "# comentario\n"
            "\n"
            "A=1\n"
            "export B=dos\n"
            'C="con # almohadilla y espacios"\n'
            "D='simple'\n"
            "E=valor # comentario al final\n"
            "línea sin igual\n"
        )
        self.assertEqual(
            values,
            {
                "A": "1",
                "B": "dos",
                "C": "con # almohadilla y espacios",
                "D": "simple",
                "E": "valor",
            },
        )

    def test_value_may_contain_equals_sign(self):
        self.assertEqual(self._parse("K=a=b=c\n"), {"K": "a=b=c"})


if __name__ == "__main__":
    unittest.main()
