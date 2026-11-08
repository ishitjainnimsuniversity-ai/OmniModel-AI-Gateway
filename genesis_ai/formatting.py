"""Text formatting for the 320x240 TFT: markdown stripping, ASCII transliteration, wrapping, pagination."""
from __future__ import annotations

import re
import textwrap
import unicodedata
from typing import List

_TRANSLIT = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-",
    "\u2026": "...", "\u2022": "*", "\u00a0": " ", "\u2192": "->", "\u2190": "<-", "\u00d7": "x",
    "\u00f7": "/", "\u2264": "<=", "\u2265": ">=", "\u2260": "!=", "\u00b0": " deg", "\u2248": "~",
    "\u03c0": "pi", "\u221a": "sqrt", "\u00b2": "^2", "\u00b3": "^3",
}


def strip_markdown(text: str) -> str:
    t = text.replace("\r\n", "\n")
    t = re.sub(r"```[a-zA-Z0-9_+-]*\n?", "", t)          # code fences (keep the code)
    t = re.sub(r"`([^`]*)`", r"\1", t)                      # inline code
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)              # images
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", t)   # links -> text (url)
    t = re.sub(r"^\s{0,3}#{1,6}\s*", "", t, flags=re.M)     # headings
    t = re.sub(r"(\*\*|__)(.*?)\1", r"\2", t)               # bold
    t = re.sub(r"(?<!\w)[*_]([^*_\n]+)[*_](?!\w)", r"\1", t)  # italics
    t = re.sub(r"^\s*[-*+]\s+", "- ", t, flags=re.M)        # bullets
    t = re.sub(r"^\s*>\s?", "", t, flags=re.M)              # quotes
    t = re.sub(r"^\s*\|?[\s:\-|]+\|\s*$", "", t, flags=re.M)  # table separator rows
    t = t.replace("|", " ")
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def to_ascii(text: str) -> str:
    out = []
    for ch in text:
        if ch in _TRANSLIT:
            out.append(_TRANSLIT[ch])
        elif ord(ch) < 128:
            out.append(ch)
        else:
            norm = unicodedata.normalize("NFKD", ch).encode("ascii", "ignore").decode()
            out.append(norm if norm else "?")
    return "".join(out)


def device_text(text: str) -> str:
    return to_ascii(strip_markdown(text))


def wrap_lines(text: str, cols: int) -> List[str]:
    lines: List[str] = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=cols, break_long_words=True,
                                   break_on_hyphens=False, replace_whitespace=False,
                                   drop_whitespace=True) or [""])
    return lines


def paginate(text: str, cols: int, rows: int) -> List[str]:
    """Split into pages of at most `rows` lines x `cols` columns (joined with \\n)."""
    cols = max(10, min(80, cols))
    rows = max(1, min(40, rows))
    lines = wrap_lines(text, cols)
    while lines and lines[-1] == "":
        lines.pop()
    pages = ["\n".join(lines[i:i + rows]) for i in range(0, len(lines), rows)]
    return pages or [""]
