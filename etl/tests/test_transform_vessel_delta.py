import pandas as pd
import pytest

from etl.models.context import VesselContext
from etl.transform.transform_vessel_delta import transform_vessel_delta


BASE_FIELDS = {
    "width": None,
    "length": None,
    "call_sign": None,
    "vessel_type_id": None,
    "draft": None,
    "cargo_type_id": None,
    "transceiver_class": None,
}

@pytest.mark.parametrize("new_data,old_data,expected_count", [
    # 1 - new MMSI -> Selected
    (
        {"mmsi": "111111111", "last_update": "2024-01-13T00:00:00", "vessel_name": "Ship1", "imo": None},
        {"vessel_id": 1, "locked": False, "mmsi": "222222222", "last_update": "2025-01-13T00:00:00", "vessel_name": "Ship2", "imo": None},
        1
    ),
    # 2 - Locked => Ignored
    (
        {"mmsi": "222222222", "last_update": "2026-01-13T00:00:00", "vessel_name": "Ship1", "imo": "IMOTEST02"},
        {"vessel_id": 1, "locked": True, "mmsi": "222222222", "last_update": "2025-01-13T00:00:00", "vessel_name": "Ship2", "imo": None},
        0
    ),
    # 3 - More recent + different name => Update
    (
        {"mmsi": "222222222", "last_update": "2025-01-13T00:00:00", "vessel_name": "Ship1", "imo": None},
        {"vessel_id": 1, "locked": False, "mmsi": "222222222", "last_update": "2024-01-13T00:00:00", "vessel_name": "Ship2", "imo": None},
        1
    ),
    # 4 - More recent + enw field => Update
    (
        {"mmsi": "222222222", "last_update": "2025-01-13T00:00:00", "vessel_name": "Ship2", "imo": "IMOTEST02"},
        {"vessel_id": 1, "locked": False, "mmsi": "222222222", "last_update": "2024-01-13T00:00:00", "vessel_name": "Ship2", "imo": None},
        1
    ),
    # 5 - More recent but equals => Ignored
    (
        {"mmsi": "222222222", "last_update": "2025-01-13T00:00:00", "vessel_name": "Ship2", "imo": None},
        {"vessel_id": 1, "locked": False, "mmsi": "222222222", "last_update": "2024-01-13T00:00:00", "vessel_name": "Ship2", "imo": None},
        0
    ),
    # 6 - Older + differences => Ignored
    (
        {"mmsi": "222222222", "last_update": "2024-01-13T00:00:00", "vessel_name": "Ship1", "imo": None},
        {"vessel_id": 1, "locked": False, "mmsi": "222222222", "last_update": "2025-01-13T00:00:00", "vessel_name": "Ship2", "imo": None},
        0
    ),
    # 7 - Older + new field => Update (case "fill")
    (
        {"mmsi": "222222222", "last_update": "2024-01-13T00:00:00", "vessel_name": "Ship2", "imo": "IMOTEST02"},
        {"vessel_id": 1, "locked": False, "mmsi": "222222222", "last_update": "2025-01-13T00:00:00", "vessel_name": "Ship2", "imo": None},
        1
    ),
    # 8 - Older + new field + differences => Update (Mixt case treated as 'fill' )
    (
        {"mmsi": "222222222", "last_update": "2024-01-13T00:00:00", "vessel_name": "Ship1", "imo": "IMOTEST02"},
        {"vessel_id": 1, "locked": False, "mmsi": "222222222", "last_update": "2025-01-13T00:00:00", "vessel_name": "Ship2", "imo": None},
        1
    ),
    # 9 - Older without changes => Ignored
    (
        {"mmsi": "222222222", "last_update": "2024-01-13T00:00:00", "vessel_name": "Ship2", "imo": None},
        {"vessel_id": 1, "locked": False, "mmsi": "222222222", "last_update": "2025-01-13T00:00:00", "vessel_name": "Ship2", "imo": None},
        0
    ),
])
def test_transform_vessel_delta(new_data, old_data, expected_count):
    new_df = pd.DataFrame([{**BASE_FIELDS, **new_data}])
    old_df = pd.DataFrame([{**BASE_FIELDS, **old_data}])

    context = VesselContext(df=new_df,df_db=old_df)

    updated_context = transform_vessel_delta(context)

    assert len(updated_context.df) == expected_count


def test_multi_vessel_mix():
    # - 111111111 : new MMSI → Selected
    # - 222222222 : More recent, and name different → Updated
    # - 333333333 : Older without changes → Ignored
    new_data_list = [
        {"mmsi": "111111111", "last_update": "2024-01-13T00:00:00", "vessel_name": "ShipNew", "imo": None},
        {"mmsi": "222222222", "last_update": "2025-01-13T00:00:00", "vessel_name": "ShipUpdate", "imo": None},
        {"mmsi": "333333333", "last_update": "2023-01-13T00:00:00", "vessel_name": "ShipOld", "imo": None},
    ]

    old_data_list = [
        {"vessel_id": 1, "locked": False, "mmsi": "222222222", "last_update": "2024-01-13T00:00:00", "vessel_name": "ShipOldName", "imo": None},
        {"vessel_id": 2, "locked": False, "mmsi": "333333333", "last_update": "2024-01-13T00:00:00", "vessel_name": "ShipOld", "imo": None},
    ]

    new_df = pd.DataFrame([{**BASE_FIELDS, **d} for d in new_data_list])
    old_df = pd.DataFrame([{**BASE_FIELDS, **d} for d in old_data_list])

    context = VesselContext(df=new_df, df_db=old_df)
    updated_context = transform_vessel_delta(context)


    assert len(updated_context.df) == 2
    selected_mmsi = set(updated_context.df["mmsi"])
    assert selected_mmsi == {"111111111", "222222222"}
