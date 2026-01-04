from comfyapi import ComfyAPIManager
from pathlib import Path

here = Path(__file__).parent

manager = ComfyAPIManager()
manager.set_base_url("http://127.0.0.1:8188")
manager.load_workflow(str(here / "workflow.json"))

# Edit workflow if needed (example)
manager.edit_workflow(["6", "inputs", "text"], "a cute anime girl")

num_images = 3  # Number of images to generate in batch

# Submit batch jobs with varying seeds
uids = manager.batch_submit(num_seeds=num_images)
print(f"Batch submitted. Prompt IDs: {uids}")

# Wait for all jobs and get results using wait_and_get_all_outputs
results, errors = manager.wait_and_get_all_outputs(uids, status_callback=lambda uid, status: print(f"UID {uid}: {status}"))
print("Batch finished. Results:", results)
if errors:
    print("Errors:", errors)

# Download all outputs
out_dir = here / "batch_output"
out_dir.mkdir(parents=True, exist_ok=True)
for filename, url in results:
    print(f"Downloading {filename} from {url}")
    manager.download_output(url, save_path=str(out_dir), filename=filename)
    print(f"Downloaded {filename}")
print("All downloads complete.")