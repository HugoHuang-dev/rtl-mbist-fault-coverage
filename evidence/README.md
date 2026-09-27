# Source and Experiment Records

Current source headers retain author, project, file, and module. Byte-exact current code hashes are in the [source SHA-256 manifest](current_source_sha256.txt). Source and documents from before the engineering revision are archived in `revisions/2026-09-26_before_engineering_review.zip` without rewriting the originals.

| File | Record |
| --- | --- |
| `frozen_source_before_headers.zip` | Source snapshot before the initial project packaging |
| [frozen_source_sha256.txt](frozen_source_sha256.txt) | Member hashes of the original snapshot |
| [source_header_manifest.csv](source_header_manifest.csv) | Earlier header inventory, retained as history |
| [step07_source_sha256_before_headers.txt](step07_source_sha256_before_headers.txt) | Original evaluation-source hashes |
| [step08_source_sha256_before_headers.txt](step08_source_sha256_before_headers.txt) | Original implementation-audit source hashes |
| [step08_hardware_sha256_before_packaging.txt](step08_hardware_sha256_before_packaging.txt) | Original board-file hashes |
| [release checks](release_checks/README.md) | Regression records from project packaging |

The original v6 campaign fingerprints refer to the original source snapshot. Comparisons of RTL/testbench bodies ignore headers and CRLF/LF differences. Revised run logs and source snapshots are kept under the corresponding `results/reruns/` ID.

A later full campaign under `results/reruns/20260926_engineering_review/step06/` retains its own `source_snapshot.zip`, `source_sha256.txt`, and raw logs. Every structured result contains its raw-log hash. The [engineering review](../docs/09_engineering_review.md) describes the current board build.

During initial packaging, absolute build directories in some logs were normalized to `<PROJECT_ROOT>` or `<WORK_ROOT>`. Numerical results were unchanged and log hashes were recomputed. Those earlier files are retained; new logs save tool output as produced. Native ILA originals and hashes are retained, with portable copies stored separately.

## Final checks

The [board evidence](../results/step08/hardware_final/README.md) includes 17 original files and audits of five ILA runs. The [repository check](release_checks/github_package_check.json) records publication-package checks; [SHA256SUMS.txt](../SHA256SUMS.txt) covers the supplied files. Earlier translation and archive manifests remain with the original project records. See [repository contents](../REPOSITORY_CONTENTS.md) for the generated files excluded from this repository.
