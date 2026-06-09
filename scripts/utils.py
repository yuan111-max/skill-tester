"""Shared utility functions for skill-tester."""

from __future__ import annotations

import re


def strip_frontmatter(content: str) -> str:
    """Return *content* with YAML frontmatter (--- ... ---) removed.

    Returns the raw content unchanged if no frontmatter delimiters are found.
    """
    m = re.match(r"^---\n.*?\n(?:---|\.\.\.)\n(.*)", content, re.DOTALL)
    return m.group(1) if m else content


# Regex to strip ANSI escape codes for visible-length calculations
_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def visible_length(text: str) -> int:
    """Return the visible length of *text* with ANSI escape codes stripped."""
    return len(_ANSI_RE.sub("", text))
