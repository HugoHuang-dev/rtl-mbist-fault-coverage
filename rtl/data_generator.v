// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : data_generator.v
// Module  : data_generator
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module data_generator #(
    parameter integer DATA_WIDTH = 8
) (
    input  wire [2:0]            phase,
    output wire [DATA_WIDTH-1:0] write_data,
    output wire [DATA_WIDTH-1:0] expected_data
);
    // M1/M3 write ones; M2/M4 expect ones. Other phases use zeros.
    assign write_data = (phase == 3'd1 || phase == 3'd3)
                      ? {DATA_WIDTH{1'b1}} : {DATA_WIDTH{1'b0}};
    assign expected_data = (phase == 3'd2 || phase == 3'd4)
                         ? {DATA_WIDTH{1'b1}} : {DATA_WIDTH{1'b0}};
endmodule
