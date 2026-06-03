from metadata.generate_org_units import build_org_units

OPENING_DATE = "2020-01-01T00:00:00.000"


def _by_name(units, name):
    return next(u for u in units if u["name"] == name)


def test_total_unit_count():
    # 1 country + 1 district + 4 neighbourhoods + 32 boreholes
    units = build_org_units()["organisationUnits"]
    assert len(units) == 38


def test_levels_are_assigned():
    units = build_org_units()["organisationUnits"]
    levels = sorted({u["level"] for u in units})
    assert levels == [1, 2, 3, 4]


def test_country_has_no_parent():
    units = build_org_units()["organisationUnits"]
    assert "parent" not in _by_name(units, "Zimbabwe")


def test_neighbourhood_parent_is_district():
    units = build_org_units()["organisationUnits"]
    district = _by_name(units, "Harare")
    central = _by_name(units, "Central Harare")
    assert central["parent"]["id"] == district["id"]
    assert central["level"] == 3


def test_borehole_has_point_geometry_and_station_code():
    units = build_org_units()["organisationUnits"]
    borehole = _by_name(units, "Milton Park — health post")
    assert borehole["level"] == 4
    assert borehole["code"] == "STATION-7"
    assert borehole["geometry"]["type"] == "Point"
    # GeoJSON order is [longitude, latitude]
    assert borehole["geometry"]["coordinates"] == [31.030, -17.832]


def test_all_units_have_required_fields():
    units = build_org_units()["organisationUnits"]
    for u in units:
        assert len(u["id"]) == 11
        assert u["name"]
        assert len(u["shortName"]) <= 50
        assert u["openingDate"] == OPENING_DATE


def test_all_ids_unique():
    units = build_org_units()["organisationUnits"]
    ids = [u["id"] for u in units]
    assert len(set(ids)) == len(ids)
