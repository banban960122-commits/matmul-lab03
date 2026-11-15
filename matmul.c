#include <stdint.h>

enum { N = 3 };
#ifndef USE_ASSEMBLY
__attribute__((noipa))
void matmul(const int8_t *restrict a, const int8_t *restrict b,
            int32_t *restrict c) {
    for (int i = 0; i < N; ++i)
        for (int j = 0; j < N; ++j) {
            c[i*N+j] = 0;
            for (int k = 0; k < N; ++k)
                c[i*N+j] += (int32_t)a[i*N+k] * b[k*N+j];
        }
}
#else
void matmul(const int8_t *a, const int8_t *b, int32_t *c);
#endif

#ifndef MATMUL_ONLY
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

int main(int argc, char **argv) {
    int8_t a[] = {1,2,3,4,5,6,7,8,9};
    int8_t b[] = {9,8,7,6,5,4,3,2,1};
    int32_t c[N*N], expected[] = {30,24,18,84,69,54,138,114,90};
    if (argc == 2 && strcmp(argv[1], "bench") == 0) {
        const int reps = 5000000;
        clock_t start = clock();
        for (int n = 0; n < reps; ++n) matmul(a, b, c);
        printf("%.2f ns/call, check=%" PRId32 "\n",
               1e9 * (clock()-start) / CLOCKS_PER_SEC / reps, c[8]);
        return c[8] != 90;
    }
    matmul(a, b, c);
    for (int p = 0; p < N*N; ++p) {
        if (c[p] != expected[p]) return 1;
        printf("%" PRId32 "%c", c[p], p%N == N-1 ? '\n' : ' ');
    }
    for (int p = 0; p < N*N; ++p) {
        a[p] = INT8_MIN;
        b[p] = p/N == 1 ? INT8_MAX : INT8_MIN;
    }
    matmul(a, b, c);
    for (int p = 0; p < N*N; ++p)
        if (c[p] != INT32_C(16512)) return 1;
    puts("PASS: 9/9 fixed + 9/9 signed boundary");
    return 0;
}
#endif
