from pathlib import Path
import os

base_dir = Path(__file__).parent.parent / "cell_trace_server" / "ericsson"

enms = ["enm01", "enm02", "enm03", "enm04", "enm05"]
for enm in enms:
    enm_dir = base_dir / enm
    if enm_dir.exists() and enm_dir.is_dir():
        total_files = sum(len(files) for _, _, files in os.walk(enm_dir))
        print(f"{enm}: {total_files} files")
    else:
        print(f"{enm}: Directory does not exist")