// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : address_generator.v
// Module  : address_generator
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module address_generator #(
    parameter integer ADDR_WIDTH = 6
) (
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire                  load,
    input  wire [ADDR_WIDTH-1:0] load_value,
    input  wire                  step,
    input  wire                  down,
    output reg  [ADDR_WIDTH-1:0] addr
);
    always @(posedge clk) begin
        if (!rst_n)
            addr <= {ADDR_WIDTH{1'b0}};
        else if (load)
            addr <= load_value;
        else if (step)
            addr <= down ? addr - 1'b1 : addr + 1'b1;
    end
endmodule
