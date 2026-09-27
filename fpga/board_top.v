// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : board_top.v
// Module  : board_top
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

// DaVinci XC7A35T board wrapper. The MBIST algorithm and RAM interface are
// the same verified 64x8 design. Buttons are active low; LEDs
// are active high according to the board schematic.
module board_top #(
    parameter integer DEBOUNCE_CYCLES = 500000,
    parameter integer INJECT_READ_FAULT = 0
) (
    input  wire       sys_clk,
    input  wire       sys_rst_n,
    input  wire       key0,
    output wire [3:0] led
);
    // Two stages synchronize asynchronous reset release. A final synchronous
    // stage drives the core so that BRAM control never changes asynchronously.
    (* ASYNC_REG = "TRUE" *) reg reset_meta;
    (* ASYNC_REG = "TRUE" *) reg reset_release;
    reg reset_sync;
    always @(posedge sys_clk or negedge sys_rst_n) begin
        if (!sys_rst_n) begin
            reset_meta <= 1'b0;
            reset_release <= 1'b0;
        end else begin
            reset_meta <= 1'b1;
            reset_release <= reset_meta;
        end
    end
    always @(posedge sys_clk)
        reset_sync <= reset_release;
    wire core_rst_n = reset_sync;

    // KEY0 is pulled up and pressed low. Synchronize and debounce it before
    // presenting a single start pulse to the MBIST core.
    (* ASYNC_REG = "TRUE" *) reg [1:0] key_sync;
    reg key_stable;
    reg [31:0] debounce_count;
    reg start_pulse;
    always @(posedge sys_clk) begin
        if (!core_rst_n) begin
            key_sync <= 2'b11;
            key_stable <= 1'b1;
            debounce_count <= 32'd0;
            start_pulse <= 1'b0;
        end else begin
            key_sync <= {key_sync[0], key0};
            start_pulse <= 1'b0;
            if (key_sync[1] == key_stable) begin
                debounce_count <= 32'd0;
            end else if (debounce_count == DEBOUNCE_CYCLES - 1) begin
                key_stable <= key_sync[1];
                debounce_count <= 32'd0;
                if (key_stable && !key_sync[1])
                    start_pulse <= 1'b1;
            end else begin
                debounce_count <= debounce_count + 1'b1;
            end
        end
    end

    (* mark_debug = "true" *) wire busy;
    (* mark_debug = "true" *) wire done;
    (* mark_debug = "true" *) wire pass;
    (* mark_debug = "true" *) wire fail;
    (* mark_debug = "true" *) wire [8:0] error_count;
    (* mark_debug = "true" *) wire [2:0] first_fail_phase;
    (* mark_debug = "true" *) wire [5:0] first_fail_addr;
    (* mark_debug = "true" *) wire [7:0] first_fail_expected;
    (* mark_debug = "true" *) wire [7:0] first_fail_actual;
    (* mark_debug = "true" *) wire req_valid;
    (* mark_debug = "true" *) wire req_ready;
    (* mark_debug = "true" *) wire req_write;
    (* mark_debug = "true" *) wire [5:0] req_addr;
    (* mark_debug = "true" *) wire [7:0] req_wdata;
    (* mark_debug = "true" *) wire rd_valid;
    (* mark_debug = "true" *) wire [7:0] rd_data;
    (* mark_debug = "true" *) reg [9:0] accepted_count;
    wire accepted_start = start_pulse && !busy;
    wire [7:0] bram_rd_data;

    always @(posedge sys_clk) begin
        if (!core_rst_n || accepted_start)
            accepted_count <= 10'd0;
        else if (req_valid && req_ready)
            accepted_count <= accepted_count + 1'b1;
    end

    mbist_top u_mbist (
        .clk(sys_clk), .rst_n(core_rst_n), .start(start_pulse),
        .busy(busy), .done(done), .pass(pass), .fail(fail),
        .error_count(error_count), .first_fail_phase(first_fail_phase),
        .first_fail_addr(first_fail_addr), .first_fail_expected(first_fail_expected),
        .first_fail_actual(first_fail_actual),
        .req_valid(req_valid), .req_ready(req_ready), .req_write(req_write),
        .req_addr(req_addr), .req_wdata(req_wdata),
        .rd_valid(rd_valid), .rd_data(rd_data)
    );

    // Optional board diagnostic: flip one response bit on read ordinal 71
    // (zero based: M2, address 7). No controller state or RAM contents change.
    generate if (INJECT_READ_FAULT != 0) begin : g_response_test
        reg [8:0] read_ordinal;
        reg perturb_response;
        always @(posedge sys_clk) begin
            if (!core_rst_n || accepted_start) begin
                read_ordinal <= 9'd0;
                perturb_response <= 1'b0;
            end else begin
                perturb_response <= req_valid && req_ready && !req_write &&
                                    read_ordinal == 9'd71;
                if (req_valid && req_ready && !req_write)
                    read_ordinal <= read_ordinal + 1'b1;
            end
        end
        assign rd_data = bram_rd_data ^ ((rd_valid && perturb_response) ? 8'h01 : 8'h00);
    end else begin : g_normal_response
        assign rd_data = bram_rd_data;
    end endgenerate

    // A 64x8 block RAM inferred from the already verified synchronous RAM.
    single_port_sync_ram u_bram (
        .clk(sys_clk), .rst_n(core_rst_n),
        .req_valid(req_valid), .req_ready(req_ready),
        .req_write(req_write), .req_addr(req_addr), .req_wdata(req_wdata),
        .rd_valid(rd_valid), .rd_data(bram_rd_data)
    );

    assign led[0] = done;
    assign led[1] = pass;
    assign led[2] = fail;
    assign led[3] = busy;
endmodule
