"""Create a portable ILA copy, preserving samples and the original capture."""
import json
import re
from zipfile import ZipFile, ZIP_DEFLATED
from project_config import ROOT, result_dir

def main():
    original = ROOT / "results/step08/hardware/ila_capture/2026-09-26_march_c_minus_64x8_full_run.ila"
    out = result_dir("portable_ila")
    out.mkdir(parents=True, exist_ok=True)
    target = out / "march_c_minus_64x8_portable.ila"
    entries = []
    with ZipFile(original) as source, ZipFile(target, "w", ZIP_DEFLATED) as destination:
        for name in source.namelist():
            before = source.read(name)
            after = before
            if name.endswith(".wcfg"):
                text = before.decode("utf-8")
                text, count = re.subn(r'(<db_ref\s+path=")[^"]*[/\\]([^/\\"]+\.wdb)(")',
                                     r'\1\2\3', text)
                if count != 1:
                    raise ValueError("Expected exactly one waveform database reference")
                after = text.encode("utf-8")
            destination.writestr(name, after)
            entries.append({"entry": name, "changed": before != after})
    if [row["entry"] for row in entries if row["changed"]] != ["hw_ila_data_1.wcfg"]:
        raise ValueError("Unexpected capture changes")
    with ZipFile(target) as reopened:
        if reopened.testzip() is not None:
            raise ValueError("Invalid archive CRC")
        (out / "portable_capture.wdb").write_bytes(reopened.read("hw_ila_data_1.wdb"))
        # A standalone view is optional; the original probe names are preserved.
        view = reopened.read("hw_ila_data_1.wcfg").decode("utf-8")
        view = view.replace('path="hw_ila_data_1.wdb"', 'path="portable_capture.wdb"')
        (out / "portable_capture.wcfg").write_text(view, encoding="utf-8")
    report = {"original": original.relative_to(ROOT).as_posix(),
              "entries": entries}
    (out / "conversion.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PORTABLE_ILA_COPY_PASS samples_unchanged=true original_unchanged=true")

if __name__ == "__main__":
    main()
