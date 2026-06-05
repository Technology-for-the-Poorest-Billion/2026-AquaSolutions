import re

from metadata.uid import dhis2_uid

UID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{10}$")


def test_uid_matches_dhis2_format():
    assert UID_RE.match(dhis2_uid("zimbabwe"))


def test_uid_is_deterministic():
    assert dhis2_uid("station-7") == dhis2_uid("station-7")


def test_distinct_seeds_give_distinct_uids():
    seeds = ["country", "district-harare", "nbh-1", "nbh-2", "station-1", "station-32"]
    uids = [dhis2_uid(s) for s in seeds]
    assert len(set(uids)) == len(seeds)
