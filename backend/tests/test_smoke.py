import asyncio

from app.main import app, health


def test_health_route_is_registered() -> None:
    assert app.url_path_for("health") == "/health"


def test_health_handler_returns_ok_status() -> None:
    assert asyncio.run(health()) == {"status": "ok"}
