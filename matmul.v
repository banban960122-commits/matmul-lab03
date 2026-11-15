`timescale 1ns/1ps
module matmul #(parameter N = 3, IN = 8, OUT = 32)(
    input  wire [N*IN-1:0] a_col, b_row,
    input  wire [N*N*OUT-1:0] previous,
    output wire [N*N*OUT-1:0] next_sum
);
    genvar i, j;
    generate
        for (i=0; i<N; i=i+1) begin : rows
            for (j=0; j<N; j=j+1) begin : cols
                wire signed [IN-1:0] a, b;
                wire signed [2*IN-1:0] product;
                wire signed [OUT-1:0] partial;
                assign a = a_col[i*IN +: IN];
                assign b = b_row[j*IN +: IN];
                assign product = a * b;
                assign partial = previous[(i*N+j)*OUT +: OUT];
                assign next_sum[(i*N+j)*OUT +: OUT] = partial + product;
            end
        end
    endgenerate
endmodule

module matmul_matrix #(parameter N=3, IN=8, OUT=32)(
    input wire clk, rst, start,
    input wire [N*N*IN-1:0] a, b,
    output reg [N*N*OUT-1:0] c,
    output reg busy, done
);
    localparam K_BITS = N > 1 ? $clog2(N) : 1;
    reg [K_BITS-1:0] k;
    wire [N*IN-1:0] a_col, b_row;
    wire [N*N*OUT-1:0] next_sum;
    genvar row, col, step;
    generate
        for (row=0; row<N; row=row+1) begin : select_a
            wire [N*IN-1:0] candidates;
            for (step=0; step<N; step=step+1) begin : gather
                assign candidates[step*IN +: IN] = a[(row*N+step)*IN +: IN];
            end
            assign a_col[row*IN +: IN] = candidates >> (k*IN);
        end
        for (col=0; col<N; col=col+1) begin : select_b
            wire [N*IN-1:0] candidates;
            for (step=0; step<N; step=step+1) begin : gather
                assign candidates[step*IN +: IN] = b[(step*N+col)*IN +: IN];
            end
            assign b_row[col*IN +: IN] = candidates >> (k*IN);
        end
    endgenerate
    matmul #(N, IN, OUT) mac(a_col, b_row, c, next_sum);

    // Keep a and b stable from start until done.
    always @(posedge clk) begin
        if (rst) begin
            k <= 0;
            c <= 0;
            busy <= 0;
            done <= 0;
        end else begin
            done <= 0;
            if (!busy && start) begin
                k <= 0;
                c <= 0;
                busy <= 1;
            end else if (busy) begin
                c <= next_sum;
                if (k == N-1) begin
                    busy <= 0;
                    done <= 1;
                end else begin
                    k <= k + 1'b1;
                end
            end
        end
    end
endmodule
