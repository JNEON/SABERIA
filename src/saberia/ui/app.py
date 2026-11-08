"""Ventana mínima de SABERIA: muestra el estado de la conexión con MySQL.

Es solo una pantalla de diagnóstico; las vistas del juego llegarán en fases posteriores.
"""

from __future__ import annotations

import flet as ft

from saberia import __version__
from saberia.config.settings import SettingsError, load_settings
from saberia.persistence.database import check_connection

CHECKING_TEXT = "Comprobando conexión con MySQL…"


def _make_button(label: str, on_click) -> ft.Control:
    # En Flet recientes el botón se llama ``Button``; antes, ``ElevatedButton``.
    button_class = getattr(ft, "Button", None) or ft.ElevatedButton
    return button_class(label, on_click=on_click)


def main(page: ft.Page) -> None:
    page.title = "SABERIA"
    status = ft.Text(CHECKING_TEXT)

    def run_check(_event=None) -> None:
        status.value = CHECKING_TEXT
        page.update()
        try:
            settings = load_settings()
        except SettingsError as error:
            status.value = str(error)
        else:
            status.value = check_connection(settings).message
        page.update()

    page.add(
        ft.Text("SABERIA", size=32, weight=ft.FontWeight.BOLD),
        ft.Text("Videojuego educativo familiar de preguntas y aprendizaje"),
        ft.Text(f"Versión {__version__} · entorno de desarrollo"),
        status,
        _make_button("Comprobar conexión", run_check),
    )
    run_check()
