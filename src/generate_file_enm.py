import os
import gzip
import random
from datetime import datetime, timezone, timedelta
from time import perf_counter
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

base_dir = Path(__file__).parent.parent / "cell_trace_server"
enms_list = [f"enm{i:02d}" for i in range(1, 6)] # 5 cụm enm
enms_hw = ["DUL1_3", "DUS41_1", "BB5216_1", "BB6630_1"] # phần cứng của các con ENM

TOTAL_FILES = 1500
SPIKE_TRAFFIC_ENM_INDICES = {0, 2}  # ENM01 và ENM03
LARGE_PAYLOAD_ENMS = 3


def write_file(task: tuple[Path, bytes]) -> None:
    filepath, data = task
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with filepath.open("wb") as f:
        f.write(data)

# Random sinh số lượng file khác nhau với các enm khác nhau
# Tổng có 1700 file: ENM01 và ENM03 tăng đột biến, khoảng 650 file/ENM
# ENM02, ENM04 và ENM05 nhận khoảng 130 file/ENM

def distribute_randomly(
    enms_list: list[str], total_files: int, spike_indices: set[int]
) -> list[int]:
    weights = []
    for idx in range(len(enms_list)):
        if idx in spike_indices:
            weights.append(random.uniform(16.0, 18.0))
        else:
            weights.append(random.uniform(3.0, 4.0))

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
            # enm_hw lặp lại sau mỗi 4 file. Thêm file_idx để các file trong
            # cùng eNodeB không trùng tên và bị ghi đè.
            file_name = f"{ts}_{dn}_{file_idx:05d}.bin.gz"
            tasks.append((enm_dir/file_name, enm_payload))
    return tasks

def generate_enm_data() -> None:

    # timedelta(hours=7): Biểu diễn một khoảng chênh lệch thời gian là 7 giờ.
    # timezone(): Lớp đại diện cho múi giờ trong module datetime. Khi nhận tham số là timedelta(hours=7), 
    # nó tạo ra một đối tượng múi giờ có offset cố định là +07:00 so với UTC.
    # vn_timezone: Biến lưu đối tượng múi giờ này để gán vào các đối tượng datetime.
    vn_timezone = timezone(timedelta(hours=7))
    date_hour = (datetime.now(vn_timezone))

    total_started = perf_counter()
    started_at = datetime.now(vn_timezone)

    payload_started = perf_counter()
    
    enm0103_payload = gzip.compress(os.urandom(7 * 1024 * 1024), compresslevel=1)
    enm0405_payload = gzip.compress(os.urandom(3 * 1024 * 1024), compresslevel=1)

    print(f"[*] Payload preparation: {perf_counter() - payload_started:.2f} seconds")
    allocations = distribute_randomly(
        enms_list, TOTAL_FILES, SPIKE_TRAFFIC_ENM_INDICES
    )

    all_enm_tasks = []
    for idx, enm in enumerate(enms_list):
        # trọng số phân bổ file của từng ENM
        num_files_for_enm = allocations[idx]
        if idx < LARGE_PAYLOAD_ENMS:  # ENM 01, 02, 03 sẽ có payload lớn hơn
            payload = enm0103_payload
        else: payload = enm0405_payload

        enm_tasks = generate_enm_file(
            enm, enms_list, enms_hw, date_hour, "eHA", payload, "HN",
            num_files_for_enm,
        )
        all_enm_tasks.extend(enm_tasks)

    print(f"write {len(all_enm_tasks)} files in disk...")

    total_bytes = sum(len(data) for _, data in all_enm_tasks)

    write_started = perf_counter()
    with ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(write_file, all_enm_tasks))

    write_seconds = perf_counter() - write_started
    total_seconds = perf_counter() - total_started
    write_speed_mib = total_bytes / (1024 * 1024) / write_seconds if write_seconds else 0

    print(f"Started at: {started_at:%Y-%m-%d %H:%M:%S %z}")
    print(f"Write time: {write_seconds:.2f} seconds ({write_speed_mib:.2f} MiB/s)")
    print(f"Total generation time: {total_seconds:.2f} seconds")
        
    print("Completed!")

if __name__ == "__main__":
    generate_enm_data() 
