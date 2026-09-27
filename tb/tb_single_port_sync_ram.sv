// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : tb_single_port_sync_ram.sv
// Module  : tb_single_port_sync_ram
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

// Independent, directed RAM test. It does not instantiate an MBIST controller.
module tb_single_port_sync_ram;
    localparam int ADDR_WIDTH = 6;
    localparam int DATA_WIDTH = 8;
    localparam int DEPTH = 1 << ADDR_WIDTH;

    logic clk = 1'b0;
    logic rst_n = 1'b0;
    logic req_valid = 1'b0;
    logic req_write = 1'b0;
    logic [ADDR_WIDTH-1:0] req_addr = '0;
    logic [DATA_WIDTH-1:0] req_wdata = '0;
    wire req_ready;
    wire rd_valid;
    wire [DATA_WIDTH-1:0] rd_data;

    logic [DATA_WIDTH-1:0] shadow [0:DEPTH-1];
    bit known [0:DEPTH-1];
    bit have_read = 0;
    logic [DATA_WIDTH-1:0] last_data;
    bit have_previous_edge = 0;
    bit previous_expected_valid = 0;
    logic [DATA_WIDTH-1:0] previous_expected_data;
    integer checks = 0;
    integer reads = 0;
    integer writes = 0;
    integer i;

    single_port_sync_ram #(
        .ADDR_WIDTH(ADDR_WIDTH),
        .DATA_WIDTH(DATA_WIDTH)
    ) dut (
        .clk(clk), .rst_n(rst_n),
        .req_valid(req_valid), .req_ready(req_ready),
        .req_write(req_write), .req_addr(req_addr), .req_wdata(req_wdata),
        .rd_valid(rd_valid), .rd_data(rd_data)
    );

    always #10 clk = ~clk;  // 50 MHz

    // Reference storage and edge-aligned response checker. The shadow array
    // starts unknown and is populated only by accepted writes; reset does not
    // clear its contents. Values after the edge are checked after NBA updates.
    always @(posedge clk) begin : check_at_edge
        bit expected_valid;
        logic [DATA_WIDTH-1:0] expected_data;

        // Active-region check sees the preceding cycle's registered outputs,
        // exactly as another posedge-triggered controller would before NBA.
        if (have_previous_edge) begin
            if (rd_valid !== previous_expected_valid)
                $fatal(1, "Consumer-edge rd_valid mismatch at %0t", $time);
            if (previous_expected_valid && rd_data !== previous_expected_data)
                $fatal(1, "Consumer-edge rd_data mismatch at %0t: got=%02h expected=%02h",
                       $time, rd_data, previous_expected_data);
        end

        expected_valid = rst_n && req_valid && !req_write;
        if (rst_n && req_valid) begin
            if (req_write) begin
                shadow[req_addr] = req_wdata;
                known[req_addr] = 1'b1;
                writes = writes + 1;
            end else begin
                if (!known[req_addr])
                    $fatal(1, "Test tried to read unwritten address %0d", req_addr);
                expected_data = shadow[req_addr];
                reads = reads + 1;
            end
        end

        #1;
        if (req_ready !== rst_n)
            $fatal(1, "req_ready mismatch at %0t: got %b, expected %b", $time, req_ready, rst_n);
        if (rd_valid !== expected_valid)
            $fatal(1, "rd_valid timing mismatch at %0t: got %b, expected %b", $time, rd_valid, expected_valid);
        if (expected_valid) begin
            if (rd_data !== expected_data)
                $fatal(1, "Read mismatch at %0t addr=%0d got=%02h expected=%02h", $time, req_addr, rd_data, expected_data);
            last_data = expected_data;
            have_read = 1'b1;
        end else if (have_read && rd_data !== last_data) begin
            $fatal(1, "rd_data changed without a read at %0t: got=%02h expected hold=%02h", $time, rd_data, last_data);
        end
        previous_expected_valid = expected_valid;
        if (expected_valid)
            previous_expected_data = expected_data;
        have_previous_edge = 1'b1;
        checks = checks + 1;
    end

    // Drive new inputs halfway between rising edges. An asynchronous read
    // implementation would change rd_data before the next edge and fail here.
    task automatic cycle(
        input bit reset_level,
        input bit valid,
        input bit write_op,
        input logic [ADDR_WIDTH-1:0] address,
        input logic [DATA_WIDTH-1:0] value
    );
        logic old_valid;
        logic [DATA_WIDTH-1:0] old_data;
        @(negedge clk);
        old_valid = rd_valid;
        old_data = rd_data;
        rst_n = reset_level;
        req_valid = valid;
        req_write = write_op;
        req_addr = address;
        req_wdata = value;
        #1;
        if (req_ready !== reset_level)
            $fatal(1, "req_ready did not track reset at %0t", $time);
        if (rd_valid !== old_valid)
            $fatal(1, "rd_valid changed before read clock edge at %0t", $time);
        if (have_read && rd_data !== old_data)
            $fatal(1, "rd_data changed before read clock edge at %0t", $time);
        @(posedge clk);
        #2;
    endtask

    initial begin : stimulus
        for (i = 0; i < DEPTH; i = i + 1)
            known[i] = 1'b0;

        // Reset, then sparse boundary writes and reads.
        cycle(0, 0, 0, 0, 0);
        cycle(0, 0, 0, 0, 0);
        cycle(1, 0, 0, 0, 0);
        cycle(1, 1, 1, 0, 8'hA5);
        cycle(1, 1, 1, 63, 8'h5A);
        cycle(1, 1, 0, 0, 0);
        cycle(1, 1, 0, 63, 0);
        cycle(1, 0, 0, 31, 0);  // No phantom read; output data holds.
        $display("CASE_PASS boundary_addresses_and_sparse_access");

        // Consecutive writes and consecutive reads across all 64 addresses.
        for (i = 0; i < DEPTH; i = i + 1)
            cycle(1, 1, 1, i, (i * 37) ^ 8'h5A);
        for (i = 0; i < DEPTH; i = i + 1)
            cycle(1, 1, 0, i, 0);
        $display("CASE_PASS all_addresses_consecutive_write_read");

        // Alternating read/write and immediate readback, including 63 -> 0.
        cycle(1, 1, 1, 63, 8'hC3);
        cycle(1, 1, 0, 63, 0);
        cycle(1, 1, 1, 0, 8'h3C);
        cycle(1, 1, 0, 0, 0);
        cycle(1, 0, 0, 0, 0);
        $display("CASE_PASS alternating_write_read_and_idle_hold");

        // Reset cancels a pending response and blocks a write, but preserves RAM.
        cycle(1, 1, 0, 63, 0);
        cycle(0, 1, 1, 63, 8'hEE);
        cycle(1, 1, 0, 63, 0);
        cycle(1, 0, 0, 63, 0);
        $display("CASE_PASS reset_blocks_write_and_preserves_ram");

        if (writes != 68 || reads != 70)
            $fatal(1, "Stimulus counts wrong: writes=%0d reads=%0d", writes, reads);
        $display("RAM_TB_PASS checks=%0d reads=%0d writes=%0d", checks, reads, writes);
        $finish;
    end

    initial begin
        #100000;
        $fatal(1, "RAM testbench timed out");
    end
endmodule
