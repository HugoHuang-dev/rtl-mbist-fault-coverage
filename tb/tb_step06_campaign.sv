// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : tb_step06_campaign.sv
// Module  : tb_step06_campaign
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

// A chunk runs in one simulator process. experiment_clear restores the fault
// RAM and reference monitor to the same unknown state as a fresh process.
// The MBIST RTL and the Step 4 transaction checker remain unchanged.
module tb_step06_campaign;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg experiment_clear = 1'b1;
    reg start = 1'b0;
    reg [2:0] fault_type = 3'd0;
    reg [5:0] fault_addr = 6'd0;
    reg [2:0] fault_bit = 3'd0;
    reg [11:0] fault_config [0:2047]; // {type[2:0], addr[5:0], bit[2:0]}
    reg [10:0] selected_ids [0:2047];
    integer start_index = 0;
    integer case_count = 2048;
    integer i, j, wait_cycles;
    integer accepted_requests = 0;

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
    initial $readmemh("campaign.hex", fault_config);
    initial $readmemh("selection.hex", selected_ids);

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
        .clk(clk), .rst_n(rst_n), .experiment_clear(experiment_clear),
        .req_valid(req_valid), .req_ready(req_ready), .req_write(req_write),
        .req_addr(req_addr), .req_wdata(req_wdata),
        .rd_valid(rd_valid), .rd_data(rd_data),
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
    fault_reference_monitor u_reference (
        .clk(clk), .rst_n(rst_n), .experiment_clear(experiment_clear),
        .req_valid(req_valid), .req_ready(req_ready), .req_write(req_write),
        .req_addr(req_addr), .req_wdata(req_wdata),
        .rd_valid(rd_valid), .rd_data(rd_data),
        .fault_type(fault_type), .fault_addr(fault_addr), .fault_bit(fault_bit),
        .fault_activated(fault_activated), .activation_count(activation_count)
    );

    always @(posedge clk) begin
        if (!rst_n || experiment_clear)
            accepted_requests <= 0;
        else if (req_valid && req_ready)
            accepted_requests <= accepted_requests + 1;
    end

    initial begin
        if ($value$plusargs("START_INDEX=%d", start_index)) begin end
        if ($value$plusargs("CASE_COUNT=%d", case_count)) begin end
        if (start_index < 0 || case_count < 1 || start_index + case_count > 2048)
            $fatal(1, "Invalid campaign range start=%0d count=%0d", start_index, case_count);

        for (j = start_index; j < start_index + case_count; j = j + 1) begin
            i = selected_ids[j];
            if (i < 0 || i > 2047)
                $fatal(1, "Invalid selected fault index %0d", i);
            @(negedge clk);
            rst_n = 1'b0;
            experiment_clear = 1'b1;
            start = 1'b0;
            fault_type = fault_config[i][11:9];
            fault_addr = fault_config[i][8:3];
            fault_bit = fault_config[i][2:0];
            $display("CASE_BEGIN id=%0d type=%0d addr=%0d bit=%0d",
                     i, fault_type, fault_addr, fault_bit);
            @(posedge clk);
            #2;
            if (fault_activated !== 1'b0 || activation_count !== 16'd0 ||
                rd_valid !== 1'b0 || done !== 1'b0 || accepted_requests != 0)
                $fatal(1, "CASE_RESET_FAIL id=%0d", i);
            @(negedge clk);
            experiment_clear = 1'b0;
            @(negedge clk);
            rst_n = 1'b1;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;

            wait_cycles = 0;
            while (!done && wait_cycles < 1500) begin
                @(negedge clk);
                wait_cycles = wait_cycles + 1;
            end
            if (!done)
                $fatal(1, "CASE_TIMEOUT id=%0d", i);
            @(negedge clk);
            if (accepted_requests != 640)
                $fatal(1, "CASE_REQUEST_COUNT_FAIL id=%0d count=%0d", i, accepted_requests);
            $display("CASE_RESULT id=%0d type=%0d addr=%0d bit=%0d activated=%0d activations=%0d detected=%0d errors=%0d first_phase=%0d first_addr=%0d first_expected=%02h first_actual=%02h requests=%0d cycles=%0d",
                     i, fault_type, fault_addr, fault_bit, fault_activated,
                     activation_count, fail, error_count, first_fail_phase,
                     first_fail_addr, first_fail_expected, first_fail_actual,
                     accepted_requests, wait_cycles);
        end
        $display("CAMPAIGN_DONE start=%0d count=%0d", start_index, case_count);
        $finish;
    end
endmodule
