from pathlib import Path

import pytest
import zarr

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_read_zarr(data, fixture_dpath):
    arr = zarr.open_array(fixture_dpath / "example.zarr")
    assert arr[:] == pytest.approx(data)


def test_read_correct():
    from zarr_template import TemplateChunkKeyEncoding

    d = {"name": "template", "configuration": {"template": "{0}_{1}_{2}.jpeg"}}
    TemplateChunkKeyEncoding.from_dict(d)


def test_read_alias():
    from zarr_template import TemplateChunkKeyEncoding

    d = {"name": "template", "configuration": {"format": "{0}_{1}_{2}.jpeg"}}
    TemplateChunkKeyEncoding.from_dict(d)
