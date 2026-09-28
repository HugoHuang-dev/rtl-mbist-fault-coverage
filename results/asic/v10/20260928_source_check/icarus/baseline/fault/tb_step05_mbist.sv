// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : tb_step05_mbist.sv
// Module  : tb_step05_mbist
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_step05_mbist;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start = 1'b0;
    reg [2:0] fault_type;
    reg [5:0] fault_addr;
    reg [2:0] fault_bit;
    reg [7:0] mask;
    integer type_arg, addr_arg, bit_arg;
    integer expected_errors, expected_activations;
    reg [2:0] expected_first_phase;
    reg [7:0] expected_first_value, expected_first_actual;

    wire busy, done, pass, fail, fault_activated;
    wire [8:0] error_count;
    wire [15:0] activation_count;
    wire [2:0] first_fail_phase;
    wire [5:0] first_fail_addr;
    wire [7:0] first_fail_expected, first_fail_actual;
    wire req_valid, req_ready, req_write, rd_valid;
    wire [5:0] req_addr;
    wire [7:0] req_wdata, rd_data;

    always #10 clk = ~clk;
    mbist_top dut (
        .clk(clk), .rst_n(rst_n), .start(start), .busy(busy),
        .done(done), .pass(pass), .fail(fail), .error_count(error_count),
        .first_fail_phase(first_fail_phase), .first_fail_addr(first_fail_addr),
        .first_fail_expected(first_fail_expected), .first_fail_actual(first_fail_actual),
        .req_valid(req_valid), .req_ready(req_ready), .req_write(req_write),
        .req_addr(req_addr), .req_wdata(req_wdata),
        .rd_valid(rd_valid), .rd_data(rd_data)
    );
    faulty_memory ram (
        .clk(clk), .rst_n(rst_n), .experiment_clear(1'b0), .req_valid(req_valid),
        .req_ready(req_ready), .req_write(req_write), .req_addr(req_addr),
        .req_wdata(req_wdata), .rd_valid(rd_valid), .rd_data(rd_data),
        .fault_type(fault_type), .fault_addr(fault_addr), .fault_bit(fault_bit),
        .fault_activated(fault_activated), .activation_count(activation_count)
    );
    march_transaction_checker u_checker (
        .clk(clk), .rst_n(rst_n), .start(start), .run_id(2'd1),
        .req_valid(req_valid), .req_ready(req_ready), .req_write(req_write),
        .req_addr(req_addr), .req_wdata(req_wdata),
        .rd_valid(rd_valid), .rd_data(rd_data),
        .done(done), .pass(pass), .fail(fail), .error_count(error_count),
        .first_fail_phase(first_fail_phase), .first_fail_addr(first_fail_addr),
        .first_fail_expected(first_fail_expected), .first_fail_actual(first_fail_actual)
    );
    fault_reference_monitor reference_monitor (
        .clk(clk), .rst_n(rst_n), .experiment_clear(1'b0), .req_valid(req_valid),
        .req_ready(req_ready), .req_write(req_write), .req_addr(req_addr),
        .req_wdata(req_wdata), .rd_valid(rd_valid), .rd_data(rd_data),
        .fault_type(fault_type), .fault_addr(fault_addr), .fault_bit(fault_bit),
        .fault_activated(fault_activated), .activation_count(activation_count)
    );

    initial begin
        type_arg = 0;
        addr_arg = 7;
        bit_arg = 2;
        if ($value$plusargs("FAULT_TYPE=%d", type_arg)) begin end
        if ($value$plusargs("FAULT_ADDR=%d", addr_arg)) begin end
        if ($value$plusargs("FAULT_BIT=%d", bit_arg)) begin end
        if (type_arg < 0 || type_arg > 4 || addr_arg < 0 || addr_arg > 63 ||
            bit_arg < 0 || bit_arg > 7)
            $fatal(1, "Invalid fault configuration");
        fault_type = type_arg[2:0];
        fault_addr = addr_arg[5:0];
        fault_bit = bit_arg[2:0];
        mask = 8'h01 << fault_bit;
        expected_errors = 0;
        expected_activations = 0;
        expected_first_phase = 0;
        expected_first_value = 0;
        expected_first_actual = 0;
        case (fault_type)
            3'd1: begin // SA0: M1 writes 1; M2 reads the stuck 0.
                expected_errors = 2; expected_activations = 2;
                expected_first_phase = 2; expected_first_value = 8'hff;
                expected_first_actual = 8'hff & ~mask;
            end
            3'd2: begin // SA1: M0 writes 0; M1 reads the stuck 1.
                expected_errors = 3; expected_activations = 3;
                expected_first_phase = 1; expected_first_value = 8'h00;
                expected_first_actual = mask;
            end
            3'd3: begin // Rising TF: M1 0->1 fails; M2 reads 0.
                expected_errors = 2; expected_activations = 2;
                expected_first_phase = 2; expected_first_value = 8'hff;
                expected_first_actual = 8'hff & ~mask;
            end
            3'd4: begin // Falling TF: M2 1->0 fails; M3 reads 1.
                expected_errors = 2; expected_activations = 2;
                expected_first_phase = 3; expected_first_value = 8'h00;
                expected_first_actual = mask;
            end
            default: begin end
        endcase

        repeat (3) @(negedge clk);
        rst_n = 1'b1;
        @(negedge clk);
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;
        wait (done);
        @(negedge clk);
        if (fault_activated !== (fault_type != 0) ||
            activation_count !== expected_activations[15:0])
            $fatal(1, "FAULT_MBIST_FAIL activation type=%0d got=%b/%0d expected=%0d",
                   fault_type, fault_activated, activation_count, expected_activations);
        if (error_count !== expected_errors[8:0] ||
            fail !== (expected_errors != 0) || pass !== (expected_errors == 0))
            $fatal(1, "FAULT_MBIST_FAIL detection type=%0d errors=%0d expected=%0d",
                   fault_type, error_count, expected_errors);
        if (fault_type != 0 &&
            (first_fail_phase !== expected_first_phase ||
             first_fail_addr !== fault_addr ||
             first_fail_expected !== expected_first_value ||
             first_fail_actual !== expected_first_actual))
            $fatal(1, "FAULT_MBIST_FAIL first diagnostic type=%0d phase=%0d addr=%0d exp=%02h got=%02h",
                   fault_type, first_fail_phase, first_fail_addr,
                   first_fail_expected, first_fail_actual);
        $display("FAULT_CASE_RESULT type=%0d addr=%0d bit=%0d activated=%0d activations=%0d detected=%0d errors=%0d first_phase=%0d first_addr=%0d first_expected=%02h first_actual=%02h",
                 fault_type, fault_addr, fault_bit, fault_activated,
                 activation_count, fail, error_count, first_fail_phase,
                 first_fail_addr, first_fail_expected, first_fail_actual);
        $display("FAULT_MBIST_PASS type=%0d", fault_type);
        $finish;
    end
    initial begin
        #100000;
        $fatal(1, "Fault MBIST timeout");
    end
endmodule
