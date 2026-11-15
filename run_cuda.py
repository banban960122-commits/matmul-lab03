"""Compile the submitted kernel with NVRTC and run it on an NVIDIA GPU."""
import ctypes as ct
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
dll = Path(os.environ['NVRTC_BIN'])
scope = os.add_dll_directory(str(dll))
os.environ['PATH'] = str(dll) + os.pathsep + os.environ['PATH']
nvrtc = ct.CDLL(str(dll / 'nvrtc64_120_0.dll'))
cuda = ct.WinDLL('nvcuda.dll')
pointer = ct.c_void_p
u32 = ct.c_uint
device_ptr = ct.c_uint64

def check(status):
    if status:
        raise RuntimeError(f"CUDA / NVRTC status {status}")

program = pointer()
source = (root / 'matmul.cu').read_bytes()
check(nvrtc.nvrtcCreateProgram(ct.byref(program), source, b'matmul.cu', 0, None, None))
options = (ct.c_char_p * 1)(b'--gpu-architecture=compute_120')
status = nvrtc.nvrtcCompileProgram(program, 1, options)
if status:
    log_size = ct.c_size_t()
    nvrtc.nvrtcGetProgramLogSize(program, ct.byref(log_size))
    log = ct.create_string_buffer(log_size.value)
    nvrtc.nvrtcGetProgramLog(program, log)
    raise RuntimeError(log.value.decode())
length = ct.c_size_t()
check(nvrtc.nvrtcGetPTXSize(program, ct.byref(length)))
ptx = ct.create_string_buffer(length.value)
check(nvrtc.nvrtcGetPTX(program, ptx))
check(nvrtc.nvrtcDestroyProgram(ct.byref(program)))

check(cuda.cuInit(0))
device = ct.c_int()
check(cuda.cuDeviceGet(ct.byref(device), 0))
context = pointer()
check(cuda.cuDevicePrimaryCtxRetain(ct.byref(context), device))
check(cuda.cuCtxSetCurrent(context))
module, kernel = pointer(), pointer()
check(cuda.cuModuleLoadData(ct.byref(module), ptx))
check(cuda.cuModuleGetFunction(ct.byref(kernel), module, b'matmul_kernel'))
launch = cuda.cuLaunchKernel
launch.argtypes = [pointer, *([u32] * 7), pointer, ct.POINTER(pointer), pointer]
name = ct.create_string_buffer(128)
check(cuda.cuDeviceGetName(name, len(name), device))
major, minor = ct.c_int(), ct.c_int()
check(nvrtc.nvrtcVersion(ct.byref(major), ct.byref(minor)))
print(f"GPU: {name.value.decode()}")
print(f"NVRTC {major.value}.{minor.value}  |  grid=1, block=32, active=9")

def run_case(a, b, expected, show):
    da, db, dc = device_ptr(), device_ptr(), device_ptr()
    result = (ct.c_int32 * 9)()
    sizes = [ct.sizeof(a), ct.sizeof(b), ct.sizeof(result)]
    for addr, size in zip((da, db, dc), sizes):
        check(cuda.cuMemAlloc_v2(ct.byref(addr), ct.c_size_t(size)))
    try:
        check(cuda.cuMemcpyHtoD_v2(da, a, ct.c_size_t(sizes[0])))
        check(cuda.cuMemcpyHtoD_v2(db, b, ct.c_size_t(sizes[1])))
        n = ct.c_int(3)
        args = (pointer * 4)(*(ct.addressof(arg) for arg in (da, db, dc, n)))
        check(launch(kernel, 1, 1, 1, 32, 1, 1, 0, None, args, None))
        check(cuda.cuCtxSynchronize())
        check(cuda.cuMemcpyDtoH_v2(result, dc, ct.c_size_t(sizes[2])))
        assert list(result) == expected, list(result)
        if show:
            for i in range(0, 9, 3):
                print(*result[i:i+3])
    finally:
        for addr in (da, db, dc):
            check(cuda.cuMemFree_v2(addr))

def benchmark_256(reference):
    from statistics import median
    from time import perf_counter
    n = ct.c_int(256)
    count = n.value ** 2
    a = (ct.c_int8 * count)(*((p*7+3)%17-8 for p in range(count)))
    b = (ct.c_int8 * count)(*((p*5+1)%19-9 for p in range(count)))
    result = (ct.c_int32 * count)()
    da, db, dc = device_ptr(), device_ptr(), device_ptr()
    sizes = [ct.sizeof(a), ct.sizeof(b), ct.sizeof(result)]
    for addr, size in zip((da, db, dc), sizes):
        check(cuda.cuMemAlloc_v2(ct.byref(addr), ct.c_size_t(size)))
    args = (pointer * 4)(*(ct.addressof(arg) for arg in (da, db, dc, n)))

    def once():
        begin = perf_counter()
        check(cuda.cuMemcpyHtoD_v2(da, a, ct.c_size_t(sizes[0])))
        check(cuda.cuMemcpyHtoD_v2(db, b, ct.c_size_t(sizes[1])))
        check(launch(kernel, count // 32, 1, 1, 32, 1, 1, 0, None, args, None))
        check(cuda.cuCtxSynchronize())
        check(cuda.cuMemcpyDtoH_v2(result, dc, ct.c_size_t(sizes[2])))
        return (perf_counter()-begin)*1000

    try:
        for _ in range(3):
            once()
        timing = median(once() for _ in range(21))
        assert bytes(result) == Path(reference).read_bytes()
        print(f"N=256, CUDA transfers + kernel median: {timing:.3f} ms")
        print("PASS: 65536 / 65536 compared with both CPU loops")
    finally:
        for addr in (da, db, dc):
            check(cuda.cuMemFree_v2(addr))


array = ct.c_int8 * 9
try:
    run_case(array(*range(1,10)), array(*range(9,0,-1)),
             [30,24,18,84,69,54,138,114,90], True)
    run_case(array(*([-128]*9)), array(*([-128]*3+[127]*3+[-128]*3)),
             [16512]*9, False)
    print("PASS: 9/9 fixed + 9/9 signed boundary")
    if len(sys.argv) == 2:
        benchmark_256(sys.argv[1])
finally:
    check(cuda.cuModuleUnload(module))
    check(cuda.cuDevicePrimaryCtxRelease_v2(device))
