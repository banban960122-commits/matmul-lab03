#include <float.h>
#include <inttypes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    double *values;
    size_t length;
} Vector;

static int parse_size(const char *text, size_t *result) {
    char *end;
    if (text[0] < '0' || text[0] > '9') return 0;
    uintmax_t n = strtoumax(text, &end, 10);
    if (*end != '\0' || n > SIZE_MAX / sizeof(double)) return 0;
    *result = (size_t)n;
    return 1;
}

static int read_vector(const char *path, Vector *v) {
    FILE *file = fopen(path, "rb");
    if (!file) return 0;
    size_t bytes = v->length * sizeof(double);
    v->values = malloc(bytes ? bytes : 1);
    int ok = v->values && fread(v->values, 1, bytes, file) == bytes
             && fgetc(file) == EOF && !ferror(file);
    fclose(file);
    if (ok) {
        unsigned char *raw = (unsigned char *)v->values;
        for (size_t i = 0; i < bytes; i += 8) {
            uint64_t bits = 0;
            for (size_t j = 0; j < 8; ++j)
                bits |= (uint64_t)raw[i + j] << (8 * j);
            memcpy(raw + i, &bits, sizeof(bits));
        }
    }
    return ok;
}

static double dot(Vector a, Vector b) {
    if (a.length != b.length) return NAN;
    double total = 0.0;
    for (size_t i = 0; i < a.length; ++i)
        total += a.values[i] * b.values[i];
    return total;
}

int main(int argc, char **argv) {
    Vector a = {0}, b = {0};
    if (sizeof(double) != 8 || DBL_MANT_DIG != 53 || DBL_MAX_EXP != 1024)
        return 2;
    if (argc != 5 || !parse_size(argv[1], &a.length)
                  || !parse_size(argv[2], &b.length)) {
        fputs("invalid arguments\n", stderr);
        return 2;
    }
    if (a.length != b.length) {
        fputs("length mismatch\n", stderr);
        return 2;
    }
    if (!read_vector(argv[3], &a) || !read_vector(argv[4], &b)) {
        fputs("invalid binary vector\n", stderr);
        free(a.values);
        free(b.values);
        return 2;
    }
#ifdef __OPTIMIZE__
    puts("READY optimized");
#else
    puts("READY unoptimized");
#endif
    fflush(stdout);
    double checksum = 0.0;
    char line[80];
    /* Reloading a volatile function pointer prevents hoisting repeated calls. */
    double (*volatile kernel)(Vector, Vector) = dot;
    int status = 0;
    while (fgets(line, sizeof(line), stdin)) {
        line[strcspn(line, "\r\n")] = '\0';
        if (strncmp(line, "go ", 3) == 0) {
            size_t reps;
            if (!parse_size(line + 3, &reps) || !reps) {
                status = 2;
                break;
            }
            checksum = 0.0;
            for (size_t i = 0; i < reps; ++i) checksum += kernel(a, b);
            puts("DONE");
        } else if (strcmp(line, "sum") == 0) {
            printf("%.17g\n", checksum);
        } else if (strcmp(line, "ping") == 0) {
            puts("DONE");
        } else {
            status = 2;
            break;
        }
        fflush(stdout);
    }
    if (status) fputs("invalid command\n", stderr);
    free(a.values);
    free(b.values);
    return status;
}
