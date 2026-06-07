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
