"""Build, verify and benchmark three persistent standard-library workers."""

from argparse import ArgumentParser
from contextlib import contextmanager
import csv
import math
import os
from pathlib import Path
from statistics import median
import subprocess as sp
import sys
from time import perf_counter

from dot import dot, read_vector
from gen_data import DATA, SIZES

ROOT = Path(__file__).resolve().parent
EXT = ".exe" if os.name == "nt" else ""
BUILD = ROOT / "build"
TARGET = BUILD / "cargo"
MODES = {"Python": "python", "C": "optimized", "Rust": "release"}


def commands(c_exe=None):
    return {
        "Python": [sys.executable, str(ROOT / "dot.py")],
        "C": [str(c_exe or BUILD / ("dot_c" + EXT))],
        "Rust": [str(TARGET / "release" / ("dot_rust" + EXT))],
    }


def compile_workers():
    BUILD.mkdir(exist_ok=True)
    c = ["gcc", "-std=c11", "-Wall", "-Wextra", "-O2", "dot.c",
         "-o", f"build/dot_c{EXT}"]
    rust = ["cargo", "build", "--release", "--offline",
            "--target-dir", "build/cargo"]
    for command in (c, rust):
        print("$", " ".join(command), flush=True)
        sp.run(command, cwd=ROOT, check=True)


def vector_args(n, m, paths=None):
    if paths is None:
        folder = DATA / str(n)
        paths = [folder / f"{v}_f64.bin" for v in ("a", "b")]
    return [str(n), str(m), *map(str, paths)]


@contextmanager
def connect(command, n, m=None, paths=None):
    args = vector_args(n, n if m is None else m, paths)
    with sp.Popen(command + args, stdin=sp.PIPE, stdout=sp.PIPE,
                  stderr=sp.PIPE, text=True, encoding="utf-8") as proc:
        try:
            ready = proc.stdout.readline().strip()
            if not ready.startswith("READY "):
                raise RuntimeError(proc.stderr.read().strip() or "worker rejected input")
            yield proc, ready.removeprefix("READY ")
        finally:
            proc.stdin.close()
            try:
                proc.wait(timeout=5)
            except sp.TimeoutExpired:
                proc.kill()
                proc.wait()


def exchange(proc, command):
    proc.stdin.write(command + "\n")
    proc.stdin.flush()
    reply = proc.stdout.readline().strip()
    if not reply:
        raise RuntimeError("worker terminated during " + command)
    return reply


def timed_batch(proc, command):
    start = perf_counter()
    reply = exchange(proc, command)
    elapsed = perf_counter() - start
    if reply != "DONE":
        raise RuntimeError("invalid acknowledgement")
    return elapsed


def error(value, reference):
    return abs(value - reference) / abs(reference) if reference else abs(value)


def assert_close(value, reference):
    deviation = error(value, reference)
    if not math.isfinite(deviation) or deviation > 1e-9:
        raise RuntimeError(f"{value:.17g} vs {reference:.17g}, error={deviation:.3e}")


def double_loop(a, b):
    total = 0.0
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            if i == j:
                total += x * y
    return total


def verify(workers, sizes=SIZES):
    references = {}
    for n in sizes:
        paths = [Path(name) for name in vector_args(n, n)[2:]]
        a, b = [read_vector(path, n) for path in paths]
        reference = dot(a, b)
        references[n] = reference
        if n == 1_000:
            direct = double_loop(a, b)
            assert_close(reference, direct)
            print(f"N=1000 nested reference={direct:.17g}")
        assert_close(reference, math.fsum(x*y for x, y in zip(a, b)))
        if n == 10_000:
            with connect(workers["Python"], n) as (proc, _):
                for _ in range(3):
                    timed_batch(proc, "go 50")
                pilot = median(timed_batch(proc, "go 50") / 50 for _ in range(5))
            print(f"Python pilot N=10000 | 3 warmups, 5 rounds | {pilot*1e6:.3f} us")
        for language, cmd in workers.items():
            with connect(cmd, n) as (proc, mode):
                if mode != MODES[language]:
                    raise RuntimeError(f"{language} build rejected: {mode}; expected {MODES[language]}")
                timed_batch(proc, "go 1")
                value = float(exchange(proc, "sum"))
            assert_close(value, reference)
            print(f"{n:>7}  {language:6}  {value:.17g}  rel.err={error(value, reference):.3e}")
    return references


def benchmark(workers, references, output):
    rows = []
    for n in SIZES[1:]:
        for language, cmd in workers.items():
            terms = 3_000_000 if language == "Python" else 180_000_000
            reps = terms // n
            with connect(cmd, n) as (proc, mode):
                if mode != MODES[language]:
                    raise RuntimeError(f"unexpected build mode: {mode}")
                overhead = median(timed_batch(proc, "ping") for _ in range(10))
                for _ in range(3):
                    timed_batch(proc, f"go {reps}")
                expected_sum = references[n] * reps
                for i in range(10):
                    elapsed = timed_batch(proc, f"go {reps}")
                    checksum = float(exchange(proc, "sum"))
                    assert_close(checksum, expected_sum)
                    rows.append((n, language, 1 + i//5, 1 + i%5, reps,
                                 elapsed, elapsed/reps, overhead, checksum))
                print(f"N={n:>7} {language:6} reps={reps:>5} checksum={checksum:.12g}",
                      flush=True)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "rounds.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["n", "language", "group", "round", "reps",
                         "batch_s", "dot_s", "ping_s", "checksum"])
        writer.writerows(rows)
    return summarize(output)


def summarize(output):
    with (output / "rounds.csv").open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    summary = []
    print("N       Lang      A5 us      B5 us     All10 us    Speedup    Delta")
    for n in SIZES[1:]:
        for language in MODES:
            case = [r for r in rows if int(r["n"]) == n and r["language"] == language]
            a, b = [[float(r["dot_s"])*1e6 for r in case if int(r["group"]) == g]
                    for g in (1, 2)]
            first, second, all_rounds = median(a), median(b), median(a + b)
            if language == "Python":
                baseline = first
            speedup, delta = baseline / first, abs(second - first) / first * 100
            summary.append((n, language, first, second, all_rounds, speedup, delta))
            print(f"{n:7} {language:6} {first:10.3f} {second:10.3f} {all_rounds:11.3f}"
                  f" {speedup:9.2f}x {delta:7.2f}%")
    with (output / "summary.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["n", "language", "A5_us", "B5_us", "All10_us",
                         "speedup_A", "delta_pct"])
        writer.writerows(summary)
    return all(row[-1] < 5.0 for row in summary)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--c-exe", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--table", action="store_true")
    args = parser.parse_args()
    if args.table:
        return 0 if summarize(args.output) else 2
    if args.build:
        compile_workers()
    workers = commands(args.c_exe.resolve() if args.c_exe else None)
    references = verify(workers)
    if not args.check_only:
        return 0 if benchmark(workers, references, args.output) else 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, sp.CalledProcessError) as exc:
        sys.exit(f"FAIL: {exc}")
