// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : march_controller.v
// Module  : march_controller
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module march_controller #(
    parameter integer ADDR_WIDTH = 6
) (
    input  wire                      clk,
    input  wire                      rst_n,
    input  wire                      start,
    input  wire                      accepted,
    input  wire                      rd_valid,
    input  wire [ADDR_WIDTH-1:0]     address,
    output reg  [2:0]                phase,
    output wire                      issue_valid,
    output wire                      issue_write,
    output wire                      compare_enable,
    output wire                      start_accepted,
    output wire                      addr_load,
    output wire [ADDR_WIDTH-1:0]     addr_load_value,
    output wire                      addr_step,
    output wire                      addr_down,
    output wire                      busy,
    output wire                      done
);
    localparam [2:0] IDLE = 3'd0, ISSUE = 3'd1,
                     WAIT_READ = 3'd2, WRITE_AFTER_READ = 3'd3,
                     DONE = 3'd4;
    localparam [ADDR_WIDTH-1:0] LAST_ADDR = {ADDR_WIDTH{1'b1}};
    reg [2:0] state;

    assign start_accepted = start && (state == IDLE || state == DONE);
    assign issue_valid = (state == ISSUE || state == WRITE_AFTER_READ);
    assign issue_write = (state == WRITE_AFTER_READ || (state == ISSUE && phase == 3'd0));
    assign compare_enable = (state == WAIT_READ && rd_valid);
    assign busy = (state == ISSUE || state == WAIT_READ || state == WRITE_AFTER_READ);
    assign done = (state == DONE);
    assign addr_down = (phase == 3'd3 || phase == 3'd4);

    wire element_complete = (state == ISSUE && phase == 3'd0 && accepted)
                          || (state == WRITE_AFTER_READ && accepted)
                          || (state == WAIT_READ && phase == 3'd5 && rd_valid);
    wire phase_end = addr_down ? (address == {ADDR_WIDTH{1'b0}})
                               : (address == LAST_ADDR);
    assign addr_load = start_accepted || (element_complete && phase_end && phase != 3'd5);
    assign addr_load_value = (element_complete && phase_end && phase == 3'd2)
                           || (element_complete && phase_end && phase == 3'd3)
                           ? LAST_ADDR : {ADDR_WIDTH{1'b0}};
    assign addr_step = element_complete && !phase_end;

    always @(posedge clk) begin
        if (!rst_n) begin
            state <= IDLE;
            phase <= 3'd0;
        end else if (start_accepted) begin
            state <= ISSUE;
            phase <= 3'd0;
        end else begin
            case (state)
                ISSUE: if (accepted) begin
                    if (phase == 3'd0)
                        state <= ISSUE;
                    else
                        state <= WAIT_READ;
                end
                WAIT_READ: if (rd_valid) begin
                    if (phase == 3'd5)
                        state <= ISSUE;
                    else
                        state <= WRITE_AFTER_READ;
                end
                WRITE_AFTER_READ: if (accepted)
                    state <= ISSUE;
                default: state <= state;
            endcase
            if (element_complete && phase_end) begin
                if (phase == 3'd5)
                    state <= DONE;
                else
                    phase <= phase + 1'b1;
            end
        end
    end
endmodule
