# 第 04 讲三语言点积基准

本实验计算两个等长 float64 向量的原始点积，示例 `[1, 2, 3] · [4, 5, 6]` 的结果为 32。注意力使用的缩放因子可以在点积之后统一应用。本次比较重复调用点积核的耗时。

实验环境为 Python 3.12.14、GCC 15.2.0、rustc / Cargo 1.100.0，源码仅使用标准库。需要将 Python、GCC 和 Cargo 加入 PATH。

```text
python gen_data.py
python benchmark.py --build --output reproduced
python test_dot.py
python benchmark.py --table --output results
```

每个规模生成一对小端 float64 二进制向量，种子为 20261118 + N。三种实现先加载数据并发送 READY，外层 Python 再发起预热与计时。每轮只计 GO 指令至 DONE 的往返，校验和读取在计时窗口外。每轮按批内调用次数求单次摊销时间。

`results/rounds.csv` 是本机全部 90 条正式轮次记录。`results/summary.csv` 保存 A 组 5 轮中位数、B 组 5 轮中位数、合并 10 轮中位数、A 组加速倍数及 A/B 偏差。若任一格偏差达到 5%，基准仍保留 CSV 并以退出码 2 结束。

提示词见 `prompts.md`，第一轮生成的核心草稿见 `draft_v1.md`。用于构建和计时的是目录中的最终代码。

## 本机重复运行

自动调度下的完整运行对照在 results/repeat1_automatic_summary.csv 和 results/repeat2_automatic_summary.csv。正式结果固定到 Windows 逻辑处理器 15，以第二次完整运行作为主表。

```powershell
[System.Diagnostics.Process]::GetCurrentProcess().ProcessorAffinity = [IntPtr]32768
python benchmark.py --build --output repeat_a
python benchmark.py --output repeat_b
```

亲和掩码 0x8000 对应本机逻辑处理器 15，复现时应按机器的可用处理器设置。results/repeat_compare.csv 对照两次完整运行的 10 轮中位数。repeat1/2 的逐轮记录以同名前缀保存，run_notes.json 标注主表与最大偏差。
