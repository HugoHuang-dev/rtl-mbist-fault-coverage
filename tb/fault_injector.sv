// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : fault_injector.sv
// Module  : fault_injector
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

// Single selected bit/cell fault. The caller supplies the cell's current
// physical contents; transition activation requires a known old bit value.
module fault_injector (
    input  wire [2:0] fault_type, // 0 none, 1 SA0, 2 SA1, 3 rising TF, 4 falling TF
    input  wire [5:0] fault_addr,
    input  wire [2:0] fault_bit,
    input  wire [5:0] write_addr,
    input  wire [7:0] old_word,
    input  wire [7:0] intended_word,
    output reg  [7:0] stored_word,
    output reg        activation_event
);
    always @* begin
        stored_word = intended_word;
        activation_event = 1'b0;
        if (write_addr == fault_addr) begin
            case (fault_type)
                3'd1: begin // SA0: requested 1 cannot be stored.
                    activation_event = (intended_word[fault_bit] === 1'b1);
                    stored_word[fault_bit] = 1'b0;
                end
                3'd2: begin // SA1: requested 0 cannot be stored.
                    activation_event = (intended_word[fault_bit] === 1'b0);
                    stored_word[fault_bit] = 1'b1;
                end
                3'd3: if (old_word[fault_bit] === 1'b0 &&
                             intended_word[fault_bit] === 1'b1) begin
                    activation_event = 1'b1;
                    stored_word[fault_bit] = 1'b0;
                end
                3'd4: if (old_word[fault_bit] === 1'b1 &&
                             intended_word[fault_bit] === 1'b0) begin
                    activation_event = 1'b1;
                    stored_word[fault_bit] = 1'b1;
                end
                default: begin end
            endcase
        end
    end
endmodule
