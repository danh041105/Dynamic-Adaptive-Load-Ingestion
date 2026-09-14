import os
import random
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

base_dir = Path(__file__).parent.parent / "cell_trace_server"
megaplexers_list = [f"mgpl{i:02d}" for i in range(1, 7)]
total_file = 280
HIGH_TRAFFIC_MEGAPLEXERS = 3
HIGH_TRAFFIC_PAYLOAD_MB = 5
NORMAL_TRAFFIC_PAYLOAD_MB = 2
MAX_WORKERS = 2

def write_file(task: tuple[Path, bytes]) -> None:
    filepath, data = task
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_bytes(data)


def random_ip() -> str:
    """Return an address from the carrier-grade NAT range 100.64.0.0/10."""
    return f"100.{random.randint(64, 127)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def distribute_randomly(
    megaplexers: list[str], total_files: int, high_traffic_count: int
) -> list[int]:
    """Allocate more files to the first high-traffic megaplexers."""
    weights = [
        random.uniform(6.0, 7.0)
        if index < high_traffic_count
        else random.uniform(3.5, 4.5)
        for index in range(len(megaplexers))
    ]
    total_weight = sum(weights)
    allocations = [int(total_files * weight / total_weight) for weight in weights]

    for _ in range(total_files - sum(allocations)):
        allocations[random.randrange(len(allocations))] += 1
    return allocations


def generate_megaplexer_files(
    megaplexer_name: str,
    created_at: datetime,
    payload: bytes,
    num_files: int,
) -> list[tuple[Path, bytes]]:
    """Build write tasks for one megaplexer using the required Nokia layout."""
    tasks = []

    for _ in range(num_files):
        # Each file has a distinct creation time/session, avoiding duplicate names.
        file_time = created_at + timedelta(seconds=random.randint(0, 59))
        date_part = file_time.strftime("%y%m%d")
        minute_part = file_time.strftime("%H%M")
        session_id = random.randint(100000, 999999)
        port = random.randint(10000, 65535)

        filename = (
            f"Ip_;;ffff;{random_ip()}_{port}_{session_id}_"
            f"{file_time.strftime('%y%m%d_%H%M%S')}.lcbin"
        )
        filepath = (
            base_dir / "nokia" / megaplexer_name / date_part / minute_part / filename
        )
        tasks.append((filepath, payload))

    return tasks


def generate_megaplexer_data() -> None:
    """Generate one batch of megaplexer files for a single DAG run."""
    vn_timezone = timezone(timedelta(hours=7))
    created_at = datetime.now(vn_timezone)
    print("[*] Dang chuan bi payload Nokia...")
    high_traffic_payload = os.urandom(HIGH_TRAFFIC_PAYLOAD_MB * 1024 * 1024)
    normal_traffic_payload = os.urandom(NORMAL_TRAFFIC_PAYLOAD_MB * 1024 * 1024)
    allocations = distribute_randomly(
        megaplexers_list, total_file, HIGH_TRAFFIC_MEGAPLEXERS
    )

    all_tasks = []
    for index, megaplexer in enumerate(megaplexers_list ):
        payload = (
            high_traffic_payload
            if index < HIGH_TRAFFIC_MEGAPLEXERS
            else normal_traffic_payload
        )
        all_tasks.extend(
            generate_megaplexer_files(
                megaplexer, created_at, payload, allocations[index]
            )
        )

    print(f"[*] Phan bo file: {dict(zip(megaplexers_list, allocations))}")
    print(f"[*] Dang ghi {len(all_tasks)} file .lcbin cho 6 megaplexer...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        list(executor.map(write_file, all_tasks))
    print("[+] Hoan tat!")

if __name__ == "__main__":
    generate_megaplexer_data()
