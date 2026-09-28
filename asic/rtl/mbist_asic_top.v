// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : mbist_asic_top.v
// Module  : mbist_asic_top
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

// Controller-only ASIC boundary. The synchronous SRAM is external and keeps
// the same request/response timing contract as the verified mbist_top.
module mbist_asic_top #(
    parameter integer ADDR_WIDTH = 6,
    parameter integer DATA_WIDTH = 8
) (
    input  wire                      clk,
    input  wire                      rst_n,
    input  wire                      start,
    output wire                      busy,
    output wire                      done,
    output wire                      pass,
    output wire                      fail,
    output wire [8:0]                error_count,
    output wire [2:0]                first_fail_phase,
    output wire [ADDR_WIDTH-1:0]     first_fail_addr,
    output wire [DATA_WIDTH-1:0]     first_fail_expected,
    output wire [DATA_WIDTH-1:0]     first_fail_actual,
    output wire                      req_valid,
    input  wire                      req_ready,
    output wire                      req_write,
    output wire [ADDR_WIDTH-1:0]     req_addr,
    output wire [DATA_WIDTH-1:0]     req_wdata,
    input  wire                      rd_valid,
    input  wire [DATA_WIDTH-1:0]     rd_data
);
    mbist_top #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH)) u_mbist (
        .clk(clk), .rst_n(rst_n), .start(start),
        .busy(busy), .done(done), .pass(pass), .fail(fail),
        .error_count(error_count), .first_fail_phase(first_fail_phase),
        .first_fail_addr(first_fail_addr),
        .first_fail_expected(first_fail_expected),
        .first_fail_actual(first_fail_actual),
        .req_valid(req_valid), .req_ready(req_ready),
        .req_write(req_write), .req_addr(req_addr), .req_wdata(req_wdata),
        .rd_valid(rd_valid), .rd_data(rd_data)
    );
endmodule
