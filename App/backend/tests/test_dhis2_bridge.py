import dhis2_bridge


def test_enabled_reads_env(monkeypatch):
    monkeypatch.delenv("DHIS2_BRIDGE_ENABLED", raising=False)
    assert dhis2_bridge.enabled() is False
    monkeypatch.setenv("DHIS2_BRIDGE_ENABLED", "true")
    assert dhis2_bridge.enabled() is True


def test_build_event_payload_core():
    payload = dhis2_bridge.build_event_payload(
        program_uid="prog", stage_uid="stg", org_unit_uid="ou",
        case_de_uid="deCASE", onset_de_uid="deONSET",
        symptom_de_by_key={"diarrhoea": "deDIAR", "fever": "deFEVER"},
        case_count=5, symptoms=["diarrhoea", "fever"],
        onset_iso="2026-06-03", occurred_iso="2026-06-05T10:00:00+00:00",
    )
    ev = payload["events"][0]
    assert ev["program"] == "prog" and ev["programStage"] == "stg" and ev["orgUnit"] == "ou"
    assert ev["occurredAt"] == "2026-06-05T10:00:00+00:00"
    assert ev["status"] == "COMPLETED"
    dv = {d["dataElement"]: d["value"] for d in ev["dataValues"]}
    assert dv["deCASE"] == "5"
    assert dv["deONSET"] == "2026-06-03"
    assert dv["deDIAR"] == "true"
    assert dv["deFEVER"] == "true"


def test_build_event_payload_omits_unmapped_or_absent_symptoms():
    payload = dhis2_bridge.build_event_payload(
        program_uid="p", stage_uid="s", org_unit_uid="o",
        case_de_uid="c", onset_de_uid="n",
        symptom_de_by_key={"diarrhoea": "deDIAR", "vomiting": None},
        case_count=1, symptoms=["diarrhoea", "vomiting"],
        onset_iso="2026-06-01", occurred_iso="2026-06-01T00:00:00+00:00",
    )
    dv = {d["dataElement"]: d["value"] for d in payload["events"][0]["dataValues"]}
    assert dv.get("deDIAR") == "true"
    assert "vomiting" not in dv and None not in dv  # unmapped symptom dropped


import urllib.request as _u
import urllib.error as _ue

import dhis2_bridge as _b


def _dhis2_up():
    try:
        req = _u.Request(_b.base_url() + "/api/system/info.json")
        req.add_header("Authorization", _b._auth_header())
        with _u.urlopen(req, timeout=5) as r:
            return r.status == 200
    except (_ue.URLError, OSError):
        return False


import pytest

dhis2 = pytest.mark.skipif(not _dhis2_up(), reason="DHIS2 not reachable")


@dhis2
def test_create_event_round_trip():
    # station 1 == DHIS2 org unit code STATION-1 (Avenues — central clinic)
    event_id = dhis2_bridge.create_event_from_report(
        station_id=1, case_count=3, symptoms=["diarrhoea", "vomiting"], onset="2026-06-03",
    )
    assert event_id, "expected a created event id"
    try:
        got = _b._get(f"/api/tracker/events/{event_id}.json?fields=event,dataValues[dataElement,value]")
        assert got["event"] == event_id
        assert any(d["value"] == "3" for d in got["dataValues"])
    finally:
        _b._post("/api/tracker?async=false&importStrategy=DELETE",
                 {"events": [{"event": event_id}]})


import json as _json


def test_sms_completion_calls_bridge(client, monkeypatch):
    calls = []
    monkeypatch.setattr(dhis2_bridge, "enabled", lambda: True)
    monkeypatch.setattr(dhis2_bridge, "create_event_from_report",
                        lambda **kw: calls.append(kw) or "evtTEST")

    def sms(body):
        return client.post("/sms", data={"From": "+15550001111", "Body": body})

    sms("1")          # station -> awaiting_case_count
    sms("5")          # case count -> awaiting_symptoms
    sms("1,3")        # diarrhoea, fever -> awaiting_onset
    r = sms("today")  # onset -> complete (bridge fires)
    assert b"Report complete" in r.data

    assert len(calls) == 1
    kw = calls[0]
    assert kw["station_id"] == 1
    assert kw["case_count"] == 5
    assert set(kw["symptoms"]) == {"diarrhoea", "fever"}
    assert kw["onset"]  # ISO onset string present


def test_sms_completion_no_bridge_when_disabled(client, monkeypatch):
    calls = []
    monkeypatch.setattr(dhis2_bridge, "enabled", lambda: False)
    monkeypatch.setattr(dhis2_bridge, "create_event_from_report",
                        lambda **kw: calls.append(kw))

    def sms(body):
        return client.post("/sms", data={"From": "+15550002222", "Body": body})

    sms("1"); sms("5"); sms("1,3"); sms("today")
    assert calls == []  # disabled -> bridge never called
