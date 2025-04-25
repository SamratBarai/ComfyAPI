from comfyapi import ComfyAPIManager
import time

# Initialize manager
manager = ComfyAPIManager()

# Set Base Url
manager.set_base_url("http://127.0.0.1:8188")

# Load workflow
manager.load_workflow("E:\projects\softwares\ComfyAPI - Class\example\workflow.json")

# Edit workflow
manager.edit_workflow(["6", "inputs", "text"], "a cute anime girl")
manager.edit_workflow(["3", "inputs", "seed"], 123456789)

# Submit workflow
prompt_id = manager.submit_workflow()

# Waiting until completion
print(f"Prompt submitted with id: {prompt_id}. Waiting for completion...")
while not manager.check_queue(prompt_id):
    print("Workflow still running...")
    time.sleep(1)  # Poll every 1 second

print("Workflow finished!")

# Find output
output_url, filename = manager.find_output(prompt_id, with_filename=True)

# Download output
print(f"Output URL: {output_url}")
print(f"Output filename: {filename}")
manager.download_output(output_url, save_path=".", filename=filename)
print("Download complete.")