// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : tb_mbist_top.sv
// Module  : tb_mbist_top
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_mbist_top;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg start = 1'b0;
    wire busy, done, pass, fail;
    wire [8:0] error_count;
    wire [2:0] first_fail_phase;
    wire [5:0] first_fail_addr;
    wire [7:0] first_fail_expected, first_fail_actual;
    wire req_valid, req_ready, req_write, rd_valid;
    wire [5:0] req_addr;
    wire [7:0] req_wdata, rd_data;
    wire [7:0] checked_rd_data;
    reg inject_mode = 1'b0;
    reg inject_pending = 1'b0;
    integer run_id = 0;
    integer seq = 0;
    integer reads = 0;
    integer writes = 0;
    integer cycles = 0;
    integer expected_phase;
    integer expected_addr;
    integer expected_write;
    integer expected_data;
    integer local_index;

    always #10 clk = ~clk;
    assign checked_rd_data = inject_pending ? (rd_data ^ 8'h01) : rd_data;

    mbist_top dut (
        .clk(clk), .rst_n(rst_n), .start(start), .busy(busy),
        .done(done), .pass(pass), .fail(fail), .error_count(error_count),
        .first_fail_phase(first_fail_phase), .first_fail_addr(first_fail_addr),
        .first_fail_expected(first_fail_expected), .first_fail_actual(first_fail_actual),
        .req_valid(req_valid), .req_ready(req_ready), .req_write(req_write),
        .req_addr(req_addr), .req_wdata(req_wdata),
        .rd_valid(rd_valid), .rd_data(checked_rd_data)
    );
    single_port_sync_ram ram (
        .clk(clk), .rst_n(rst_n), .req_valid(req_valid),
        .req_ready(req_ready), .req_write(req_write), .req_addr(req_addr),
        .req_wdata(req_wdata), .rd_valid(rd_valid), .rd_data(rd_data)
    );

    // Faulty-response smoke test only: the independent fault RAM belongs to
    // Step 5. This perturbation proves the Step 3 diagnostic/continue path.
    always @(posedge clk) begin
        if (!rst_n)
            inject_pending <= 1'b0;
        else
            inject_pending <= inject_mode && req_valid && req_ready &&
                              !req_write && run_id == 2 &&
                              dut.u_controller.phase == 3'd2 && req_addr == 6'd7;
    end

    // Independent operation oracle uses the Step 1 phase ranges, not the
    // controller's next-state logic. The run log is also checked against the
    // frozen 640-row CSV by scripts/check_step03_trace.py.
    always @(posedge clk) begin
        if (rst_n && req_valid && req_ready) begin
            if (seq >= 640)
                $fatal(1, "Extra RAM request run=%0d seq=%0d", run_id, seq);
            if (seq < 64) begin
                expected_phase = 0;
                expected_addr = seq;
                expected_write = 1;
                expected_data = 0;
            end else if (seq < 192) begin
                expected_phase = 1;
                local_index = seq - 64;
                expected_addr = local_index / 2;
                expected_write = local_index % 2;
                expected_data = 255;
            end else if (seq < 320) begin
                expected_phase = 2;
                local_index = seq - 192;
                expected_addr = local_index / 2;
                expected_write = local_index % 2;
                expected_data = 0;
            end else if (seq < 448) begin
                expected_phase = 3;
                local_index = seq - 320;
                expected_addr = 63 - local_index / 2;
                expected_write = local_index % 2;
                expected_data = 255;
            end else if (seq < 576) begin
                expected_phase = 4;
                local_index = seq - 448;
                expected_addr = 63 - local_index / 2;
                expected_write = local_index % 2;
                expected_data = 0;
            end else begin
                expected_phase = 5;
                expected_addr = seq - 576;
                expected_write = 0;
                expected_data = 0;
            end
            if (dut.u_controller.phase !== expected_phase[2:0] ||
                req_addr !== expected_addr[5:0] ||
                req_write !== expected_write[0] ||
                (expected_write && req_wdata !== expected_data[7:0]))
                $fatal(1, "Request mismatch run=%0d seq=%0d phase=%0d addr=%0d write=%0d data=%02h",
                       run_id, seq, dut.u_controller.phase, req_addr, req_write, req_wdata);
            $display("TRACE,%0d,%0d,%0d,%0d,%0d,%02h", run_id, seq,
                     dut.u_controller.phase, req_addr, req_write, req_wdata);
            seq = seq + 1;
            if (req_write) writes = writes + 1;
            else reads = reads + 1;
        end
        if (rst_n && run_id != 0) cycles = cycles + 1;
    end

    task automatic launch(input integer next_run, input reg inject);
        begin
            @(negedge clk);
            run_id = next_run;
            inject_mode = inject;
            seq = 0;
            reads = 0;
            writes = 0;
            cycles = 0;
            start = 1'b1;
            @(negedge clk);
            start = 1'b0;
        end
    endtask

    task automatic await_completion(input integer expected_fail);
        begin
            while (!done) begin
                @(negedge clk);
                if (cycles > 3000) $fatal(1, "MBIST timed out run=%0d", run_id);
            end
            if (seq != 640 || reads != 320 || writes != 320)
                $fatal(1, "Counts run=%0d requests=%0d reads=%0d writes=%0d",
                       run_id, seq, reads, writes);
            if (fail !== expected_fail[0] || pass !== !expected_fail[0])
                $fatal(1, "Result run=%0d done=%b pass=%b fail=%b", run_id, done, pass, fail);
            if (expected_fail && (error_count !== 9'd1 ||
                first_fail_phase !== 3'd2 || first_fail_addr !== 6'd7 ||
                first_fail_expected !== 8'hff || first_fail_actual !== 8'hfe))
                $fatal(1, "Diagnostics run=%0d count=%0d phase=%0d addr=%0d exp=%02h got=%02h",
                       run_id, error_count, first_fail_phase, first_fail_addr,
                       first_fail_expected, first_fail_actual);
            if (!expected_fail && error_count !== 9'd0)
                $fatal(1, "Unexpected mismatches run=%0d count=%0d", run_id, error_count);
            $display("CASE_PASS run=%0d requests=%0d reads=%0d writes=%0d cycles=%0d pass=%0d fail=%0d errors=%0d",
                     run_id, seq, reads, writes, cycles, pass, fail, error_count);
        end
    endtask

    initial begin
        repeat (3) @(negedge clk);
        rst_n = 1'b1;
        launch(1, 1'b0);
        // A pulse while active must not restart the sequence.
        repeat (100) @(negedge clk);
        start = 1'b1;
        @(negedge clk);
        start = 1'b0;
        await_completion(0);
        repeat (3) @(negedge clk);
        if (!done || !pass) $fatal(1, "Result did not hold in DONE");
        launch(2, 1'b1);  // Restart from DONE without clearing RAM contents.
        await_completion(1);
        $display("MBIST_TB_PASS normal_and_injected_continue");
        $finish;
    end

    initial begin
        #100000;
        $fatal(1, "Global MBIST timeout");
    end
endmodule
