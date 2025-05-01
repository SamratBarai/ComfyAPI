import comfyapi as com
import gradio as gr
import random
import sys

# Ensure BASE_URL includes scheme
if len(sys.argv) > 1:
    BASE_URL = sys.argv[1]
    if not BASE_URL.startswith("http://") and not BASE_URL.startswith("https://"):
        BASE_URL = "http://" + BASE_URL
else:
    BASE_URL = "http://127.0.0.1:8188"

# Use the new ComfyAPIManager system
manager = com.ComfyAPIManager()
manager.set_base_url(BASE_URL)

# Load workflow once at startup (if you want to reload every call, move this into main)
WORKFLOW_PATH = "./workflow.json"
manager.load_workflow(WORKFLOW_PATH)

def main(prompt, height, width, seed, random_seed, steps, model):
    try:
        # Always work on a fresh copy
        manager.load_workflow(WORKFLOW_PATH)
        manager.edit_workflow(["6", "inputs", "text"], prompt)
        manager.edit_workflow(["5", "inputs", "height"], height)
        manager.edit_workflow(["5", "inputs", "width"], width)
        if random_seed:
            seed = random.randint(0, 9999999)
        manager.edit_workflow(["3", "inputs", "seed"], seed)
        manager.edit_workflow(["3", "inputs", "steps"], steps)
        manager.edit_workflow(["10", "inputs", "ckpt_name"], model)

        prompt_id = manager.submit_workflow()
        # Wait for finish (blocking)
        result = manager.wait_for_finish(prompt_id)
        url, filename = manager.find_output(prompt_id, with_filename=True)
        if url is None:
            return None, "No output image found."
        return url, None
    except Exception as e:
        return None, f"Error: {str(e)}"

# --- BEAUTIFYING THE UI FOR GRADIO 5.x ---
CUSTOM_CSS = '''
.gradio-container {background: linear-gradient(135deg, #f8fafc 0%, #e0e7ef 100%);}
.gr-button {background: #6366f1 !important; color: #fff !important; border-radius: 8px !important; font-weight: 600;}
.gr-textbox, .gr-slider, .gr-dropdown {border-radius: 8px !important;}
.gr-image {border-radius: 16px !important; box-shadow: 0 4px 16px rgba(0,0,0,0.08);}
'''

with gr.Blocks(theme=gr.themes.Soft(), css=CUSTOM_CSS) as demo:
    gr.Markdown("""
        # <span style='color:#6366f1;'>ComfyAPI Workflow Runner</span>
        <span style='font-size:1.1em;color:#334155;'>
        Easily edit and submit workflows with a beautiful interface.
        </span>
        <hr style='margin-top:8px;margin-bottom:16px;border:0;border-top:1.5px solid #e0e7ef;'>
    """, elem_id="header")
    with gr.Row():
        with gr.Column():
            prompt_textbox = gr.Textbox(label="Prompt", placeholder="Describe what you want to generate...", elem_id="prompt")
            height_slider = gr.Slider(minimum=64, maximum=2048, value=512, label="Height", interactive=True)
            width_slider = gr.Slider(minimum=64, maximum=2048, value=512, label="Width", interactive=True)
            with gr.Row():
                seed = gr.Slider(minimum=0, maximum=999999, value=0, label="Seed", interactive=True)
                random_seed = gr.Checkbox(label="Randomize Seed", value=False)
            steps_slider = gr.Slider(minimum=1, maximum=150, value=20, label="Steps", interactive=True)
            model = gr.Dropdown(choices=["WAI-ANI-Illustrious-PONYXL-v.13.safetensors", "Realistic_vision.safetensors"], label="Model", interactive=True)
            submit_button = gr.Button("✨ Generate Image", elem_id="submit_btn")
        with gr.Column():
            output_image = gr.Image(label="Result", elem_id="output_img")
            error_box = gr.Textbox(label="Error", interactive=False, visible=False, elem_id="error_box")

    def handle_submit(*args):
        img_url, error = main(*args)
        if error:
            return img_url, gr.update(value=error, visible=True)
        return img_url, gr.update(value="", visible=False)

    submit_button.click(
        fn=handle_submit,
        inputs=[prompt_textbox, height_slider, width_slider, seed, random_seed, steps_slider, model],
        outputs=[output_image, error_box]
    )

demo.launch()
