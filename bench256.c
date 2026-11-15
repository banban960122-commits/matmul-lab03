#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

enum { N=256, COUNT=N*N, TRIALS=21 };
static int8_t a[COUNT], b[COUNT];
static int32_t c[COUNT], baseline[COUNT];

__attribute__((noipa))
static void ijk(void) {
    for (int i=0; i<N; ++i)
        for (int j=0; j<N; ++j) {
            int32_t sum=0;
            for (int k=0; k<N; ++k) sum += a[i*N+k]*b[k*N+j];
            c[i*N+j]=sum;
        }
}

__attribute__((noipa))
static void ikj(void) {
    memset(c, 0, sizeof c);
    for (int i=0; i<N; ++i)
        for (int k=0; k<N; ++k) {
            const int32_t x=a[i*N+k];
            for (int j=0; j<N; ++j) c[i*N+j] += x*b[k*N+j];
        }
}

static int order(const void *a, const void *b) {
    double x=*(const double *)a, y=*(const double *)b;
    return (x>y)-(x<y);
}

int main(int argc, char **argv) {
    if (argc != 2) return 1;
    for (int p=0; p<COUNT; ++p) {
        a[p]=(p*7+3)%17-8;
        b[p]=(p*5+1)%19-9;
    }
    ijk();
    memcpy(baseline, c, sizeof c);
    ikj();
    if (memcmp(baseline, c, sizeof c)) return 2;
    LARGE_INTEGER freq, start, stop;
    QueryPerformanceFrequency(&freq);
    double ms[2][TRIALS];
    for (int t=0; t<TRIALS; ++t) {
        QueryPerformanceCounter(&start);
        ijk();
        QueryPerformanceCounter(&stop);
        ms[0][t]=1000.0*(stop.QuadPart-start.QuadPart)/freq.QuadPart;
        QueryPerformanceCounter(&start);
        ikj();
        QueryPerformanceCounter(&stop);
        ms[1][t]=1000.0*(stop.QuadPart-start.QuadPart)/freq.QuadPart;
    }
    for (int i=0; i<2; ++i) qsort(ms[i], TRIALS, sizeof(double), order);
    printf("N=256, C i-j-k median: %.3f ms\n", ms[0][TRIALS/2]);
    printf("N=256, C i-k-j median: %.3f ms\n", ms[1][TRIALS/2]);
    FILE *output=fopen(argv[1], "wb");
    if (!output) return 3;
    size_t written=fwrite(c, sizeof c[0], COUNT, output);
    return fclose(output) || written != COUNT;
}
