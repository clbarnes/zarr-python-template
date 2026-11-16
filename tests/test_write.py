import pytest
import zarr
from zarr.storage import MemoryStore

from zarr_template import TemplateChunkKeyEncoding


def test_writes_template():
    cke = TemplateChunkKeyEncoding("{0}_{1}.jpeg")
    d = cke.to_dict()
    assert "template" in d["configuration"]  # type:ignore
    assert "format" not in d["configuration"]  # type:ignore


def test_write_zarr(data):
    store = MemoryStore()
    arr = zarr.create_array(
        store,
        data=data,
        chunks=[5, 5],
        chunk_key_encoding=TemplateChunkKeyEncoding("c/{*}.chunk", "/"),
    )
    for k in store._store_dict:
        if k.endswith("zarr.json"):
            continue
        assert k.endswith(".chunk")
    data2 = arr[:]
    assert data == pytest.approx(data2)
