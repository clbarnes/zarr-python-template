from pathlib import Path

import pytest
import zarr

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_read_zarr(data, fixture_dpath):
    arr = zarr.open_array(fixture_dpath / "example.zarr")
    assert arr[:] == pytest.approx(data)
