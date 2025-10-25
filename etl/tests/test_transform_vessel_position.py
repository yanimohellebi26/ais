import pandas as pd
import pytest
from unittest.mock import patch

from etl.models.context import PipelineContext
from etl.transform.transform_vessel_position import detect_vessel_incoherent_positions, haversine_km, speed_kmh

@pytest.mark.parametrize(
    "new_positions, prev_positions, expected_remaining_mmsi",
    [
        # 1 - Coherent position
        (
            [{"mmsi": "111111111", "base_date_time": "2025-01-01T12:00:00", "lat": 48.8566, "lon": 2.3522}],
            [{"mmsi": "111111111", "prev_date": "2025-01-01T11:00:00", "prev_lat": 48.8566, "prev_lon": 2.3522}],
            {"111111111"}
        ),
        # 2 - Too fast -> removed
        (
            [{"mmsi": "222222222", "base_date_time": "2025-01-01T11:00:00", "lat": 50.5, "lon": 2.3522}],
            [{"mmsi": "222222222", "prev_date": "2025-01-01T10:00:00", "prev_lat": 48.8566, "prev_lon": 2.3522}],
            set()
        ),
        # 3 - No previous position -> kept
        (
            [{"mmsi": "333333333", "base_date_time": "2025-01-01T12:00:00", "lat": 48.8566, "lon": 2.3522}],
            [],
            {"333333333"}
        ),
        # 4 - Invalid time (negative) -> removed
        (
            [{"mmsi": "444444444", "base_date_time": "2025-01-01T10:00:00", "lat": 48.8566, "lon": 2.3522}],
            [{"mmsi": "444444444", "prev_date": "2025-01-01T12:00:00", "prev_lat": 48.0, "prev_lon": 2.0}],
            set()
        ),
    ]
)
@patch("etl.transform.transform_vessel_position.get_session")
@patch("etl.transform.transform_vessel_position.pd.read_sql")
def test_detect_vessel_incoherent_positions(mock_read_sql, mock_session, new_positions, prev_positions, expected_remaining_mmsi):
    df = pd.DataFrame(new_positions)
    context = PipelineContext(df=df)

    mock_read_sql.return_value = pd.DataFrame(prev_positions, columns=["mmsi", "prev_date", "prev_lat", "prev_lon"])
    mock_session.return_value.__enter__.return_value.bind = "fake_bind"

    updated_context = detect_vessel_incoherent_positions(context)

    remaining_mmsi = set(updated_context.df["mmsi"])
    assert remaining_mmsi == expected_remaining_mmsi

def test_haversine_km():
    dist = haversine_km(48.8566, 2.3522, 51.5074, -0.1278)
    assert round(dist) == 344

def test_speed_kmh():
    dist = pd.Series([100, 0])
    time = pd.Series([2, 0])
    spd = speed_kmh(dist, time)
    assert spd.iloc[0] == 50
    assert pd.isna(spd.iloc[1])

def test_empty_dataset():
    context = PipelineContext(df=pd.DataFrame())
    updated_context = detect_vessel_incoherent_positions(context)
    assert updated_context.df.empty

@patch("etl.transform.transform_vessel_position.get_session")
@patch("etl.transform.transform_vessel_position.pd.read_sql")
def test_multiple_mmsi(mock_read_sql, mock_session):
    # 111111111 - coherent
    # 222222222 - too fast
    # 333333333 - no previous position
    new_positions = [
        {"mmsi": "111111111", "base_date_time": "2025-01-01T12:00:00", "lat": 48.8566, "lon": 2.3522},
        {"mmsi": "222222222", "base_date_time": "2025-01-01T11:00:00", "lat": 50.5, "lon": 2.3522},
        {"mmsi": "333333333", "base_date_time": "2025-01-01T12:00:00", "lat": 48.8566, "lon": 2.3522},
    ]
    df = pd.DataFrame(new_positions)
    context = PipelineContext(df=df)

    prev_positions = [
        {"mmsi": "111111111", "prev_date": "2025-01-01T11:00:00", "prev_lat": 48.8566, "prev_lon": 2.3522},
        {"mmsi": "222222222", "prev_date": "2025-01-01T10:30:00", "prev_lat": 48.8566, "prev_lon": 2.3522},
    ]

    mock_read_sql.return_value = pd.DataFrame(prev_positions, columns=["mmsi", "prev_date", "prev_lat", "prev_lon"])
    mock_session.return_value.__enter__.return_value.bind = "fake_bind"

    updated_context = detect_vessel_incoherent_positions(context)

    remaining_mmsi = set(updated_context.df["mmsi"])
    assert remaining_mmsi == {"111111111", "333333333"}