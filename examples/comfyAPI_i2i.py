from comfyapi import ComfyAPIManager
import time
from pathlib import Path

here = Path(__file__).parent


def status_cb(uid, status):
    print(f"[STATUS] {uid}: {status}")

manager = ComfyAPIManager()
manager.set_base_url("http://127.0.0.1:8188")

# SINGLE RUN: inject base64 image and run
manager.load_workflow(str(here / "workflw.json"))
manager.edit_workflow(["6", "inputs", "text"], "A cinematic portrait of a person on a beach")
manager.edit_workflow(["3", "inputs", "seed"], 42)

# Inject a local image into Base64ImageLoader (node id 10 in the example workflow)
manager.set_base64_image(node_id="10", image_path=str(here / "example.png"))

prompt_id = manager.submit_workflow()
print("Submitted single workflow:", prompt_id)
filename, output_url = manager.wait_for_finish(prompt_id, status_callback=status_cb)
print("Single finished:", filename, output_url)

out_dir = here / "outputs"
out_dir.mkdir(parents=True, exist_ok=True)
manager.download_output(output_url, save_path=str(out_dir), filename=filename)

# BATCH RUN: random seeds and wait concurrently
manager.load_workflow(str(here / "workflow.json"))
manager.edit_workflow(["6", "inputs", "text"], "A stylized concept art landscape")

uids = manager.batch_submit(num_seeds=4, random_seeds=True)
print("Submitted batch:", uids)
results, errors = manager.wait_and_get_all_outputs(uids, status_callback=status_cb)
print("Batch results:", results)
if errors:
    print("Errors during batch:", errors)

for filename, url in results:
    manager.download_output(url, save_path=str(out_dir), filename=filename)

print("All done.")