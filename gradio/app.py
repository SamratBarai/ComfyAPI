import comfyapi as com
import gradio as gr
import sys

if len(sys.argv) > 1:
    BASE_URL = sys.argv[1]
else: BASE_URL = "127.0.0.1:8188"

com.set_base_url(BASE_URL)

def main(prompt, height, width, steps, model):
    workflow = com.load_workflow("./workflow.json")

    workflow = com.edit_workflow(workflow, ["6", "inputs", "text"], prompt)
    workflow = com.edit_workflow(workflow, ["5", "inputs", "height"], height)
    workflow = com.edit_workflow(workflow, ["5", "inputs", "width"], width)
    workflow = com.edit_workflow(workflow, ["3", "inputs", "steps"], steps)
    workflow = com.edit_workflow(workflow, ["10", "inputs", "ckpt_name"], model)

    uid = com.submit(workflow)
    url = com.wait_for_finish(uid)

    return url

with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            prompt_textbox = gr.Textbox(label="prompt")
            height_slider = gr.Slider(minimum=64, maximum=2048, value=512, label="height")
            width_slider = gr.Slider(minimum=64, maximum=2048, value=512, label="width")
            steps_slider = gr.Slider(minimum=1, maximum=150, value=20, label="steps")
            model = gr.Dropdown(choices=["WAI-ANI-Illustrious-PONYXL-v.13.safetensors", "Realistic_vision.safetensors"], label="Model")
            submit_button = gr.Button("Submit")
        with gr.Column():
            output_image = gr.Image()

    submit_button.click(
        fn=main,
        inputs=[prompt_textbox, height_slider, width_slider, steps_slider, model],
        outputs=output_image
    )

demo.launch(share=True, server_port=8000)
