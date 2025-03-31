import comfyapi
import time

# 1. Set the URL
comfyapi.set_base_url("https://malawi-operations-accessibility-innocent.trycloudflare.com/")

# 2. Load workflow
workflow = comfyapi.load_workflow("E:\\projects\\softwares\\ComfyAPI\\example\\workflow.json")

workflow = comfyapi.edit_workflow(workflow, ["6", "inputs", "text"], 'a cute anime girl with adorable face and massive breasts')
# 3. Define number of seeds and the path to the seed node
num_images_to_generate = 2

try:
    # 4. Submit the batch using num_seeds for automatic seed generation
    print(f"Submitting batch for {num_images_to_generate} images (random seeds)...")
    # Provide num_seeds instead of an explicit seeds list
    uids = comfyapi.batch_submit(workflow, num_seeds=num_images_to_generate)
    print(f"Batch submitted. UIDs: {uids}")

    # 5. Wait for all jobs and get results
    print("Waiting for all jobs to finish...")

    # This function waits concurrently
    results, errors = comfyapi.wait_and_get_all_outputs(uids)
    print(results)

    print("\n--- Batch Results ---")
    # 6. Process successful results
    if results:
        print("Successful jobs:")
        for file, output_url in results:
            # Download each image into the 'batch_output' folder using its original filename
            try:
                # Call download_output without specifying a filename; it will extract the filename from the URL.
                saved_path = comfyapi.download_output(output_url, ".", file)
                print(f"    Downloaded: {saved_path}")
            except: pass
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
