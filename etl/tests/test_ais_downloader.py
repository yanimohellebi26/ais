import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from etl.extract.AISDownloader import AISDownloader


# -------------------------------
# Fixtures
# -------------------------------
@pytest.fixture
def temp_download_folder(tmp_path):
    """Dossier temporaire pour simuler les téléchargements"""
    folder = tmp_path / "data/downloads"
    folder.mkdir(parents=True, exist_ok=True)
    return str(folder)


# -------------------------------
# Statics
# -------------------------------
def test_construct_file_name():
    # 2015-2024 years
    assert AISDownloader._construct_file_name(2024, date(2024, 1, 13)) == "AIS_2024_01_13.zip"
    # > 2025
    assert AISDownloader._construct_file_name(2025, date(2025, 5, 7)) == "ais-2025-05-07.csv.zst"
    # Invalid
    with pytest.raises(ValueError):
        AISDownloader._construct_file_name(2010, date(2010, 1, 1))


def test_get_index_url():
    downloader = AISDownloader(download_folder="tests/data/downloads")
    assert downloader._get_index_url(2024) == f"{downloader.base_url}/2024/index.html"


# -------------------------------
# Mock requests index
# -------------------------------
@patch("etl.extract.AISDownloader.requests.get")
def test_list_files_from_index(mock_get):
    mock_response = MagicMock()
    mock_response.text = '<a href="AIS_2024_01_13.zip">file</a><a href="AIS_2024_01_14.zip">file</a>'
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    downloader = AISDownloader(download_folder="tests/data/downloads")
    files = downloader._list_files_from_index(2024)
    assert "AIS_2024_01_13.zip" in files
    assert "AIS_2024_01_14.zip" in files


@patch("etl.extract.AISDownloader.requests.get")
@patch("zipfile.ZipFile")
def test_get_file(mock_zip, mock_get, temp_download_folder):
    # Mock http RESPONSE
    mock_response = MagicMock()
    mock_response.content = b"fake zip content"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    # Mock unzip
    mock_zip.return_value.__enter__.return_value.extractall = MagicMock()

    downloader = AISDownloader(download_folder=temp_download_folder)

    # Forcer files list
    with patch.object(AISDownloader, "_list_files_from_index", return_value=["AIS_2024_01_13.zip"]):
        csv_path = downloader.get_file(2024, 1, 13)

    assert csv_path.endswith("AIS_2024_01_13.csv")
    assert os.path.basename(csv_path) == "AIS_2024_01_13.csv"


@patch("etl.extract.AISDownloader.requests.get")
def test_get_file_list(mock_get):
    mock_response = MagicMock()
    mock_response.text = '<a href="AIS_2024_01_13.zip">file</a><a href="AIS_2024_01_14.zip">file</a>'
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    downloader = AISDownloader(download_folder="tests/data/downloads")
    files = downloader.get_file_list(2024)
    assert "AIS_2024_01_13.zip" in files
    assert "AIS_2024_01_14.zip" in files

    files_feb = downloader.get_file_list(2024, month=1)
    assert all("_01_" in f for f in files_feb)
