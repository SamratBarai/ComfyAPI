import comfyapi as com
import gradio as gr
import random
import sys

if len(sys.argv) > 1:
    BASE_URL = sys.argv[1]
else:
    BASE_URL = "127.0.0.1:8188"

# Use the new ComfyAPIManager system
manager = com.ComfyAPIManager()
manager.set_base_url(BASE_URL)

# Load workflow once at startup (if you want to reload every call, move this into main)
WORKFLOW_PATH = "./workflow.json"
manager.load_workflow(WORKFLOW_PATH)

def main(prompt, height, width, seed, random_seed, steps, model):
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
    manager.wait_for_finish(prompt_id)
    url, filename = manager.find_output(prompt_id, with_filename=True)
    return url

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            prompt_textbox = gr.Textbox(label="prompt")
            height_slider = gr.Slider(minimum=64, maximum=2048, value=512, label="height")
            width_slider = gr.Slider(minimum=64, maximum=2048, value=512, label="width")
            with gr.Row():
                seed = gr.Slider(minimum=0, maximum=999999, value=0, label="seed")
                random_seed = gr.Checkbox(label="Randomize seed", value=False)
            
            steps_slider = gr.Slider(minimum=1, maximum=150, value=20, label="steps")
            model = gr.Dropdown(choices=["WAI-ANI-Illustrious-PONYXL-v.13.safetensors", "Realistic_vision.safetensors"], label="Model")
            submit_button = gr.Button("Submit")
        with gr.Column():
            output_image = gr.Image()

    submit_button.click(
        fn=main,
        inputs=[prompt_textbox, height_slider, width_slider, seed, random_seed, steps_slider, model],
        outputs=output_image
    )

demo.launch()
