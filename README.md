# ComfyAPI Client

A Python client library for interacting with a running ComfyUI instance via its API. Allows you to programmatically queue workflows, monitor progress, and retrieve outputs.

## Features

*   Load ComfyUI workflow JSON files.
*   Edit workflow parameters (prompts, seeds, dimensions, etc.).
*   Submit single workflows for execution.
*   Submit batches of workflows with varying seeds.
*   Wait for job completion (single or batch).
*   Retrieve output image URLs.
*   Download output images.
*   Concurrent handling of batch jobs.

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

### Basic Example (Single Image)

```python
import comfyapi

# 1. Set the URL of your ComfyUI server
comfyapi.set_base_url("http://127.0.0.1:8188") # Replace with your server URL

# 2. Load your workflow file
workflow = comfyapi.load_workflow("path/to/your/workflow.json")

# 3. Modify workflow parameters (optional)
# Example: Change positive prompt (assuming node "6" is the positive prompt node)
workflow = comfyapi.edit_workflow(workflow, ["6", "inputs", "text"], "a beautiful landscape painting")
# Example: Change seed (assuming node "3" is the KSampler seed input)
workflow = comfyapi.edit_workflow(workflow, ["3", "inputs", "seed"], 12345)

try:
    # 4. Submit the workflow
    print("Submitting workflow...")
    prompt_id = comfyapi.submit(workflow)
    print(f"Workflow submitted. Prompt ID: {prompt_id}")

    # 5. Wait for the job to finish
    print("Waiting for job to finish...")
    # You can optionally provide a status callback function:
    # def my_status_callback(pid, status):
    #     print(f"Job {pid}: {status}")
    # comfyapi.wait_for_finish(prompt_id, status_callback=my_status_callback)
    # wait_for_finish now returns (filename, url)
    filename, output_url = comfyapi.wait_for_finish(prompt_id)
    print(f"Job finished. Filename: {filename}, Output URL: {output_url}")

    # 6. Download the output image (find_output_url call is no longer needed here)
    if output_url:
        print("Downloading output...")
        # Saves to current directory with filename from URL
        saved_path = comfyapi.download_output(output_url, save_path="output_images")
        # Or specify a filename:
        # saved_path = comfyapi.download_output(output_url, save_path="output_images", filename="my_image.png")
        print(f"Image saved to: {saved_path}")

except comfyapi.ComfyAPIError as e:
    print(f"An API error occurred: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

```

### Batch Example (Multiple Seeds - Automatic Generation)

```python
import comfyapi
import time

# 1. Set the URL
comfyapi.set_base_url("http://127.0.0.1:8188")

# 2. Load workflow
workflow = comfyapi.load_workflow("path/to/your/workflow.json")

# 3. Define number of seeds and the path to the seed node
num_images_to_generate = 5
# IMPORTANT: Update this path based on your specific workflow JSON structure!
# Find the node that takes the seed (e.g., KSampler) and its input name.
seed_node_path = ["3", "inputs", "seed"] # Example: Node "3", input named "seed"

try:
    # 4. Submit the batch using num_seeds for automatic seed generation
    print(f"Submitting batch for {num_images_to_generate} images (random seeds)...")
    # Provide num_seeds instead of an explicit seeds list
    uids = comfyapi.batch_submit(workflow, seed_node_path, num_seeds=num_images_to_generate)
    print(f"Batch submitted. UIDs: {uids}")

    # 5. Wait for all jobs and get results
    print("Waiting for all jobs to finish...")
    # Optional status callback for batch progress
    def batch_status_update(uid, status):
         print(f"  Job {uid}: {status}")
    # This function waits concurrently and returns (results_list, errors_list)
    results_list, errors_list = comfyapi.wait_and_get_all_outputs(uids, status_callback=batch_status_update)

    print("\n--- Batch Results ---")
    # 6. Process successful results
    if results_list:
        print("Successful jobs:")
        # results_list contains (filename, output_url) tuples
        for filename, output_url in results_list:
            print(f"  Filename: {filename}, Output URL: {output_url}")
            # Download each image into the 'batch_output' folder using its original filename
            try:
                # Pass the URL and the desired filename to download_output
                saved_path = comfyapi.download_output(output_url, save_path="batch_output", filename=filename)
                print(f"    Downloaded: {saved_path}")
            except comfyapi.ComfyAPIError as dl_e:
                print(f"    Error downloading {filename}: {dl_e}")
            time.sleep(0.1) # Small delay

    # 7. Report errors
    if errors_list:
        print("\nFailed jobs/errors:")
        # errors_list contains error objects/strings
        for error in errors_list:
            print(f"  Error: {error}")

except comfyapi.ComfyAPIError as e:
    print(f"An API error occurred during batch processing: {e}")
except ValueError as e:
     print(f"Configuration error: {e}") # e.g., invalid seed path
except Exception as e:
    print(f"An unexpected error occurred: {e}")

```

## API Reference

*(TODO: Add detailed descriptions of public functions and exceptions here)*

*   `set_base_url(url)`
*   `load_workflow(filepath)`
*   `edit_workflow(workflow, path, value)`
*   `submit(workflow)`
*   `batch_submit(workflow, seed_node_path, seeds=None, num_seeds=None)`
*   `wait_for_finish(prompt_id, poll_interval=3, max_wait_time=600, status_callback=None)` (Returns `(filename, output_url)`)
*   `find_output_url(prompt_id)` (Can still be used to check history for already completed jobs)
*   `wait_and_get_all_outputs(uids, status_callback=None)` (Returns `(results_list, errors_list)` where `results_list` is `[(filename, output_url), ...]`)
*   `download_output(output_url, save_path=".", filename=None)`
*   Exceptions: `ComfyAPIError`, `ConnectionError`, `QueueError`, `HistoryError`, `ExecutionError`, `TimeoutError`

## Contributing

*(TODO: Add contribution guidelines if desired)*

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
