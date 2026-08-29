import os
import gzip
import random
from datetime import datetime, time, timezone, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import time

base_dir = Path(__file__).parent.parent / "cell_trace_server"
enms_list = [f"enm{i:02d}" for i in range(1, 11)] # 10 cụm enm
enms_hw = ["DUL1_3", "DUS41_1", "BB5216_1", "BB6630_1"] # phần cứng của các con ENM


def write_file(task: tuple[Path, bytes]) -> None:
    filepath, data = task
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open("wb") as f:
        f.write(data)

# Random sinh số lượng file khác nhau với các enm khác nhau
# Tổng có 500 file: 4 ENM sẽ có trọng số cao hơn sẽ có nhiều file hơn, các ENMS khác trung bình 40 file
# 4 ENM đầu sẽ có 50 file mỗi file 8mb
# 6 ENM sau sẽ có 40 file mỗi file 3mb

def distribute_randomly(enms_list: list, total_files: int, idx_requirements: int) -> list: 
    weights = []
    for idx in range(len(enms_list)):
        if idx < idx_requirements:
            weights.append(random.uniform(6.0, 7.0))
        else: 
            weights.append(random.uniform(3.5, 4.5))

    total_weight = sum(weights)
    allocations = [int(total_files * (w / total_weight)) for w in weights]
    for _ in range(total_files - sum(allocations)):
        allocations[random.randrange(len(allocations))] += 1
    return allocations

def generate_enm_file(enm_name: str, enms_list: list, enms_hw: list, 
                    date_hour: datetime, enm_prefix: str, enm_payload: bytes,
                    province: str, num_files: int) -> list[tuple[Path, bytes]]:
    tasks = []
    enm_id = int(enm_name[-2:]) # lấy ra id của enm. Ví dụ enm01
    enodeB_weights = [random.uniform(0.8, 1.2) for _ in range(len(enms_list))]

    # Phân bổ số lượng file ra các enodeB khác nhau
    total_enodeB_count = sum(enodeB_weights)
    enodeB_allocations = [int(num_files * (w / total_enodeB_count)) for w in enodeB_weights]
    for _ in range(num_files - sum(enodeB_allocations)):
        enodeB_allocations[random.randrange(len(enodeB_allocations))] += 1

    for enodeB_idx in range(len(enms_list)):
        files_for_enodeB = enodeB_allocations[enodeB_idx]
        
        enodeB_id = f"{enm_prefix}{enm_id:02d}{enodeB_idx+1:03d}"
        # Ví dụ: {eha}{01}{001}
        for file_idx in range(files_for_enodeB):

            ts = f"A{(date_hour - timedelta(minutes=1)).strftime('%Y%m%d.%H%M%z')}-{(date_hour).strftime('%H%M%z')}"
    
            enm_hw = enms_hw[(enodeB_idx + file_idx + 1) % len(enms_hw)]
            dn = f"SubNetwork={province},MeContext={enodeB_id},ManagedElement={enodeB_id}_celltracefile_{enm_hw}"
            
            enm_dir = base_dir / "ericsson" / enm_name / "CELLTRACE"
            file_name = f"{ts}_{dn}.gz"
            tasks.append((enm_dir/file_name, enm_payload))
    return tasks

def generate_enm_data() -> list[tuple[Path, bytes]]:

    # timedelta(hours=7): Biểu diễn một khoảng chênh lệch thời gian là 7 giờ.
    # timezone(): Lớp đại diện cho múi giờ trong module datetime. Khi nhận tham số là timedelta(hours=7), 
    # nó tạo ra một đối tượng múi giờ có offset cố định là +07:00 so với UTC.
    # vn_timezone: Biến lưu đối tượng múi giờ này để gán vào các đối tượng datetime.
    vn_timezone = timezone(timedelta(hours=7))
    date_hour = (datetime.now(vn_timezone))
    
    print("[*] Đang chuẩn bị payload...")
    enm0104_payload = gzip.compress(os.urandom(7 * 1024 * 1024), compresslevel=1)
    enm0510_payload = gzip.compress(os.urandom(3 * 1024 * 1024), compresslevel=1)

    allocations = distribute_randomly(enms_list, 820, 4) 

    all_enm_tasks = []
    for idx, enm in enumerate(enms_list):
        # trọng số phân bổ file của từng ENM
        num_files_for_enm = allocations[idx]
        if idx < 4:
            payload = enm0104_payload
        else: payload = enm0510_payload

        enm_tasks = generate_enm_file(
            enm, enms_list, enms_hw, date_hour, "eHA", payload, "HN",
            num_files_for_enm,
        )
        all_enm_tasks.extend(enm_tasks)

    print(f"Đang ghi tổng cộng {len(all_enm_tasks)} files vào ổ cứng...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(write_file, all_enm_tasks))
        
    print("Hoàn tất!")

if __name__ == "__main__":
    generate_enm_data() 