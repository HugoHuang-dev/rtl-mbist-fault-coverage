// -----------------------------------------------------------------------------
// Hugo's MBIST Project
// -----------------------------------------------------------------------------
// Author  : sunmingyin.huang@haw-hamburg.de
// Project : RTL-Based MBIST with Automated Fault-Coverage Evaluation
// File    : march_transaction_checker.sv
// Module  : march_transaction_checker
// -----------------------------------------------------------------------------
`timescale 1ns/1ps

// Black-box monitor: only public RAM and result ports are observed. oracle.hex
// is generated from the frozen Step 1 CSV before each regression run.
module march_transaction_checker (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       start,
    input  wire [1:0] run_id,
    input  wire       req_valid,
    input  wire       req_ready,
    input  wire       req_write,
    input  wire [5:0] req_addr,
    input  wire [7:0] req_wdata,
    input  wire       rd_valid,
    input  wire [7:0] rd_data,
    input  wire       done,
    input  wire       pass,
    input  wire       fail,
    input  wire [8:0] error_count,
    input  wire [2:0] first_fail_phase,
    input  wire [5:0] first_fail_addr,
    input  wire [7:0] first_fail_expected,
    input  wire [7:0] first_fail_actual
);
    reg [17:0] oracle [0:639]; // {phase[2:0], address[5:0], write, data[7:0]}
    integer request_count = 0;
    integer expected_errors = 0;
    integer cycles = 0;
    reg active = 1'b0;
    reg finished = 1'b0;
    reg pending = 1'b0;
    reg [2:0] pending_phase;
    reg [5:0] pending_addr;
    reg [7:0] pending_expected;
    reg [2:0] expected_first_phase;
    reg [5:0] expected_first_addr;
    reg [7:0] expected_first_data;
    reg [7:0] expected_first_actual;
    reg [17:0] row;

    initial $readmemh("oracle.hex", oracle);

    // Failure codes: 1 address, 2 operation, 3 write data,
    // 4 comparison/response timing, 5 completion, 6 first diagnosis.
    task automatic reject(input integer code);
        begin
            $display("CHECKER_FAIL code=%0d run=%0d request=%0d cycle=%0d",
                     code, run_id, request_count, cycles);
            $fatal(1, "Independent checker rejected DUT");
        end
    endtask

    always @(posedge clk) begin
        if (!rst_n) begin
            active = 1'b0;
            finished = 1'b0;
            pending = 1'b0;
            request_count = 0;
            expected_errors = 0;
            cycles = 0;
        end else if (start && (!active || finished)) begin
            active = 1'b1;
            finished = 1'b0;
            pending = 1'b0;
            request_count = 0;
            expected_errors = 0;
            cycles = 0;
            #1;
            if (done !== 1'b0 || fail !== 1'b0 || error_count !== 9'd0)
                reject(5);
        end else if (active) begin
            // A start pulse during a run is ignored by the DUT specification;
            // keep checking the same transaction stream without resetting.
            cycles = cycles + 1;
            if (cycles > 1500)
                reject(5);
            if (finished) begin
                if (req_valid !== 1'b0 || done !== 1'b1)
                    reject(5);
            end else begin
                // At the active edge these are the prior request's registered
                // response values, as sampled by a synchronous controller.
                if (rd_valid) begin
                    if (!pending)
                        reject(4);
                    if (rd_data !== pending_expected) begin
                        if (expected_errors == 0) begin
                            expected_first_phase = pending_phase;
                            expected_first_addr = pending_addr;
                            expected_first_data = pending_expected;
                            expected_first_actual = rd_data;
                        end
                        expected_errors = expected_errors + 1;
                    end
                    pending = 1'b0;
                end

                if (req_valid && req_ready) begin
                    if (request_count >= 640)
                        reject(5);
                    if (pending)
                        reject(2); // V1.0 allows only one outstanding read.
                    row = oracle[request_count];
                    if (req_addr !== row[14:9])
                        reject(1);
                    if (req_write !== row[8])
                        reject(2);
                    if (req_write && req_wdata !== row[7:0])
                        reject(3);
                    if (!req_write) begin
                        pending = 1'b1;
                        pending_phase = row[17:15];
                        pending_addr = row[14:9];
                        pending_expected = row[7:0];
                    end
                    request_count = request_count + 1;
                end

                #1; // DUT result registers update in NBA after the same edge.
                if (error_count !== expected_errors[8:0] ||
                    fail !== (expected_errors != 0))
                    reject(4);
                if (expected_errors != 0 &&
                    (first_fail_phase !== expected_first_phase ||
                     first_fail_addr !== expected_first_addr ||
                     first_fail_expected !== expected_first_data ||
                     first_fail_actual !== expected_first_actual))
                    reject(6);
                if (done) begin
                    if (request_count != 640 || pending)
                        reject(5);
                    if (pass !== (expected_errors == 0))
                        reject(5);
                    finished = 1'b1;
                    $display("CHECKER_PASS run=%0d requests=%0d cycles=%0d errors=%0d",
                             run_id, request_count, cycles, expected_errors);
                end
            end
        end
    end
endmodule
