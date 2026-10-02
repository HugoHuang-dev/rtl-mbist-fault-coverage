# Portable Copy of the Original ILA

`march_c_minus_64x8_portable.ila` changes only the internal WCFG reference to the WDB filename in the same directory. The original remains under `results/step08/hardware/ila_capture/`.

[`conversion.json`](conversion.json) checks ZIP members. WDB, CSV, VCD, LTX, and DMP bytes are identical; only the WCFG path changes. Vivado 2018.3 imported the copy using `read_hw_ila_data`. The separate WDB/WCFG files also opened; see the [log](reopen.log).

An independent waveform viewer showed an object-name resolution message for `u_mbist/phase`; phase values were checked in native ILA/CSV. Neither original nor copy could re-export CSV through offline batch mode; the existing CSV was extracted directly from the archive and checked byte for byte.

To reproduce, set `MBIST_RUN_ID`, run `py -3 scripts/prepare_portable_ila.py`, then use Vivado 2018.3 with `fpga/verify_portable_ila.tcl`. New copies go into that run ID's `portable_ila/` directory.
