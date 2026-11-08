"""Pruebas de humo de la ventana contra un SUSTITUTO de Flet.

No validan Flet real (eso se comprueba ejecutando la aplicación); solo que
nuestra lógica de la ventana y del punto de entrada se comporta como se espera.
"""

import importlib
import sys
import types
import unittest
from unittest.mock import patch

from saberia.config.settings import Settings, SettingsError
from saberia.persistence.database import ConnectionResult


def make_flet_stub(*, with_run=True):
    stub = types.ModuleType("flet")

    class Control:
        def __init__(self, *args, **kwargs):
            self.value = args[0] if args and isinstance(args[0], str) else kwargs.get("value")
            self.on_click = kwargs.get("on_click")

    class Text(Control):
        pass

    class Button(Control):
        pass

    class FontWeight:
        BOLD = "bold"

    class Page:
        pass

    stub.Control, stub.Text, stub.Button, stub.FontWeight, stub.Page = (
        Control,
        Text,
        Button,
        FontWeight,
        Page,
    )
    stub.calls = []
    if with_run:
        stub.run = lambda target: stub.calls.append(("run", target))
    stub.app = lambda target: stub.calls.append(("app", target))
    return stub


class FakePage:
    def __init__(self):
        self.title = None
        self.controls = []
        self.updates = 0

    def add(self, *controls):
        self.controls.extend(controls)

    def update(self):
        self.updates += 1


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.stub = make_flet_stub()
        patcher = patch.dict(sys.modules, {"flet": self.stub})
        patcher.start()
        self.addCleanup(patcher.stop)
        sys.modules.pop("saberia.ui.app", None)
        self.addCleanup(lambda: sys.modules.pop("saberia.ui.app", None))
        self.app = importlib.import_module("saberia.ui.app")

    def _texts(self, page):
        return [c.value for c in page.controls if isinstance(c, self.stub.Text)]

    def test_window_shows_connection_result(self):
        result = ConnectionResult(ok=True, message="Conexión correcta. Servidor MySQL 8.0.36.")
        with (
            patch.object(self.app, "load_settings", return_value=Settings()),
            patch.object(self.app, "check_connection", return_value=result) as check,
        ):
            page = FakePage()
            self.app.main(page)
        self.assertEqual(page.title, "SABERIA")
        self.assertIn("SABERIA", self._texts(page))
        self.assertIn(result.message, self._texts(page))
        check.assert_called_once()

    def test_window_shows_configuration_errors(self):
        with patch.object(self.app, "load_settings", side_effect=SettingsError("Config rota")):
            page = FakePage()
            self.app.main(page)
        self.assertIn("Config rota", self._texts(page))

    def test_button_repeats_the_check(self):
        result = ConnectionResult(ok=False, message="No se pudo conectar")
        with (
            patch.object(self.app, "load_settings", return_value=Settings()),
            patch.object(self.app, "check_connection", return_value=result) as check,
        ):
            page = FakePage()
            self.app.main(page)
            button = next(c for c in page.controls if isinstance(c, self.stub.Button))
            button.on_click(None)
        self.assertEqual(check.call_count, 2)


class EntryPointTests(unittest.TestCase):
    def _run_with(self, stub):
        with patch.dict(sys.modules, {"flet": stub}):
            sys.modules.pop("saberia.ui.app", None)
            try:
                importlib.import_module("saberia.main").run()
            finally:
                sys.modules.pop("saberia.ui.app", None)

    def test_uses_ft_run_when_available(self):
        stub = make_flet_stub(with_run=True)
        self._run_with(stub)
        self.assertEqual([name for name, _ in stub.calls], ["run"])

    def test_missing_flet_gives_a_clear_message(self):
        with patch.dict(sys.modules, {"flet": None}):
            with self.assertRaises(SystemExit) as ctx:
                importlib.import_module("saberia.main").run()
        self.assertIn("pip install", str(ctx.exception))

    def test_falls_back_to_ft_app(self):
        stub = make_flet_stub(with_run=False)
        self._run_with(stub)
        self.assertEqual([name for name, _ in stub.calls], ["app"])


if __name__ == "__main__":
    unittest.main()
