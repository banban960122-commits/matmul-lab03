`timescale 1ns/1ps
module tb_matmul;
    localparam N=3, IN=8, OUT=32;
    reg clk=0, rst=1, start=0;
    reg [N*N*IN-1:0] a, b;
    wire [N*N*OUT-1:0] c;
    wire busy, done;
    reg signed [OUT-1:0] expected[0:8], actual;
    integer j, p, cycles;
    matmul_matrix dut(clk, rst, start, a, b, c, busy, done);
    always #5 clk=~clk;

    task run_case;
        input print_matrix;
        begin
            @(negedge clk);
            start=1;
            @(negedge clk);
            start=0;
            cycles=0;
            while (!done && cycles<N) begin
                @(negedge clk);
                cycles=cycles+1;
            end
            if (done !== 1 || busy !== 0 || cycles != N)
                $fatal(1, "handshake or cycle count failed");
            for (p=0; p<N*N; p=p+1) begin
                actual = c[p*OUT +: OUT];
                if (actual !== expected[p])
                    $fatal(1, "index %0d: %0d != %0d", p, actual, expected[p]);
                if (print_matrix) begin
                    $write("%0d", actual);
                    if (p%N == N-1) $write("\n");
                    else $write(" ");
                end
            end
        end
    endtask

    initial begin
        @(negedge clk);
        rst=0;
        for (j=0; j<N*N; j=j+1) begin
            a[j*IN +: IN]=j+1;
            b[j*IN +: IN]=9-j;
        end
        expected[0]=30;  expected[1]=24;  expected[2]=18;
        expected[3]=84;  expected[4]=69;  expected[5]=54;
        expected[6]=138; expected[7]=114; expected[8]=90;
        run_case(1);
        for (j=0; j<N*N; j=j+1) begin
            a[j*IN +: IN] = 8'sh80;
            b[j*IN +: IN] = j/N == 1 ? 8'sh7f : 8'sh80;
            expected[j] = 32'sd16512;
        end
        run_case(0);
        $display("PASS: 9/9 fixed + 9/9 signed boundary");
        $display("PASS: done after 3 MAC cycles");
        $finish(0);
    end
endmodule
