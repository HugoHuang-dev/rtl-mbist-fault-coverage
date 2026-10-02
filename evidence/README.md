# Experiment Inputs

Two source archives are retained for historical experiment checks:

- [frozen_source_before_headers.zip](frozen_source_before_headers.zip): early v6–v8 source, used by `scripts/frozen_source.py`.
- [asic_integration/source_snapshot.zip](asic_integration/source_snapshot.zip): original ASIC experiment source, used by `asic/scripts/source_provenance.py`. The [shared-source comparison](asic_integration/shared_file_comparison.json) retains byte and source-body comparisons.

Comparisons between historical RTL and current implementation allow only recognized project-header and line-ending differences. Configuration and SDC are compared byte for byte.

Earlier archiving normalized some log paths to `<PROJECT_ROOT>` or `<WORK_ROOT>`; those files are retained as recorded. Local absolute project-root paths in ASIC logs and `toolchain.txt` are normalized to `.`, relative to the project root. Only path text is changed; experiment parameters, dates, and numerical results are preserved. Native ILA data is unchanged.
