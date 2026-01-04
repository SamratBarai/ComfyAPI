from comfyapi import ComfyAPIManager
import time

# Initialize manager
manager = ComfyAPIManager()

# Set Base Url (update as needed)
manager.set_base_url("http://127.0.0.1:8188")

from pathlib import Path
here = Path(__file__).parent

# Load workflow (relative path)
manager.load_workflow(str(here / "workflw.json"))

# Edit workflow
manager.edit_workflow(["6", "inputs", "text"], "a professional photo of a person in a studio")
manager.edit_workflow(["3", "inputs", "seed"], 123456789)

# Submit workflow
prompt_id = manager.submit_workflow()

# Wait for completion (use wait_for_finish which returns (filename, url))
print(f"Prompt submitted with id: {prompt_id}. Waiting for completion...")
filename, output_url = manager.wait_for_finish(prompt_id)
print(f"Workflow finished! Output: {filename} -> {output_url}")

# Download output
out_dir = here / "images"
out_dir.mkdir(parents=True, exist_ok=True)
manager.download_output(output_url, save_path=str(out_dir), filename=filename)
print("Download complete.")