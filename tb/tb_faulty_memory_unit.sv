// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : tb_faulty_memory_unit.sv
// Module  : tb_faulty_memory_unit
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

module tb_faulty_memory_unit;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg req_valid = 1'b0;
    reg req_write = 1'b0;
    reg [5:0] req_addr = 0;
    reg [7:0] req_wdata = 0;
    wire req_ready, rd_valid, fault_activated;
    wire [7:0] rd_data;
    wire [15:0] activation_count;
    reg [2:0] fault_type;
    reg [5:0] fault_addr;
    reg [2:0] fault_bit;
    integer type_arg, addr_arg, bit_arg;
    reg [7:0] mask, last_expected;
    reg [5:0] other_addr;

    always #10 clk = ~clk;
    faulty_memory dut (
        .clk(clk), .rst_n(rst_n), .experiment_clear(1'b0), .req_valid(req_valid),
        .req_ready(req_ready), .req_write(req_write), .req_addr(req_addr),
        .req_wdata(req_wdata), .rd_valid(rd_valid), .rd_data(rd_data),
        .fault_type(fault_type), .fault_addr(fault_addr), .fault_bit(fault_bit),
        .fault_activated(fault_activated), .activation_count(activation_count)
    );

    task automatic write_check(input [5:0] addr, input [7:0] data,
                               input integer count);
        begin
            @(negedge clk);
            req_valid = 1'b1;
            req_write = 1'b1;
            req_addr = addr;
            req_wdata = data;
            if (req_ready !== 1'b1) $fatal(1, "RAM not ready");
            @(posedge clk);
            #1;
            if (rd_valid !== 1'b0 || activation_count !== count[15:0] ||
                fault_activated !== (count != 0))
                $fatal(1, "UNIT_FAIL write type=%0d addr=%0d data=%02h count=%0d got=%0d",
                       fault_type, addr, data, count, activation_count);
        end
    endtask

    task automatic read_check(input [5:0] addr, input [7:0] expected,
                              input integer count);
        reg [7:0] old_data;
        begin
            @(negedge clk);
            old_data = rd_data;
            req_valid = 1'b1;
            req_write = 1'b0;
            req_addr = addr;
            #1;
            if (rd_data !== old_data)
                $fatal(1, "UNIT_FAIL asynchronous read addr=%0d", addr);
            @(posedge clk);
            #1;
            if (rd_valid !== 1'b1 || rd_data !== expected ||
                activation_count !== count[15:0])
                $fatal(1, "UNIT_FAIL read type=%0d addr=%0d got=%02h expected=%02h count=%0d",
                       fault_type, addr, rd_data, expected, activation_count);
        end
    endtask

    task automatic read_stuck_bit_before_write(input reg expected);
        begin
            @(negedge clk);
            req_valid = 1'b1;
            req_write = 1'b0;
            req_addr = fault_addr;
            @(posedge clk);
            #1;
            if (rd_valid !== 1'b1 || rd_data[fault_bit] !== expected ||
                activation_count !== 16'd0)
                $fatal(1, "UNIT_FAIL stuck bit before first write");
        end
    endtask

    initial begin
        type_arg = 0;
        addr_arg = 7;
        bit_arg = 2;
        if ($value$plusargs("FAULT_TYPE=%d", type_arg)) begin end
        if ($value$plusargs("FAULT_ADDR=%d", addr_arg)) begin end
        if ($value$plusargs("FAULT_BIT=%d", bit_arg)) begin end
        if (type_arg < 0 || type_arg > 4 || addr_arg < 0 || addr_arg > 63 ||
            bit_arg < 0 || bit_arg > 7)
            $fatal(1, "Invalid fault configuration");
        fault_type = type_arg[2:0];
        fault_addr = addr_arg[5:0];
        fault_bit = bit_arg[2:0];
        mask = 8'h01 << fault_bit;
        other_addr = (fault_addr == 6'd63) ? 6'd0 : fault_addr + 1'b1;

        repeat (2) @(negedge clk);
        rst_n = 1'b1;
        if (fault_type == 3'd1) read_stuck_bit_before_write(1'b0);
        if (fault_type == 3'd2) read_stuck_bit_before_write(1'b1);
        case (fault_type)
            3'd0: begin
                write_check(fault_addr, 8'h00, 0); read_check(fault_addr, 8'h00, 0);
                write_check(fault_addr, 8'hff, 0); read_check(fault_addr, 8'hff, 0);
                write_check(other_addr, 8'ha5, 0); read_check(other_addr, 8'ha5, 0);
                last_expected = 8'hff;
            end
            3'd1: begin
                write_check(fault_addr, 8'h00, 0); read_check(fault_addr, 8'h00, 0);
                write_check(other_addr, 8'hff, 0); read_check(other_addr, 8'hff, 0);
                write_check(fault_addr, 8'hff, 1); read_check(fault_addr, 8'hff & ~mask, 1);
                write_check(fault_addr, 8'hff, 2); read_check(fault_addr, 8'hff & ~mask, 2);
                write_check(fault_addr, 8'h00, 2); read_check(fault_addr, 8'h00, 2);
                last_expected = 8'h00;
            end
            3'd2: begin
                write_check(fault_addr, 8'hff, 0); read_check(fault_addr, 8'hff, 0);
                write_check(other_addr, 8'h00, 0); read_check(other_addr, 8'h00, 0);
                write_check(fault_addr, 8'h00, 1); read_check(fault_addr, mask, 1);
                write_check(fault_addr, 8'h00, 2); read_check(fault_addr, mask, 2);
                write_check(fault_addr, 8'hff, 2); read_check(fault_addr, 8'hff, 2);
                last_expected = 8'hff;
            end
            3'd3: begin
                write_check(fault_addr, 8'hff, 0); read_check(fault_addr, 8'hff, 0);
                write_check(fault_addr, 8'h00, 0); read_check(fault_addr, 8'h00, 0);
                write_check(fault_addr, 8'h00, 0); read_check(fault_addr, 8'h00, 0);
                write_check(fault_addr, 8'h00, 0); read_check(fault_addr, 8'h00, 0);
                write_check(other_addr, 8'hff, 0); read_check(other_addr, 8'hff, 0);
                write_check(fault_addr, 8'hff, 1); read_check(fault_addr, 8'hff & ~mask, 1);
                write_check(fault_addr, 8'hff, 2); read_check(fault_addr, 8'hff & ~mask, 2);
                write_check(fault_addr, 8'h00, 2); read_check(fault_addr, 8'h00, 2);
                last_expected = 8'h00;
            end
            3'd4: begin
                write_check(fault_addr, 8'h00, 0); read_check(fault_addr, 8'h00, 0);
                write_check(fault_addr, 8'hff, 0); read_check(fault_addr, 8'hff, 0);
                write_check(fault_addr, 8'hff, 0); read_check(fault_addr, 8'hff, 0);
                write_check(other_addr, 8'h00, 0); read_check(other_addr, 8'h00, 0);
                write_check(fault_addr, 8'h00, 1); read_check(fault_addr, mask, 1);
                write_check(fault_addr, 8'h00, 2); read_check(fault_addr, mask, 2);
                write_check(fault_addr, 8'hff, 2); read_check(fault_addr, 8'hff, 2);
                last_expected = 8'hff;
            end
        endcase

        // Synchronous reset clears activation bookkeeping and blocks writes,
        // while the storage cell retains its pre-reset value.
        @(negedge clk);
        rst_n = 1'b0;
        req_valid = 1'b1;
        req_write = 1'b1;
        req_addr = fault_addr;
        req_wdata = ~last_expected;
        @(posedge clk);
        #1;
        if (req_ready !== 1'b0 || rd_valid !== 1'b0 ||
            fault_activated !== 1'b0 || activation_count !== 16'd0)
            $fatal(1, "UNIT_FAIL reset behavior");
        @(negedge clk);
        rst_n = 1'b1;
        req_valid = 1'b0;
        read_check(fault_addr, last_expected, 0);
        $display("FAULT_UNIT_PASS type=%0d addr=%0d bit=%0d", fault_type, fault_addr, fault_bit);
        $finish;
    end
    initial begin
        #10000;
        $fatal(1, "Fault RAM unit timeout");
    end
endmodule
