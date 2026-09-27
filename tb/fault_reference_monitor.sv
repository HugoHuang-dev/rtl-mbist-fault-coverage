// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : fault_reference_monitor.sv
// Module  : fault_reference_monitor
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

// Independent physical-cell scoreboard. It never reads faulty_memory.cells or
// the controller's diagnostic registers to form expected RAM/activation data.
module fault_reference_monitor (
    input wire        clk,
    input wire        rst_n,
    input wire        experiment_clear,
    input wire        req_valid,
    input wire        req_ready,
    input wire        req_write,
    input wire [5:0]  req_addr,
    input wire [7:0]  req_wdata,
    input wire        rd_valid,
    input wire [7:0]  rd_data,
    input wire [2:0]  fault_type,
    input wire [5:0]  fault_addr,
    input wire [2:0]  fault_bit,
    input wire        fault_activated,
    input wire [15:0] activation_count
);
    reg [7:0] reference_cells [0:63];
    reg known [0:63];
    reg expected_activated = 1'b0;
    integer expected_count = 0;
    reg have_read = 1'b0;
    reg [7:0] last_read;
    reg expected_valid;
    reg [7:0] expected_data;
    reg [7:0] next_word;
    reg old_bit;
    reg triggered;
    integer i;

    initial for (i = 0; i < 64; i = i + 1) known[i] = 1'b0;

    always @(posedge clk) begin
        expected_valid = rst_n && !experiment_clear && req_valid && !req_write && req_ready;
        if (experiment_clear) begin
            for (i = 0; i < 64; i = i + 1) known[i] = 1'b0;
            have_read = 1'b0;
            expected_activated = 1'b0;
            expected_count = 0;
        end else if (!rst_n) begin
            expected_activated = 1'b0;
            expected_count = 0;
        end else if (req_valid && req_ready) begin
            if (req_write) begin
                next_word = req_wdata;
                triggered = 1'b0;
                if (req_addr == fault_addr) begin
                    old_bit = known[req_addr] ? reference_cells[req_addr][fault_bit] : 1'bx;
                    case (fault_type)
                        3'd1: begin
                            if (req_wdata[fault_bit] == 1'b1) triggered = 1'b1;
                            next_word[fault_bit] = 1'b0;
                        end
                        3'd2: begin
                            if (req_wdata[fault_bit] == 1'b0) triggered = 1'b1;
                            next_word[fault_bit] = 1'b1;
                        end
                        3'd3: if (known[req_addr] && old_bit == 1'b0 &&
                                      req_wdata[fault_bit] == 1'b1) begin
                            triggered = 1'b1;
                            next_word[fault_bit] = old_bit;
                        end
                        3'd4: if (known[req_addr] && old_bit == 1'b1 &&
                                      req_wdata[fault_bit] == 1'b0) begin
                            triggered = 1'b1;
                            next_word[fault_bit] = old_bit;
                        end
                        default: begin end
                    endcase
                end
                reference_cells[req_addr] = next_word;
                known[req_addr] = 1'b1;
                if (triggered) begin
                    expected_activated = 1'b1;
                    expected_count = expected_count + 1;
                    $display("FAULT_ACTIVATE type=%0d addr=%0d bit=%0d count=%0d",
                             fault_type, req_addr, fault_bit, expected_count);
                end
            end else begin
                if (!known[req_addr])
                    $fatal(1, "FAULT_REF_FAIL read before initialization addr=%0d", req_addr);
                expected_data = reference_cells[req_addr];
                if (req_addr == fault_addr && fault_type == 3'd1)
                    expected_data[fault_bit] = 1'b0;
                else if (req_addr == fault_addr && fault_type == 3'd2)
                    expected_data[fault_bit] = 1'b1;
            end
        end
        #1;
        if (rd_valid !== expected_valid)
            $fatal(1, "FAULT_REF_FAIL rd_valid addr=%0d got=%b expected=%b",
                   req_addr, rd_valid, expected_valid);
        if (expected_valid) begin
            if (rd_data !== expected_data)
                $fatal(1, "FAULT_REF_FAIL data addr=%0d got=%02h expected=%02h",
                       req_addr, rd_data, expected_data);
            last_read = expected_data;
            have_read = 1'b1;
        end else if (have_read && rd_data !== last_read) begin
            $fatal(1, "FAULT_REF_FAIL rd_data changed without read");
        end
        if (fault_activated !== expected_activated ||
            activation_count !== expected_count[15:0])
            $fatal(1, "FAULT_REF_FAIL activation got=%b/%0d expected=%b/%0d",
                   fault_activated, activation_count, expected_activated, expected_count);
    end
endmodule
