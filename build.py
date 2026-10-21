"""Draw the terminal-style header for the GitHub profile README.

Writes assets/header-light.svg and assets/header-dark.svg.

The yearly contribution count comes from the GitHub GraphQL API when a
GITHUB_TOKEN is available (as it is inside GitHub Actions). Without a token
the line is still drawn, just without the number, so the script also runs
offline.
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from datetime import date
from html import escape
from pathlib import Path

USER = "jpmfigueiras"
CAREER_START = date(2023, 10, 1)  # first full-time developer role

ASSETS = Path(__file__).parent / "assets"


@dataclass(frozen=True)
class Theme:
    name: str
    background: str
    border: str
    bar: str
    text: str
    muted: str
    prompt: str
    accent: str


LIGHT = Theme("light", "#ffffff", "#d0d7de", "#f6f8fa", "#1f2328", "#59636e", "#1a7f37", "#0969da")
DARK = Theme("dark", "#0d1117", "#30363d", "#161b22", "#e6edf3", "#9198a1", "#3fb950", "#4493f8")


def uptime(start: date, today: date) -> str:
    """Human-readable time since `start`, e.g. '3 years, 1 month'."""
    if today < start:
        raise ValueError("today is before start")
    months = (today.year - start.year) * 12 + (today.month - start.month)
    if today.day < start.day:
        months -= 1
    years, months = divmod(months, 12)
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months or not years:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    return ", ".join(parts)


def fetch_contributions(user: str, year: int, token: str | None) -> int | None:
    """Total contributions for `year`, or None when no token / request fails."""
    if not token:
        return None
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar { totalContributions }
        }
      }
    }"""
    body = json.dumps({
        "query": query,
        "variables": {"login": user, "from": f"{year}-01-01T00:00:00Z", "to": f"{year}-12-31T23:59:59Z"},
    }).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.load(resp)
        return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    except Exception:
        return None


def terminal_lines(today: date, contributions: int | None) -> list[tuple[str, str]]:
    """(command, output) pairs shown in the terminal."""
    commits = f"{contributions} contributions in {today.year}" if contributions is not None else f"contributing in {today.year}"
    return [
        ("whoami", "Joel Figueiras · Full Stack Developer · Backend, Web & Application Security"),
        ("uptime", f"{uptime(CAREER_START, today)} shipping production code"),
        ("cat stack.txt", "Python · Flask · SQLAlchemy · MySQL · Redis · React · Azure"),
        ("cat focus.txt", "MSc Cybersecurity · secure-by-design web platforms"),
        (f"git log --since={today.year}-01-01 | wc -l", commits),
    ]


def render(theme: Theme, lines: list[tuple[str, str]]) -> str:
    width, line_h, top = 860, 22, 58
    height = top + len(lines) * 2 * line_h + 34
    font = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Joel Figueiras terminal header">',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{theme.background}" stroke="{theme.border}"/>',
        f'<path d="M0.5 10.5a10 10 0 0 1 10-10h{width - 21}a10 10 0 0 1 10 10v22H0.5z" fill="{theme.bar}" stroke="{theme.border}"/>',
        '<circle cx="22" cy="17" r="6" fill="#ff5f57"/><circle cx="42" cy="17" r="6" fill="#febc2e"/><circle cx="62" cy="17" r="6" fill="#28c840"/>',
        f'<text x="{width / 2}" y="21" text-anchor="middle" font-family="{font}" font-size="12" fill="{theme.muted}">joel@braga: ~</text>',
        f'<g font-family="{font}" font-size="14">',
    ]
    y = top
    for command, output in lines:
        out.append(
            f'<text x="24" y="{y}"><tspan fill="{theme.prompt}">joel@braga</tspan>'
            f'<tspan fill="{theme.muted}">:~$ </tspan><tspan fill="{theme.text}">{escape(command)}</tspan></text>'
        )
        y += line_h
        out.append(f'<text x="24" y="{y}" fill="{theme.accent}">{escape(output)}</text>')
        y += line_h
    out.append(
        f'<text x="24" y="{y}"><tspan fill="{theme.prompt}">joel@braga</tspan><tspan fill="{theme.muted}">:~$ </tspan>'
        f'<tspan fill="{theme.text}">▍<animate attributeName="opacity" values="1;0;1" dur="1.2s" repeatCount="indefinite"/></tspan></text>'
    )
    out += ["</g>", "</svg>"]
    return "\n".join(out) + "\n"


def main(today: date | None = None) -> None:
    today = today or date.today()
    contributions = fetch_contributions(USER, today.year, os.environ.get("GITHUB_TOKEN"))
    lines = terminal_lines(today, contributions)
    ASSETS.mkdir(exist_ok=True)
    for theme in (LIGHT, DARK):
        (ASSETS / f"header-{theme.name}.svg").write_text(render(theme, lines), encoding="utf-8")


if __name__ == "__main__":
    main()
