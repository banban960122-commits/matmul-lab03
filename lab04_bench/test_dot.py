"""Exercise the five assigned boundaries through all three executables."""

import math
from pathlib import Path
import subprocess as sp
from tempfile import TemporaryDirectory
import unittest

from benchmark import ROOT, commands, connect, exchange, vector_args
from gen_data import write_vector


class TestDot(unittest.TestCase):
    def exercise(self, a, b, expected):
        with TemporaryDirectory(dir=ROOT) as temp:
            paths = [Path(temp) / "a.bin", Path(temp) / "b.bin"]
            for path, vector in zip(paths, (a, b)):
                write_vector(path, vector)
            for lang, command in commands().items():
                with self.subTest(language=lang):
                    args = vector_args(len(a), len(b), paths)
                    if expected is None:
                        process = sp.run(command + args, capture_output=True, text=True,
                                         timeout=5)
                        self.assertEqual(process.returncode, 2)
                        self.assertIn("length mismatch", process.stderr)
                    else:
                        with connect(command, len(a), len(b), paths) as (proc, _):
                            self.assertEqual(exchange(proc, "go 1"), "DONE")
                            result = float(exchange(proc, "sum"))
                        if math.isnan(expected):
                            self.assertTrue(math.isnan(result))
                        else:
                            self.assertEqual(result, expected)

    def test_01_empty(self):
        self.exercise([], [], 0.0)

    def test_02_single(self):
        self.exercise([2.0], [3.0], 6.0)

    def test_03_mismatch(self):
        self.exercise([1.0, 2.0], [3.0], None)

    def test_04_zeros(self):
        self.exercise([0.0, 0.0, 0.0], [0.0, 0.0, 0.0], 0.0)

    def test_05_nan(self):
        self.exercise([1.0, math.nan], [2.0, 3.0], math.nan)


if __name__ == "__main__":
    unittest.main(verbosity=2)
