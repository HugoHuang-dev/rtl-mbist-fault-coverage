// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : single_port_sync_ram.v
// Module  : single_port_sync_ram
// -----------------------------------------------------------------------------
`timescale 1ns/1ps
// Single-port, synchronous-read RAM for the Step 1 request/response contract.
// The memory array has no power-up initialization and is not reset.
// A read accepted at edge E produces rd_valid/rd_data after E, so a synchronous
// controller samples them at the next rising edge. Writes have no response.
module single_port_sync_ram #(
    parameter integer ADDR_WIDTH = 6,
    parameter integer DATA_WIDTH = 8
) (
    input  wire                      clk,
    input  wire                      rst_n,
    input  wire                      req_valid,
    output wire                      req_ready,
    input  wire                      req_write,
    input  wire [ADDR_WIDTH-1:0]     req_addr,
    input  wire [DATA_WIDTH-1:0]     req_wdata,
    output reg                       rd_valid,
    output reg  [DATA_WIDTH-1:0]     rd_data
);
    localparam integer DEPTH = 1 << ADDR_WIDTH;

    // Synthesis hint only: the actual Vivado RAM mapping needs report review.
    // Do not reset this array or rd_data; a reset on either can obstruct BRAM
    // inference or add an unwanted read pipeline stage.
    (* ram_style = "block" *) reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    // No transaction is accepted during the synchronous reset cycle.
    assign req_ready = rst_n;

    always @(posedge clk) begin
        if (rst_n && req_valid) begin
            if (req_write)
                mem[req_addr] <= req_wdata;
            else
                rd_data <= mem[req_addr];
        end
    end

    always @(posedge clk) begin
        if (!rst_n)
            rd_valid <= 1'b0;
        else
            rd_valid <= req_valid && !req_write;
    end
endmodule
