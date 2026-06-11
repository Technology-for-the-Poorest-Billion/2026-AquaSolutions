"""Tests for the SMS state-machine parsers (parse_case_count, parse_symptoms, parse_onset)."""

from datetime import date


def test_parse_case_count_accepts_positive_integers():
    from sms_dialog import parse_case_count
    assert parse_case_count("3") == 3
    assert parse_case_count("17") == 17


def test_parse_case_count_rejects_zero_and_negative():
    from sms_dialog import parse_case_count
    assert parse_case_count("0") is None
    assert parse_case_count("-2") is None


def test_parse_case_count_rejects_above_200():
    from sms_dialog import parse_case_count
    assert parse_case_count("500") is None


def test_parse_case_count_extracts_from_text():
    from sms_dialog import parse_case_count
    assert parse_case_count("about 5 people") == 5


def test_parse_case_count_rejects_garbage():
    from sms_dialog import parse_case_count
    assert parse_case_count("nope") is None


def test_parse_symptoms_by_digit():
    from sms_dialog import parse_symptoms
    assert parse_symptoms("1,3") == ["diarrhoea", "fever"]
    assert parse_symptoms("1 2 3 4") == ["diarrhoea", "vomiting", "fever", "dehydration"]


def test_parse_symptoms_by_name():
    from sms_dialog import parse_symptoms
    assert parse_symptoms("diarrhoea, fever") == ["diarrhoea", "fever"]


def test_parse_symptoms_dedupes():
    from sms_dialog import parse_symptoms
    assert parse_symptoms("1,1,1") == ["diarrhoea"]


def test_parse_symptoms_returns_none_on_no_matches():
    from sms_dialog import parse_symptoms
    assert parse_symptoms("nothing") is None
    assert parse_symptoms("") is None


def test_parse_onset_today():
    from sms_dialog import parse_onset
    assert parse_onset("today") == date.today()
    assert parse_onset("TODAY") == date.today()


def test_parse_onset_yesterday():
    from sms_dialog import parse_onset
    from datetime import timedelta
    assert parse_onset("yesterday") == date.today() - timedelta(days=1)


def test_parse_onset_dd_mm():
    from sms_dialog import parse_onset
    today = date.today()
    parsed = parse_onset(f"{today.day:02d}/{today.month:02d}")
    assert parsed == today


def test_parse_onset_rejects_future():
    from sms_dialog import parse_onset
    from datetime import timedelta
    future = date.today() + timedelta(days=10)
    assert parse_onset(f"{future.day:02d}/{future.month:02d}") is None


def test_parse_onset_rejects_garbage():
    from sms_dialog import parse_onset
    assert parse_onset("sometime") is None
