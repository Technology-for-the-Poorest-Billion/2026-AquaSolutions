"""Geography seed COPIED from App/backend/database.py (SEED_NEIGHBORHOODS /
SEED_STATIONS). Deliberately duplicated: the DHIS2 track is a separate entity
from the frozen demo. If the demo's geography changes, re-sync this by hand.
"""

# (neighborhood_id, name)
SEED_NEIGHBORHOODS = [
    (1, "Central Harare"),
    (2, "Northern Suburbs"),
    (3, "Southern Areas"),
    (4, "Eastern Suburbs"),
]

# (station_id, name, lat, lon, neighborhood_id)
SEED_STATIONS = [
    (1,  "Avenues — central clinic",          -17.815, 31.050, 1),
    (2,  "Belvedere — community hall",        -17.840, 31.025, 1),
    (7,  "Milton Park — health post",         -17.832, 31.030, 1),
    (11, "Causeway — government complex",     -17.831, 31.048, 1),
    (12, "Kopje — civic hall",                -17.835, 31.038, 1),
    (13, "CBD — central market",              -17.828, 31.052, 1),
    (14, "Africa Unity Square — fountain",    -17.830, 31.054, 1),
    (15, "Workington — industrial water",     -17.840, 31.030, 1),
    (6,  "Newlands — shopping centre",        -17.810, 31.067, 2),
    (9,  "Mt Pleasant — north well",          -17.795, 31.045, 2),
    (16, "Avondale — north clinic",           -17.797, 31.038, 2),
    (17, "Belgravia — community well",        -17.800, 31.038, 2),
    (18, "Mt Pleasant Heights — school",      -17.785, 31.040, 2),
    (19, "Marlborough — clinic",              -17.795, 31.025, 2),
    (20, "Strathaven — water point",          -17.797, 31.045, 2),
    (21, "Pomona — north settlement",         -17.787, 31.060, 2),
    (4,  "Mbare — Musika market",             -17.860, 31.045, 3),
    (5,  "Hatfield — community borehole",     -17.852, 31.072, 3),
    (22, "Waterfalls — south clinic",         -17.870, 31.058, 3),
    (23, "Sunningdale — water point",         -17.875, 31.078, 3),
    (24, "Lichendale — primary school",       -17.875, 31.050, 3),
    (25, "Southerton — community well",       -17.865, 31.020, 3),
    (26, "Aspindale Park — water point",      -17.870, 31.025, 3),
    (27, "Prospect — health post",            -17.878, 31.015, 3),
    (3,  "Eastlea — primary school",          -17.825, 31.062, 4),
    (8,  "Hillside — water point",            -17.847, 31.058, 4),
    (10, "Greendale — east settlement",       -17.835, 31.082, 4),
    (28, "Highlands — east clinic",           -17.820, 31.075, 4),
    (29, "Athlone — primary school",          -17.825, 31.085, 4),
    (30, "Cranborne — water point",           -17.850, 31.075, 4),
    (31, "Donnybrook — community hall",       -17.855, 31.085, 4),
    (32, "Msasa — industrial water point",    -17.830, 31.090, 4),
]
