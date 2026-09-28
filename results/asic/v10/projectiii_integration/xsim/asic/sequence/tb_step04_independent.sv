// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : tb_step04_independent.sv
// Module  : tb_step04_independent
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_step04_independent;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start = 1'b0;
    reg [1:0] run_id = 0;
    reg inject = 1'b0;
    reg inject_pending = 1'b0;
    integer accepted_count = 0;
    wire busy, done, pass, fail;
    wire [8:0] error_count;
    wire [2:0] first_fail_phase;
    wire [5:0] first_fail_addr;
    wire [7:0] first_fail_expected, first_fail_actual;
    wire req_valid, req_ready, req_write, rd_valid;
    wire [5:0] req_addr;
    wire [7:0] req_wdata, ram_rd_data;
    wire [7:0] observed_rd_data = inject_pending ? (ram_rd_data ^ 8'h01) : ram_rd_data;

    always #10 clk = ~clk;
    mbist_asic_top dut (
        .clk(clk), .rst_n(rst_n), .start(start), .busy(busy),
        .done(done), .pass(pass), .fail(fail), .error_count(error_count),
        .first_fail_phase(first_fail_phase), .first_fail_addr(first_fail_addr),
        .first_fail_expected(first_fail_expected), .first_fail_actual(first_fail_actual),
        .req_valid(req_valid), .req_ready(req_ready), .req_write(req_write),
        .req_addr(req_addr), .req_wdata(req_wdata),
        .rd_valid(rd_valid), .rd_data(observed_rd_data)
    );
    single_port_sync_ram ram (
        .clk(clk), .rst_n(rst_n), .req_valid(req_valid),
        .req_ready(req_ready), .req_write(req_write), .req_addr(req_addr),
        .req_wdata(req_wdata), .rd_valid(rd_valid), .rd_data(ram_rd_data)
    );
    march_transaction_checker u_checker (
        .clk(clk), .rst_n(rst_n), .start(start), .run_id(run_id),
        .req_valid(req_valid), .req_ready(req_ready), .req_write(req_write),
        .req_addr(req_addr), .req_wdata(req_wdata),
        .rd_valid(rd_valid), .rd_data(observed_rd_data),
        .done(done), .pass(pass), .fail(fail), .error_count(error_count),
        .first_fail_phase(first_fail_phase), .first_fail_addr(first_fail_addr),
        .first_fail_expected(first_fail_expected), .first_fail_actual(first_fail_actual)
    );

    // One deterministic response perturbation in run 2. This is a checker
    // calibration stimulus, not the Step 5 faulty memory model.
    always @(posedge clk) begin
        if (!rst_n || start) begin
            accepted_count <= 0;
            inject_pending <= 1'b0;
        end else begin
            inject_pending <= inject && req_valid && req_ready &&
                              !req_write && accepted_count == 206;
            if (req_valid && req_ready)
                accepted_count <= accepted_count + 1;
        end
    end

    task automatic launch(input [1:0] id, input reg inject_one);
        begin
            @(negedge clk);
            run_id = id;
            inject = inject_one;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
        end
    endtask

    initial begin
        repeat (3) @(negedge clk);
        rst_n = 1'b1;
        launch(1, 1'b0);
        repeat (100) @(negedge clk);
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;
        wait (done);
        repeat (2) @(negedge clk);
        launch(2, 1'b1);
        wait (done);
        repeat (2) @(negedge clk);
        $display("STEP04_PASS independent_checker_normal_and_diagnostic");
        $finish;
    end

    initial begin
        #100000;
        $display("CHECKER_FAIL code=5 run=%0d request=%0d cycle=global_timeout",
                 run_id, accepted_count);
        $fatal(1, "Global timeout");
    end
endmodule
