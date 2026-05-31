"""Generate machine-translated draft entries for a .po catalog.

Reads a .po file, runs every untranslated msgid through Google Translate
(via the unofficial googletrans library), writes the translation back
as msgstr, and marks every translated entry as #, fuzzy so it's flagged
for native-speaker review.

Usage:
    python scripts/translate_po.py translations/sn/LC_MESSAGES/messages.po --lang sn

The googletrans dependency lives in App/backend/requirements-dev.txt and
is never installed on Railway. This script is offline-only.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Entry:
    msgid: str
    msgid_plural: str | None


_MSGID_BLOCK = re.compile(
    r'(?ms)'
    r'(?P<header>(?:#[^\n]*\n)*)'                # any leading # comments
    r'msgid "(?P<msgid>(?:[^"\\]|\\.)*)"\n'
    r'(?:msgid_plural "(?P<plural>(?:[^"\\]|\\.)*)"\n)?'
    r'(?P<msgstr>(?:msgstr(?:\[\d+\])? "[^"]*"\n)+)'
)


def parse_msgids(text: str) -> list[Entry]:
    entries: list[Entry] = []
    for m in _MSGID_BLOCK.finditer(text):
        msgid = m.group("msgid")
        if not msgid:  # skip the header entry whose msgid is ""
            continue
        entries.append(Entry(msgid=msgid, msgid_plural=m.group("plural")))
    return entries


def _translate_one(text: str, dest: str) -> str:
    """Real Google-Translate call. Replaced by a stub in tests."""
    from googletrans import Translator  # imported lazily so tests can monkeypatch
    return Translator().translate(text, dest=dest).text


def translate_catalog(po_path: Path, lang: str) -> None:
    """Read a .po catalog, translate every entry, write back with #, fuzzy."""
    text = po_path.read_text(encoding="utf-8")

    def replace(m: re.Match) -> str:
        msgid = m.group("msgid")
        if not msgid:
            return m.group(0)  # header entry — leave alone
        plural = m.group("plural")
        header_lines = m.group("header") or ""
        # Don't add a duplicate `#, fuzzy` marker if one is already present.
        if "fuzzy" not in header_lines:
            header_lines = header_lines + "#, fuzzy\n"

        translated_singular = _translate_one(msgid, lang).replace('"', '\\"')
        if plural is None:
            new_msgstr = f'msgstr "{translated_singular}"\n'
        else:
            translated_plural = _translate_one(plural, lang).replace('"', '\\"')
            new_msgstr = (
                f'msgstr[0] "{translated_singular}"\n'
                f'msgstr[1] "{translated_plural}"\n'
            )

        plural_line = f'msgid_plural "{plural}"\n' if plural else ""
        return (
            f'{header_lines}'
            f'msgid "{msgid}"\n'
            f'{plural_line}'
            f'{new_msgstr}'
        )

    new_text = _MSGID_BLOCK.sub(replace, text)
    po_path.write_text(new_text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("po_path", type=Path)
    parser.add_argument("--lang", required=True, help="Target language code (e.g. sn, nd).")
    args = parser.parse_args()
    translate_catalog(args.po_path, args.lang)
    print(f"Translated {args.po_path} to {args.lang} (entries flagged #, fuzzy).")


if __name__ == "__main__":
    main()
