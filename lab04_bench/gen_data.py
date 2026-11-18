"""Generate reproducible raw little-endian float64 vectors."""

from array import array
from pathlib import Path
from random import Random
import sys

SIZES = (1_000, 10_000, 100_000, 1_000_000)
DATA = Path(__file__).resolve().parent / "data"


def write_vector(path, values):
    data = array("d", values)
    if data.itemsize != 8:
        raise RuntimeError("binary64 is required")
    if sys.byteorder == "big":
        data.byteswap()
    with path.open("wb") as stream:
        data.tofile(stream)


if __name__ == "__main__":
    for n in SIZES:
        directory = DATA / str(n)
        directory.mkdir(parents=True, exist_ok=True)
        rng = Random(20261118 + n)
        for name in ("a", "b"):
            write_vector(directory / f"{name}_f64.bin", (rng.random() for _ in range(n)))
        print(f"N={n:>7}   {n * 8:>8} bytes/file   seed={20261118 + n}")
