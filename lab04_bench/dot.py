"""Binary64 dot product and a persistent benchmark worker."""

from array import array
from pathlib import Path
import sys


def read_vector(path, n):
    if n < 0:
        raise ValueError("negative length")
    raw = Path(path).read_bytes()
    if len(raw) != 8 * n:
        raise ValueError(f"expected {8 * n} bytes, got {len(raw)}")
    values = array("d")
    if values.itemsize != 8:
        raise RuntimeError("binary64 is required")
    values.frombytes(raw)
    if sys.byteorder == "big":
        values.byteswap()
    return values


def dot(a, b):
    if len(a) != len(b):
        raise ValueError("length mismatch")
    total = 0.0
    for x, y in zip(a, b):
        total += x * y
    return total


def worker(n, m, path_a, path_b):
    if n != m:
        raise ValueError("length mismatch")
    a, b = read_vector(path_a, n), read_vector(path_b, m)
    checksum = 0.0
    print("READY python", flush=True)
    for line in sys.stdin:
        command = line.split()
        match command:
            case ["go", count]:
                reps = int(count)
                if reps <= 0:
                    raise ValueError("repetitions must be positive")
                checksum = 0.0
                for _ in range(reps):
                    checksum += dot(a, b)
                print("DONE", flush=True)
            case ["sum"]:
                print(format(checksum, ".17g"), flush=True)
            case ["ping"]:
                print("DONE", flush=True)
            case _:
                raise ValueError("invalid command")


if __name__ == "__main__":
    try:
        n, m, path_a, path_b = sys.argv[1:]
        worker(int(n), int(m), path_a, path_b)
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(2)
