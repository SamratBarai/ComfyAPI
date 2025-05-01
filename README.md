# ComfyAPI Client

A Python client library for interacting with a running ComfyUI instance via its API. Allows you to programmatically queue workflows, monitor progress, and retrieve outputs.

## Features

*   Load ComfyUI workflow JSON files.
*   Edit workflow parameters (prompts, seeds, dimensions, etc.) programmatically.
*   Submit single or batch workflows for execution.
*   Wait for job completion (single or batch) with non-blocking polling.
*   Retrieve output image URLs and download outputs.
*   Designed for automation, scripting, and integration with UIs (e.g., Gradio, Flask).

## Installation

```bash
pip install comfyapi-client # Or: pip install . if installing from local source
```
*(Note: Package name on PyPI might differ if 'comfyapi-client' is taken. Check `setup.py`)*

**Dependencies:**

*   `requests`
*   `websocket-client`

These will be installed automatically via pip.

## Usage

### Recommended: ComfyAPIManager (Single & Batch)

```python
from comfyapi import ComfyAPIManager
import time

manager = ComfyAPIManager()
manager.set_base_url("http://127.0.0.1:8188")
manager.load_workflow("path/to/your/workflow.json")

# Edit workflow parameters (example: prompt and seed)
manager.edit_workflow(["6", "inputs", "text"], "a beautiful landscape painting")
manager.edit_workflow(["3", "inputs", "seed"], 123456)

# Submit workflow
prompt_id = manager.submit_workflow()

# Wait for completion
while not manager.check_queue(prompt_id):
    print("Workflow running...")
    time.sleep(1)
print("Workflow finished!")

# Retrieve and download output
output_url, filename = manager.find_output(prompt_id, with_filename=True)
manager.download_output(output_url, save_path="output_images", filename=filename)
```

### Batch Example (Multiple Images, Automatic Seeds)

```python
# Number of images to generate
num_images = 5
# Path to the seed input in your workflow (update as needed)
seed_node_path = ["3", "inputs", "seed"]

uids = manager.batch_submit(num_seeds=num_images, seed_node_path=seed_node_path)
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
    manager.download_output(output_url, save_path="batch_output", filename=filename)
    print(f"Downloaded {filename}")
print("All downloads complete.")
```

### Legacy API (Functional, Not Recommended)

```python
import comfyapi

comfyapi.set_base_url("http://127.0.0.1:8188")
workflow = comfyapi.load_workflow("path/to/your/workflow.json")
workflow = comfyapi.edit_workflow(workflow, ["6", "inputs", "text"], "a beautiful landscape painting")
workflow = comfyapi.edit_workflow(workflow, ["3", "inputs", "seed"], 12345)

prompt_id = comfyapi.submit(workflow)
filename, output_url = comfyapi.wait_for_finish(prompt_id)
comfyapi.download_output(output_url, save_path="output_images")
```

## API Reference (Key Methods)

### ComfyAPIManager
- `set_base_url(url)`
- `load_workflow(filepath)`
- `edit_workflow(path, value)`
- `submit_workflow()`
- `batch_submit(num_seeds=None, seeds=None, seed_node_path=[...])`
- `check_queue(prompt_id)`
- `find_output(prompt_id, with_filename=False)`
- `wait_for_finish(prompt_id, poll_interval=3, max_wait_time=600, status_callback=None)`
- `wait_and_get_all_outputs(uids, status_callback=None)`
- `download_output(output_url, save_path=".", filename=None)`

### Exceptions
- `ComfyAPIError`, `ConnectionError`, `QueueError`, `HistoryError`, `ExecutionError`, `TimeoutError`

## Notes
- Always update the seed node path based on your workflow structure.
- All editing is non-destructive: the workflow is copied and updated in memory.
- Use the Manager for all new scripts and integrations.

## Contributing

*(TODO: Add contribution guidelines if desired)*

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
