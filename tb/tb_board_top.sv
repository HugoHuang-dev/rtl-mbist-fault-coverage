// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : tb_board_top.sv
// Module  : tb_board_top
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

// Short board-wrapper regression. The RAM remains the same synchronous RTL;
// this checks button conditioning, LEDs, and the complete public transaction
// sequence before any physical-board claim is made.
module tb_board_top #(parameter integer INJECT = 0);
    reg sys_clk = 1'b0;
    reg sys_rst_n = 1'b0;
    reg key0 = 1'b1;
    wire [3:0] led;
    integer rounds = 0;
    integer busy_seen = 0;
    always #10 sys_clk = ~sys_clk;

    board_top #(.DEBOUNCE_CYCLES(4), .INJECT_READ_FAULT(INJECT)) dut (
        .sys_clk(sys_clk), .sys_rst_n(sys_rst_n), .key0(key0), .led(led)
    );
    march_transaction_checker u_checker (
        .clk(sys_clk), .rst_n(dut.core_rst_n), .start(dut.start_pulse),
        .run_id(2'd1), .req_valid(dut.req_valid), .req_ready(dut.req_ready),
        .req_write(dut.req_write), .req_addr(dut.req_addr),
        .req_wdata(dut.req_wdata), .rd_valid(dut.rd_valid),
        .rd_data(dut.rd_data), .done(dut.done), .pass(dut.pass),
        .fail(dut.fail), .error_count(dut.error_count),
        .first_fail_phase(dut.first_fail_phase),
        .first_fail_addr(dut.first_fail_addr),
        .first_fail_expected(dut.first_fail_expected),
        .first_fail_actual(dut.first_fail_actual)
    );
    always @(posedge sys_clk)
        if (dut.busy)
            busy_seen <= 1;

    task automatic run_once;
        integer timeout;
        begin
            @(negedge sys_clk);
            key0 = 1'b0;
            repeat (10) @(negedge sys_clk);
            key0 = 1'b1;
            // Attempt a second debounced start while still busy. It must not
            // restart the controller or clear the request counter.
            repeat (10) @(negedge sys_clk);
            key0 = 1'b0;
            repeat (10) @(negedge sys_clk);
            key0 = 1'b1;
            timeout = 0;
            while (!dut.done && timeout < 1200) begin
                @(negedge sys_clk);
                timeout = timeout + 1;
            end
            if (!dut.done)
                $fatal(1, "BOARD_TB_TIMEOUT round=%0d", rounds);
            #2;
            if (led !== (INJECT ? 4'b0101 : 4'b0011) || dut.accepted_count !== 10'd640 ||
                dut.error_count !== (INJECT ? 9'd1 : 9'd0) || !busy_seen)
                $fatal(1, "BOARD_TB_RESULT_FAIL round=%0d led=%b count=%0d errors=%0d",
                       rounds, led, dut.accepted_count, dut.error_count);
            if (INJECT && (dut.first_fail_phase !== 3'd2 ||
                dut.first_fail_addr !== 6'd7 || dut.first_fail_expected !== 8'hff ||
                dut.first_fail_actual !== 8'hfe))
                $fatal(1, "BOARD_TB_FAULT_DIAGNOSTIC_FAIL");
            rounds = rounds + 1;
            $display("BOARD_CASE_PASS round=%0d requests=%0d led=%b",
                     rounds, dut.accepted_count, led);
            repeat (10) @(negedge sys_clk);
        end
    endtask

    initial begin
        repeat (4) @(negedge sys_clk);
        sys_rst_n = 1'b1;
        repeat (6) @(negedge sys_clk);
        if (led !== 4'b0000)
            $fatal(1, "BOARD_TB_RESET_LED_FAIL led=%b", led);
        run_once;
        run_once;
        // Abort an active run with an asynchronous button edge, then restart.
        @(negedge sys_clk); key0 = 1'b0;
        repeat (15) @(negedge sys_clk);
        if (!dut.busy) $fatal(1, "BOARD_TB_ABORT_NOT_BUSY");
        #3; sys_rst_n = 1'b0; key0 = 1'b1;
        repeat (6) @(negedge sys_clk);
        if (led !== 4'b0000 || dut.accepted_count !== 0 || dut.req_valid !== 0)
            $fatal(1, "BOARD_TB_ACTIVE_RESET_FAIL");
        #3; sys_rst_n = 1'b1;
        repeat (8) @(negedge sys_clk);
        run_once;
        $display("BOARD_TB_PASS rounds=3 inject=%0d busy_start=ignored active_reset=pass", INJECT);
        $finish;
    end
    initial begin
        #200000;
        $fatal(1, "BOARD_TB_GLOBAL_TIMEOUT");
    end
endmodule

module tb_board_fault;
    tb_board_top #(.INJECT(1)) test();
endmodule
