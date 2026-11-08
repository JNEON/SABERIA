"""Punto de entrada de la aplicación."""

from __future__ import annotations


def run() -> None:
    """Abre la ventana de SABERIA.

    Flet se importa aquí (y no al cargar el módulo) para que el resto del
    proyecto pueda importarse y probarse sin tener Flet instalado.
    """
    try:
        import flet as ft
    except ImportError as exc:
        raise SystemExit('Falta Flet. Instala el proyecto con: pip install -e ".[dev]"') from exc

    from saberia.ui.app import main as app_main

    # Flet recientes exponen ``ft.run``; las anteriores usan ``ft.app``.
    runner = getattr(ft, "run", None)
    if callable(runner):
        runner(app_main)
    else:
        ft.app(target=app_main)


if __name__ == "__main__":
    run()
