# Source Checksums and Experiment Inputs

[current_source_sha256.txt](current_source_sha256.txt) covers maintained source, constraints, and scripts. Original experiment fingerprints remain in their respective `results/` run directories and continue to identify the files used at the time.

Two source archives are retained for historical experiment checks:

- [frozen_source_before_headers.zip](frozen_source_before_headers.zip): early v6–v8 source, used by `scripts/frozen_source.py` and `audit_step08.py`. Its original manifests are [frozen_source_sha256.txt](frozen_source_sha256.txt) and [step08_source_sha256_before_headers.txt](step08_source_sha256_before_headers.txt).
- [asic_integration/source_snapshot.zip](asic_integration/source_snapshot.zip): original ASIC experiment source, used by `asic/scripts/source_provenance.py`. The [shared-source comparison](asic_integration/shared_file_comparison.json) retains byte and source-body comparisons.

Comparisons between historical RTL and current implementation allow only recognized project-header and line-ending differences. Configuration and SDC are compared byte for byte. Current source checksums do not replace historical manifests.

Earlier archiving normalized some log paths to `<PROJECT_ROOT>` or `<WORK_ROOT>` and updated corresponding log hashes; those files are retained as recorded. Local absolute project-root paths in ASIC logs and `toolchain.txt` are normalized to `.`, relative to the project root. Only path text is changed; experiment parameters, dates, and numerical results are preserved. Associated log checksums identify the normalized files. Native ILA data is unchanged.
