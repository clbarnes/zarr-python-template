from zarr_template.impl import TemplateChunkKeyEncoder, parse_format

FORMAT = "potato{0}-{2}/${4:03}_{*},{-1}suffix"


def parse_encoder():
    return list(parse_format(FORMAT))


def test_bench_parse(benchmark):
    benchmark(parse_encoder)


def test_benchmark_interp(benchmark):
    enc = TemplateChunkKeyEncoder.from_format(FORMAT, "/")
    coord = (0, 1, 2, 3, 4, 5, 6)
    benchmark(lambda: enc.encode(coord))
