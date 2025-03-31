import comfyapi

# comfyapi.set_base_url("127.0.0.1:8188")
comfyapi.set_base_url("https://malawi-operations-accessibility-innocent.trycloudflare.com/")

workflow = comfyapi.load_workflow("E:\projects\softwares\ComfyAPI\example\workflow.json")

workflow = comfyapi.edit_workflow(workflow, ["6", "inputs", "text"], "a cute anime girl")
workflow = comfyapi.edit_workflow(workflow, ["3", "inputs", "seed"], 675597785947)

uid = comfyapi.submit(workflow)

filename, url = comfyapi.wait_for_finish(uid)

comfyapi.download_output(url, "example/", filename)
