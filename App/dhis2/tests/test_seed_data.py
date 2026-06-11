from metadata.seed_data import SEED_NEIGHBORHOODS, SEED_STATIONS


def test_neighborhood_count():
    assert len(SEED_NEIGHBORHOODS) == 4


def test_station_count():
    assert len(SEED_STATIONS) == 32


def test_every_station_references_a_real_neighborhood():
    nbh_ids = {nid for nid, _ in SEED_NEIGHBORHOODS}
    for station_id, name, lat, lon, nbh_id in SEED_STATIONS:
        assert nbh_id in nbh_ids, f"station {station_id} has unknown neighbourhood {nbh_id}"


def test_station_ids_unique():
    ids = [s[0] for s in SEED_STATIONS]
    assert len(set(ids)) == len(ids)
