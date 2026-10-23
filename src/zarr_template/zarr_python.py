from dataclasses import dataclass, field
from typing import ClassVar, Literal, cast

from zarr.core.chunk_key_encodings import ChunkKeyEncoding
from zarr.core.common import JSON
from zarr.registry import register_chunk_key_encoding

from .impl import (
    TemplateChunkKeyEncoder,
    TemplateChunkKeyEncodingConfiguration,
)


@dataclass(frozen=True)
class TemplateChunkKeyEncoding(ChunkKeyEncoding):
    """Template chunk key encoding for use with zarr-python."""

    format: str
    separator: str | None = None
    encoder: TemplateChunkKeyEncoder = field(init=False)
    name: ClassVar[Literal["template"]] = "template"

    def __post_init__(self):
        encoder = TemplateChunkKeyEncoder.from_format(self.format, self.separator)
        object.__setattr__(self, "encoder", encoder)

    def encode_chunk_key(self, chunk_coords: tuple[int, ...]) -> str:
        return self.encoder.encode(chunk_coords)

    def to_dict(self) -> dict[str, JSON]:
        config: TemplateChunkKeyEncodingConfiguration = {"format": self.format}
        if self.separator:
            config["separator"] = self.separator

        return {"name": self.name, "configuration": cast(JSON, config)}


register_chunk_key_encoding("template", TemplateChunkKeyEncoding)
