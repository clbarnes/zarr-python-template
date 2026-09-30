from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Self

import pytest

import template_cke

PWD = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Example:
    template: str
    separator: str | None
    chunk_coordinate: list[int]
    encoded: str
    note: str

    @classmethod
    def from_row_dict(cls, row: dict[str, str]) -> Self:
        return cls(
            row["template"],
            row["separator"] or None,
            [int(c) for c in row["chunk_coordinate"].split(",")],
            row["encoded"],
            row["note"],
        )


def id_fn(example: Example) -> str:
    return "".join(c if c.isalnum() else "_" for c in example.note)


def read_tsv():
    with PWD.joinpath("fixtures/examples.tsv").open(newline="") as f:
        rdr = csv.DictReader(f, delimiter="\t")
        for row in rdr:
            yield Example.from_row_dict(row)


@pytest.mark.parametrize(("example",), [[eg] for eg in read_tsv()], ids=id_fn)
def test_examples(example: Example):
    cke = template_cke.impl.TemplateChunkKeyEncoder.from_format(
        example.template, example.separator
    )
    out = cke.encode(example.chunk_coordinate)
    assert out == example.encoded
