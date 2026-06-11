"""Unit tests for the translate_po helper, exercising the pure parsing/
writing logic. The Google Translate API call is monkeypatched."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from translate_po import translate_catalog, parse_msgids


SAMPLE_POT = textwrap.dedent('''
    # Sample catalog
    msgid ""
    msgstr ""

    msgid "Sign in"
    msgstr ""

    msgid "Username"
    msgstr ""

    msgid "%(n)d case"
    msgid_plural "%(n)d cases"
    msgstr[0] ""
    msgstr[1] ""
''').strip()


def test_parse_msgids_extracts_non_header_entries():
    entries = parse_msgids(SAMPLE_POT)
    msgids = [e.msgid for e in entries]
    assert "Sign in" in msgids
    assert "Username" in msgids
    # Plural is reported as one entry with both forms
    plural = next(e for e in entries if e.msgid_plural)
    assert plural.msgid == "%(n)d case"
    assert plural.msgid_plural == "%(n)d cases"


def test_translate_catalog_writes_fuzzy_entries(tmp_path, monkeypatch):
    pot = tmp_path / "messages.po"
    pot.write_text(SAMPLE_POT)

    def fake_translate(text: str, dest: str) -> str:
        return f"[{dest}] {text}"

    monkeypatch.setattr("translate_po._translate_one", fake_translate)
    translate_catalog(pot, lang="sn")

    out = pot.read_text()
    assert '#, fuzzy' in out
    assert 'msgstr "[sn] Sign in"' in out
    assert 'msgstr "[sn] Username"' in out
    # Plural — both forms translated
    assert 'msgstr[0] "[sn] %(n)d case"' in out
    assert 'msgstr[1] "[sn] %(n)d cases"' in out
