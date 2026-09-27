// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : mbist_top.v
// Module  : mbist_top
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module mbist_top #(
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
    wire [2:0] phase;
    wire issue_valid, issue_write, accepted, compare_enable, start_accepted;
    wire addr_load, addr_step, addr_down;
    wire [ADDR_WIDTH-1:0] addr_load_value, address;
    wire [DATA_WIDTH-1:0] write_data, expected_data;

    march_controller #(.ADDR_WIDTH(ADDR_WIDTH)) u_controller (
        .clk(clk), .rst_n(rst_n), .start(start), .accepted(accepted),
        .rd_valid(rd_valid), .address(address), .phase(phase),
        .issue_valid(issue_valid), .issue_write(issue_write),
        .compare_enable(compare_enable), .start_accepted(start_accepted),
        .addr_load(addr_load), .addr_load_value(addr_load_value),
        .addr_step(addr_step), .addr_down(addr_down), .busy(busy), .done(done)
    );
    address_generator #(.ADDR_WIDTH(ADDR_WIDTH)) u_address (
        .clk(clk), .rst_n(rst_n), .load(addr_load), .load_value(addr_load_value),
        .step(addr_step), .down(addr_down), .addr(address)
    );
    data_generator #(.DATA_WIDTH(DATA_WIDTH)) u_data (
        .phase(phase), .write_data(write_data), .expected_data(expected_data)
    );
    memory_interface #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH)) u_memory_if (
        .issue_valid(issue_valid), .issue_write(issue_write), .address(address),
        .write_data(write_data), .req_ready(req_ready), .req_valid(req_valid),
        .req_write(req_write), .req_addr(req_addr), .req_wdata(req_wdata),
        .accepted(accepted)
    );
    response_checker #(.ADDR_WIDTH(ADDR_WIDTH), .DATA_WIDTH(DATA_WIDTH)) u_checker (
        .clk(clk), .rst_n(rst_n), .clear(start_accepted),
        .compare_enable(compare_enable), .phase(phase), .address(address),
        .expected_data(expected_data), .rd_data(rd_data), .fail(fail),
        .error_count(error_count), .first_fail_phase(first_fail_phase),
        .first_fail_addr(first_fail_addr),
        .first_fail_expected(first_fail_expected), .first_fail_actual(first_fail_actual)
    );
    assign pass = done && !fail;
endmodule
