from comfyapi import ComfyAPIManager
import time

from pathlib import Path

here = Path(__file__).parent

manager = ComfyAPIManager()
manager.set_base_url("127.0.0.1:8188")

# NOTE: To enable image uploading via the Base64ImageLoader node,
# clone the helper nodes into your ComfyUI custom_nodes folder:
# git clone https://github.com/SamratBarai/ComfyAPI_helper <COMFYUI_CUSTOM_NODES_DIR>/ComfyAPI_helper
# Restart ComfyUI after adding the custom node.

# Load your workflow that contains the "Base64 Image Loader" node
manager.load_workflow(str(here / "workflow_i2i.json"))

# Update standard text/seed inputs
manager.edit_workflow(["6", "inputs", "text"], "A cute cat sitting on a sofa")

# Update the image input using the new function
# Node ID '10' is the Base64ImageLoader in workflw.json
# Example: enforce a 300 KB maximum size and 800px maximum dimension
manager.set_base64_image(node_id="10", image_path=str(here / "example.png"), max_size_bytes=300000, max_dimension=800)

# Submit and wait
prompt_id = manager.submit_workflow()
print(f"Workflow submitted: {prompt_id}")
manager.wait_for_finish(prompt_id)

# Get result and download
output_url, filename = manager.find_output(prompt_id, with_filename=True)
out_dir = here / "results"
out_dir.mkdir(parents=True, exist_ok=True)
manager.download_output(output_url, save_path=str(out_dir), filename=filename)
print("Download complete.")