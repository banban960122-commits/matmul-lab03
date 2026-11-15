extern "C" __global__
void matmul_kernel(const signed char *a, const signed char *b, int *c, int n) {
    int p = blockIdx.x * blockDim.x + threadIdx.x;
    if (p >= n*n) return;
    int i = p/n, j = p%n;
    int sum = 0;
    for (int k = 0; k < n; ++k)
        sum += (int)a[i*n+k] * b[k*n+j];
    c[p] = sum;
}

#ifndef __CUDACC_RTC__
#include <musa_runtime.h>
#include <cstdio>
#include <cstdlib>

static void check(musaError_t status) {
    if (status != musaSuccess) {
        std::fprintf(stderr, "%s\n", musaGetErrorString(status));
        std::exit(EXIT_FAILURE);
    }
}

int main() {
    constexpr int N = 3, threads = 32;
    constexpr int blocks = (N*N + threads - 1)/threads;
    signed char a[] = {1,2,3,4,5,6,7,8,9}, b[] = {9,8,7,6,5,4,3,2,1};
    int c[N*N], expected[] = {30,24,18,84,69,54,138,114,90};
    signed char *da, *db;
    int *dc;
    check(musaMalloc((void **)&da, sizeof a));
    check(musaMalloc((void **)&db, sizeof b));
    check(musaMalloc((void **)&dc, sizeof c));
    for (int test = 0; test < 2; ++test) {
        if (test) {
            for (int p = 0; p < N*N; ++p) {
                a[p] = -128;
                b[p] = p/N == 1 ? 127 : -128;
                expected[p] = 16512;
            }
        }
        check(musaMemcpy(da, a, sizeof a, musaMemcpyHostToDevice));
        check(musaMemcpy(db, b, sizeof b, musaMemcpyHostToDevice));
        matmul_kernel<<<blocks, threads>>>(da, db, dc, N);
        check(musaGetLastError());
        check(musaDeviceSynchronize());
        check(musaMemcpy(c, dc, sizeof c, musaMemcpyDeviceToHost));
        for (int p = 0; p < N*N; ++p) {
            if (c[p] != expected[p]) return EXIT_FAILURE;
            if (!test) std::printf("%d%c", c[p], p%N == N-1 ? '\n' : ' ');
        }
    }
    check(musaFree(dc));
    check(musaFree(db));
    check(musaFree(da));
    std::puts("PASS: 9/9 fixed + 9/9 signed boundary");
}
#endif
