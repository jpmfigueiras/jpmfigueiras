from datetime import date
import xml.etree.ElementTree as ET

import pytest

import build


@pytest.mark.parametrize(
    "start, today, expected",
    [
        (date(2023, 10, 1), date(2023, 10, 1), "0 months"),
        (date(2023, 10, 1), date(2023, 11, 1), "1 month"),
        (date(2023, 10, 1), date(2024, 10, 1), "1 year"),
        (date(2023, 10, 1), date(2026, 10, 21), "3 years"),
        (date(2023, 10, 1), date(2026, 12, 2), "3 years, 2 months"),
        (date(2023, 10, 15), date(2023, 11, 14), "0 months"),
    ],
)
def test_uptime(start, today, expected):
    assert build.uptime(start, today) == expected


def test_uptime_rejects_future_start():
    with pytest.raises(ValueError):
        build.uptime(date(2030, 1, 1), date(2026, 1, 1))


def test_no_token_means_no_request():
    assert build.fetch_contributions("someone", 2026, None) is None


def test_lines_with_and_without_count():
    with_count = dict(build.terminal_lines(date(2026, 5, 1), 123))
    without = dict(build.terminal_lines(date(2026, 5, 1), None))
    assert with_count["git log --since=2026-01-01 | wc -l"] == "123 contributions in 2026"
    assert without["git log --since=2026-01-01 | wc -l"] == "contributing in 2026"


@pytest.mark.parametrize("theme", [build.LIGHT, build.DARK])
def test_render_is_valid_svg_and_escapes_text(theme):
    svg = build.render(theme, [("echo <x>", "a & b")])
    root = ET.fromstring(svg)
    assert root.tag.endswith("svg")
    assert "&lt;x&gt;" in svg and "a &amp; b" in svg


def test_main_writes_both_themes(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "ASSETS", tmp_path)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    build.main(date(2026, 10, 21))
    assert (tmp_path / "header-light.svg").exists()
    assert (tmp_path / "header-dark.svg").exists()
