from backend.clients.nifi_client import NifiClient


client = NifiClient()

print("=== AUTH ===")
client.auth.authenticate()
print("Authentication OK")


print("\n=== ROOT PROCESS GROUP ===")

root = (
    client
    .process_groups
    .get_root_process_group()
)

print(root)