# Codex 第一轮核心草稿

将两个 float64 向量逐项相乘后用一个累加器求和。Python 用 zip 顺序遍历，主要成本在解释器执行浮点运算。C 用连续数组和简单循环，主要依赖 -O2。Rust 用迭代器，release 可消除迭代器抽象的大部分开销。读取数据后保持工作进程运行，外层用 perf_counter 计一次请求，工作进程输出结果用于校验。

```python
def dot(a, b):
    total = 0.0
    for x, y in zip(a, b):
        total += x * y
    return total
```

```c
#include <stddef.h>

double dot(const double *a, const double *b, size_t n) {
    double total = 0.0;
    for (size_t i = 0; i < n; ++i) {
        total += a[i] * b[i];
    }
    return total;
}
```

```rust
fn dot(a: &[f64], b: &[f64]) -> f64 {
    a.iter().zip(b.iter()).fold(0.0, |sum, (&x, &y)| sum + x * y)
}
```

```python
from statistics import median
from time import perf_counter

def sample(worker):
    # worker is already started and has loaded the binary files.
    for _ in range(3):
        worker.request("go 1")
    times, checksum = [], 0.0
    for _ in range(10):
        start = perf_counter()
        worker.request("go 1")
        times.append(perf_counter() - start)
        checksum += float(worker.request("sum"))
    return median(times[:5]), median(times[5:]), median(times), checksum
```
