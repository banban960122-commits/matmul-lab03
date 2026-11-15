# 矩阵乘法四层实现

四份主源码为 matmul.c、matmul.s、matmul.v、matmul.cu。matmul.s 来自 GCC 15.2.0 x86-64 Windows UCRT，使用 AT&T 语法。tb_matmul.v 为 Icarus 仿真测试平台。matmul.mu 为 MUSA Runtime API 静态迁移对照。

## 固定用例与边界

A 为 1 到 9，B 为 9 到 1，按行填充。预期结果各行为 30 24 18、84 69 54、138 114 90。边界用例取有符号 8 位极值，9 项输出均为 16512。

## 复现

```powershell
gcc -O0 matmul.c -o c.exe
gcc -O0 -DMATMUL_ONLY -S matmul.c -o matmul.s
gcc -O2 -DUSE_ASSEMBLY matmul.c matmul.s -o asm.exe
.\c.exe
.\asm.exe
iverilog -g2012 -Wall -s tb_matmul -o matmul.vvp matmul.v tb_matmul.v
vvp matmul.vvp
nvcc -O2 matmul.cu -o cuda.exe
.\cuda.exe
```

本次 CUDA 实测使用 Windows CUDA Driver API 与 NVRTC 12.9。从同一份 matmul.cu 即时编译核函数。设置 NVRTC_BIN 为 NVIDIA NVRTC DLL 所在目录，再运行 python run_cuda.py。RTX 5060 使用 compute_120 编译目标。MUSA 文件仅做静态比较。

N=256 对照实验使用 gcc -O2 bench256.c -o bench256.exe。bench256.exe reference256.bin 检查两种 CPU 循环并生成参考输出。python run_cuda.py reference256.bin 运行同一 CUDA 核函数并逐项比较。
