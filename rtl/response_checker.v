// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : response_checker.v
// Module  : response_checker
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module response_checker #(
    parameter integer ADDR_WIDTH = 6,
    parameter integer DATA_WIDTH = 8
) (
    input  wire                      clk,
    input  wire                      rst_n,
    input  wire                      clear,
    input  wire                      compare_enable,
    input  wire [2:0]                phase,
    input  wire [ADDR_WIDTH-1:0]     address,
    input  wire [DATA_WIDTH-1:0]     expected_data,
    input  wire [DATA_WIDTH-1:0]     rd_data,
    output reg                       fail,
    output reg  [8:0]                error_count,
    output reg  [2:0]                first_fail_phase,
    output reg  [ADDR_WIDTH-1:0]     first_fail_addr,
    output reg  [DATA_WIDTH-1:0]     first_fail_expected,
    output reg  [DATA_WIDTH-1:0]     first_fail_actual
);
    always @(posedge clk) begin
        if (!rst_n || clear) begin
            fail <= 1'b0;
            error_count <= 9'd0;
            first_fail_phase <= 3'd0;
            first_fail_addr <= {ADDR_WIDTH{1'b0}};
            first_fail_expected <= {DATA_WIDTH{1'b0}};
            first_fail_actual <= {DATA_WIDTH{1'b0}};
        end else if (compare_enable && rd_data != expected_data) begin
            fail <= 1'b1;
            error_count <= error_count + 1'b1;
            if (!fail) begin
                first_fail_phase <= phase;
                first_fail_addr <= address;
                first_fail_expected <= expected_data;
                first_fail_actual <= rd_data;
            end
        end
    end
endmodule
