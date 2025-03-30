import comfyapi
import time

# 1. Set the URL
comfyapi.set_base_url("https://marion-tokyo-sporting-baths.trycloudflare.com/")

# 2. Load workflow
workflow = comfyapi.load_workflow("E:\\projects\\softwares\\Gradio\\api\\workflow.json")

# 3. Define number of seeds and the path to the seed node
num_images_to_generate = 1
# IMPORTANT: Update this path based on your specific workflow JSON structure!
# Find the node that takes the seed (e.g., KSampler) and its input name.
seed_node_path = ["3", "inputs", "seed"] # Example: Node "3", input named "seed"

try:
    # 4. Submit the batch using num_seeds for automatic seed generation
    print(f"Submitting batch for {num_images_to_generate} images (random seeds)...")
    # Provide num_seeds instead of an explicit seeds list
    uids = comfyapi.batch_submit(workflow, num_seeds=num_images_to_generate)
    print(f"Batch submitted. UIDs: {uids}")

    # 5. Wait for all jobs and get results
    print("Waiting for all jobs to finish...")
    # Optional status callback for batch progress
    def batch_status_update(uid, status):
        print(f"  Job {uid}: {status}")
    # This function waits concurrently
    results, errors = comfyapi.wait_and_get_all_outputs(uids, status_callback=batch_status_update)

    print("\n--- Batch Results ---")
    # 6. Process successful results
    if results:
        print("Successful jobs:")
        for uid, output_url in results.items():
            print(f"  UID: {uid}, Output URL: {output_url}")
            # Download each image into the 'batch_output' folder using its original filename
            try:
                # Call download_output without specifying a filename; it will extract the filename from the URL.
                saved_path = comfyapi.download_output(output_url, save_path="batch_output")
                print(f"    Downloaded: {saved_path}")
            except comfyapi.ComfyAPIError as dl_e:
                print(f"    Error downloading {uid} ({output_url}): {dl_e}")
            time.sleep(0.1) # Small delay

    # 7. Report errors
    if errors:
        print("\nFailed jobs:")
        for uid, error in errors.items():
            print(f"  UID: {uid}, Error: {error}")

except comfyapi.ComfyAPIError as e:
    print(f"An API error occurred during batch processing: {e}")
except ValueError as e:
     print(f"Configuration error: {e}") # e.g., invalid seed path
except Exception as e:
    print(f"An unexpected error occurred: {e}")
