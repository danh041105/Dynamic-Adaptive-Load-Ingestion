import os
from pathlib import Path

folder_path = Path(__file__).parent.parent / "cell_trace_server"

def delete_files() -> None:
    for root,_ , files in os.walk(folder_path):
        for file in files:
            file_path = Path(root) / file
            os.remove(file_path)
            print(f"Deleted: {file_path}")

if __name__ == "__main__":
    delete_files()