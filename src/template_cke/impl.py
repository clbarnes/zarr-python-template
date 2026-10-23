from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Literal, NotRequired, Self, TypedDict

logger = logging.getLogger(__name__)


def _pad(val: int, pad: int):
    return f"{val:0{pad}}"


@dataclass
class CatchAll:
    pad: int = 0

    def encode(self, coord: Sequence[int], exclude: set[int], separator: str) -> str:
        return separator.join(
            _pad(c, self.pad) for idx, c in enumerate(coord) if idx not in exclude
        )


@dataclass
class Index:
    index: int
    pad: int = 0

    def pos_idx(self, length: int) -> int:
        if self.index >= 0:
            if self.index >= length:
                raise ValueError("Index longer than coordinate")
            return self.index
        return self.index % length

    def encode(self, coord: Sequence[int]) -> str:
        return _pad(coord[self.index], self.pad)

    def is_neg(self) -> bool:
        return self.index < 0


type FormatPart = str | CatchAll | Index


class TemplateChunkKeyEncodingConfiguration(TypedDict):
    """TypedDict representing the configuration object within the Zarr v3 metadata representing the template chunk key encoding.

    i.e.

        {
          "format": "{*}",
          "separator": "/"
        }
    """

    format: str
    separator: NotRequired[str | None]


class TemplateChunkKeyEncodingMetadata(TypedDict):
    """TypedDict representing the Zarr v3 metadata representing the template chunk key encoding.

    i.e.

        {
          "name": "template",
          "configuration": {
            ... // see TemplateChunkKeyEncodingConfiguration type
          }
        }
    """

    name: Literal["template"]
    configuration: TemplateChunkKeyEncodingConfiguration


class TemplateChunkKeyEncoder:
    """Generic chunk key encoder for use with any zarr library."""

    def __init__(self, parts: list[FormatPart], separator: str | None = None) -> None:
        self.parts = parts
        self.separator = separator
        self.has_catchall = False
        self.idxs: set[int] = set()
        self.largest_idx = -1
        for p in parts:
            if isinstance(p, CatchAll):
                if self.has_catchall:
                    raise ValueError("More than one catchall found")
                else:
                    self.has_catchall = True
            elif isinstance(p, Index):
                if p.index in self.idxs:
                    raise ValueError(f"Index referred to more than once: {self.idxs}")
                self.idxs.add(p.index)
                self.largest_idx = max(self.largest_idx, p.index)

    @classmethod
    def from_format(cls, format: str, separator: str | None = None) -> Self:
        parts = list(parse_format(format))
        return cls(parts, separator)

    @classmethod
    def from_config(cls, config: TemplateChunkKeyEncodingConfiguration) -> Self:
        return cls.from_format(**config)

    @classmethod
    def from_metadata(cls, metadata: TemplateChunkKeyEncodingMetadata) -> Self:
        name = metadata.get("name")
        if name != "template":
            raise ValueError(f"Expected name 'template', got '{name!r}'")
        return cls.from_config(metadata.get("configuration"))

    def encode(self, coord: Sequence[int]) -> str:
        if self.largest_idx > len(coord):
            raise ValueError(
                f"Coordinate is too short; expected at least {self.largest_idx} elements"
            )
        out_parts: list[str] = []
        catchall: tuple[int, CatchAll] | None = None
        used_idxs = set()
        for part in self.parts:
            if isinstance(part, str):
                out_parts.append(part)
            elif isinstance(part, CatchAll):
                if catchall is not None:
                    raise ValueError("More than one catchall found")
                catchall = (len(out_parts), part)
                out_parts.append("")  # to be filled later
            elif isinstance(part, Index):
                pos = part.pos_idx(len(coord))
                if pos in used_idxs:
                    raise ValueError(f"Index {pos} used more than once")
                used_idxs.add(pos)
                out_parts.append(part.encode(coord))
            else:
                raise TypeError(f"Unknown template encoder part type: {type(part)}")

        if catchall is not None:
            if self.separator is None:
                raise ValueError("Format had catchall but no separator given")
            out_parts[catchall[0]] = catchall[1].encode(
                coord, used_idxs, self.separator
            )

        return "".join(out_parts)


def _parse_braced(s: str) -> CatchAll | Index:
    """Return index (or none for catchall) and padding (or none)"""
    logger.debug("parsing braced expression %s", s)
    before, *after = s.split(":")
    if len(after) > 1:
        raise ValueError(f"Only expected one colon in '{s}'")
    if not after:
        padding = 0
    else:
        post = after.pop()
        if not post.startswith("0"):
            raise ValueError(f"Unknown padding format '{post}'")
        padding = int(post[1:])

    if before == "*":
        return CatchAll(padding)
    return Index(int(before), padding)


def _strget(s: str, idx: int) -> str | None:
    if idx >= len(s) or idx < 0:
        return None
    return s[idx]


def parse_format(fmt: str) -> Iterable[FormatPart]:
    idx = 0
    buf: list[str] = []
    in_brace = False
    has_catchall = False

    while idx < len(fmt):
        c = fmt[idx]
        idx += 1
        if in_brace and c == "}":
            in_brace = False
            braced = _parse_braced("".join(buf))
            if isinstance(braced, CatchAll):
                if has_catchall:
                    raise ValueError("More than one catchall variant found")
                else:
                    has_catchall = True
            logger.debug("emitting %s", braced)
            yield braced
            buf.clear()
        elif not in_brace and c == "{":
            if (c2 := _strget(fmt, idx)) and c2 == "{":
                buf.append("{")
                idx += 1
                continue
            if buf:
                s = "".join(buf)
                logger.debug("emitting '%s'", s)
                yield s
                buf.clear()
            in_brace = True
            continue
        elif not in_brace and c == "}":
            if (c2 := _strget(fmt, idx)) and c2 == "}":
                buf.append("}")
                idx += 1
                continue
            raise ValueError("Unmatched closing brace")
        else:
            buf.append(c)

    if in_brace:
        raise ValueError("Unmatched opening brace")
    if buf:
        s = "".join(buf)
        logger.debug("emitting '%s'", s)
        yield s
