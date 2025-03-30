import comfyapi

# comfyapi.set_base_url("127.0.0.1:8188")
comfyapi.set_base_url("https://marion-tokyo-sporting-baths.trycloudflare.com/")

workflow = comfyapi.load_workflow("example\workflow.json")

workflow = comfyapi.edit_workflow(workflow, ["6", "inputs", "text"], "a cute anime girl")
workflow = comfyapi.edit_workflow(workflow, ["3", "inputs", "seed"], 675597785947)

uid = comfyapi.submit(workflow)

url = comfyapi.wait_for_finish(uid)

comfyapi.download_output(url, "example/")
