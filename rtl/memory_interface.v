// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : memory_interface.v
// Module  : memory_interface
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

// Combinational request adapter. A stalled request remains stable because the
// controller holds its state, phase and address until req_ready is sampled.
module memory_interface #(
    parameter integer ADDR_WIDTH = 6,
    parameter integer DATA_WIDTH = 8
) (
    input  wire                      issue_valid,
    input  wire                      issue_write,
    input  wire [ADDR_WIDTH-1:0]     address,
    input  wire [DATA_WIDTH-1:0]     write_data,
    input  wire                      req_ready,
    output wire                      req_valid,
    output wire                      req_write,
    output wire [ADDR_WIDTH-1:0]     req_addr,
    output wire [DATA_WIDTH-1:0]     req_wdata,
    output wire                      accepted
);
    assign req_valid = issue_valid;
    assign req_write = issue_write;
    assign req_addr = address;
    assign req_wdata = write_data;
    assign accepted = issue_valid && req_ready;
endmodule
