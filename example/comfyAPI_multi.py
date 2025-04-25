from comfyapi import ComfyAPIManager
import time

manager = ComfyAPIManager()
manager.set_base_url("http://127.0.0.1:8188")
manager.load_workflow("E:\projects\softwares\ComfyAPI - Class\example\workflow.json")

# Edit workflow if needed (example)
manager.edit_workflow(["6", "inputs", "text"], "a cute anime girl")

num_images = 3  # Number of images to generate in batch

# Submit batch jobs with varying seeds
uids = manager.batch_submit(num_seeds=num_images)
print(f"Batch submitted. Prompt IDs: {uids}")

# Wait for all jobs to finish
pending = set(uids)
results = {}
while pending:
    finished = []
    for uid in list(pending):
        if manager.check_queue(uid):
            output_url, filename = manager.find_output(uid, with_filename=True)
            results[uid] = (output_url, filename)
            print(f"Prompt {uid} finished! Output: {filename}")
            finished.append(uid)
    for uid in finished:
        pending.remove(uid)
    if pending:
        print(f"Waiting for {len(pending)} jobs...")
        time.sleep(1)

# Download all outputs
for uid, (output_url, filename) in results.items():
    print(f"Downloading {filename} from {output_url}")
    manager.download_output(output_url, save_path=".", filename=filename)
    print(f"Downloaded {filename}")
print("All downloads complete.")