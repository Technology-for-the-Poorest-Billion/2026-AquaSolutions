"""Deterministic DHIS2 UID generation.

A DHIS2 UID is 11 chars: first is a letter, the rest are alphanumeric.
We derive it from a SHA-256 of the seed so the same seed always yields the
same UID — making the generated metadata reproducible and parent refs stable.
"""

from __future__ import annotations

import hashlib

_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_ALNUM = _LETTERS + "0123456789"


def dhis2_uid(seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    first = _LETTERS[digest[0] % len(_LETTERS)]
    rest = "".join(_ALNUM[b % len(_ALNUM)] for b in digest[1:11])
    return first + rest
