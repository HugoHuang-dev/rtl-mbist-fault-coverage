// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : faulty_memory.sv
// Module  : faulty_memory
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

// Verification-only RAM. Storage changes on accepted writes; fault effects
// originate in the selected physical cell, never in MBIST result signals.
module faulty_memory (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       experiment_clear,
    input  wire       req_valid,
    output wire       req_ready,
    input  wire       req_write,
    input  wire [5:0] req_addr,
    input  wire [7:0] req_wdata,
    output reg        rd_valid,
    output reg  [7:0] rd_data,
    input  wire [2:0] fault_type,
    input  wire [5:0] fault_addr,
    input  wire [2:0] fault_bit,
    output reg        fault_activated,
    output reg [15:0] activation_count
);
    reg [7:0] cells [0:63];
    wire [7:0] stored_word;
    wire activation_event;
    integer i;
    assign req_ready = rst_n;

    fault_injector u_injector (
        .fault_type(fault_type), .fault_addr(fault_addr), .fault_bit(fault_bit),
        .write_addr(req_addr), .old_word(cells[req_addr]),
        .intended_word(req_wdata), .stored_word(stored_word),
        .activation_event(activation_event)
    );

    always @(posedge clk) begin
        if (fault_type > 3'd4 || (^fault_type === 1'bx))
            $fatal(1, "Unsupported or unknown fault_type");
        if (experiment_clear) begin
            // Verification-only fresh-process equivalent for a campaign case.
            // Ordinary rst_n still preserves storage as specified in Step 5.
            for (i = 0; i < 64; i = i + 1)
                cells[i] <= 8'hxx;
            rd_data <= 8'hxx;
            rd_valid <= 1'b0;
            fault_activated <= 1'b0;
            activation_count <= 16'd0;
        end else if (!rst_n) begin
            rd_valid <= 1'b0;
            fault_activated <= 1'b0;
            activation_count <= 16'd0;
        end else begin
            rd_valid <= req_valid && !req_write;
            if (req_valid) begin
                if (req_write) begin
                    cells[req_addr] <= stored_word;
                    if (activation_event) begin
                        fault_activated <= 1'b1;
                        activation_count <= activation_count + 1'b1;
                    end
                end else begin
                    rd_data <= cells[req_addr];
                    // A stuck bit is physically fixed even before this cell's
                    // first write. Other uninitialized bits remain undefined.
                    if (req_addr == fault_addr && fault_type == 3'd1)
                        rd_data[fault_bit] <= 1'b0;
                    else if (req_addr == fault_addr && fault_type == 3'd2)
                        rd_data[fault_bit] <= 1'b1;
                end
            end
        end
    end
endmodule
