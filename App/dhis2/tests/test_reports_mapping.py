from etl.reports import report_event_to_row, SYMPTOM_PREFIX

DE = {
    "deCASE": "Illness - Case Count",
    "deONSET": "Illness - Onset Date",
    "deDIAR": "Symptom: Diarrhoea",
    "deVOM": "Symptom: Vomiting",
}
OU = {
    "ouBORE": {"name": "Milton Park — health post", "code": "STATION-7", "parent": "ouNBH"},
    "ouNBH": {"name": "Central Harare", "code": None, "parent": "ouDIST"},
}
SYMPTOMS = ["Diarrhoea", "Vomiting"]


def _event():
    return {
        "event": "evt1",
        "occurredAt": "2026-06-05T00:00:00.000",
        "orgUnit": "ouBORE",
        "dataValues": [
            {"dataElement": "deCASE", "value": "5"},
            {"dataElement": "deONSET", "value": "2026-06-03"},
            {"dataElement": "deDIAR", "value": "true"},
        ],
    }


def test_row_core_fields():
    row = report_event_to_row(_event(), DE, OU, SYMPTOMS)
    assert row["event_id"] == "evt1"
    assert row["timestamp"] == "2026-06-05T00:00:00.000"
    assert row["onset_date"] == "2026-06-03"
    assert row["station_id"] == 7
    assert row["borehole"] == "Milton Park — health post"
    assert row["neighbourhood"] == "Central Harare"
    assert row["case_count"] == 5


def test_symptom_columns_are_0_or_1():
    row = report_event_to_row(_event(), DE, OU, SYMPTOMS)
    assert row["diarrhoea"] == 1   # ticked
    assert row["vomiting"] == 0    # absent
