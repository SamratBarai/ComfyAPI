import json
import random
import websocket
import urllib.parse
import requests
import time
import threading
import copy
import os
from queue import Queue

# --- Module State ---
_base_url = None
_websocket_url = None
_client_id = None

# --- Exceptions ---
class ComfyAPIError(Exception):
    """Base exception for comfyapi errors."""
    pass

class ConnectionError(ComfyAPIError):
    """Error connecting to the ComfyUI server."""
    pass

class QueueError(ComfyAPIError):
    """Error queueing the prompt."""
    pass

class HistoryError(ComfyAPIError):
    """Error fetching or interpreting history."""
    pass

class ExecutionError(ComfyAPIError):
    """Error during prompt execution on the server."""
    pass

class TimeoutError(ComfyAPIError):
    """Operation timed out."""
    pass

# --- Internal Helper Functions ---

def _extract_urls(url):
    """Extracts base HTTP/HTTPS and WS/WSS URLs."""
    if not url:
        raise ValueError("Server URL cannot be empty.")
    parsed_url = urllib.parse.urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError(f"Invalid server URL format: {url}")
    base = f"{parsed_url.scheme}://{parsed_url.netloc}"
    ws_scheme = "wss" if parsed_url.scheme == "https" else "ws"
    ws_url = f"{ws_scheme}://{parsed_url.netloc}/ws"
    return base, ws_url

def _generate_client_id():
    """Generates a unique client ID."""
    return str(random.randint(1000000000, 9999999999)) # Increased range

def _find_output(prompt_id):
    """
    Finds the output image URL and filename for a completed job by checking its history.
    Returns (url, filename) or (None, None) if not found.
    """
    history = _get_history(prompt_id)
    filename = _find_output_in_history(history)
    if filename:
        base_url = _get_base_url()
        encoded_filename = urllib.parse.quote(filename)
        url = f"{base_url}/view?filename={encoded_filename}&type=output"
        return url, filename
    return None, None

def _find_output_url(prompt_id):
    url, _ = _find_output(prompt_id)
    return url

def _find_output_in_history(prompt_history):
    """Parses history to find output images/files."""
    # print(f"[_find_output_in_history] Processing history: {prompt_history}") # DEBUG REMOVED
    if not prompt_history or 'outputs' not in prompt_history:
        # print("[_find_output_in_history] History empty or missing 'outputs' key.") # DEBUG REMOVED
        return None # Not finished or no outputs

    outputs = prompt_history['outputs']
    # Iterate through nodes to find the first image output
    # Assumes the desired output is an image; might need adjustment for other types
    for node_id, node_output in outputs.items():
        # print(f"[_find_output_in_history] Checking node {node_id}: {node_output}") # DEBUG REMOVED
        if 'images' in node_output:
            # print(f"[_find_output_in_history] Found 'images' in node {node_id}: {node_output['images']}") # DEBUG REMOVED
            for image_data in node_output['images']:
                # print(f"[_find_output_in_history] Checking image data: {image_data}") # DEBUG REMOVED
                # Check for standard output fields
                if image_data.get('type') == 'output' and 'filename' in image_data:
                    # print(f"[_find_output_in_history] Found output filename: {image_data['filename']}") # DEBUG REMOVED
                    return image_data['filename'] # Returns filename if found
    # print("[_find_output_in_history] No suitable output image found in history.") # DEBUG REMOVED
    return None # No image output found

# --- State Management ---

def set_base_url(url):
    """Sets the base URL for the ComfyUI server and generates a client ID."""
    global _base_url, _websocket_url, _client_id
    try:
        _base_url, _websocket_url = _extract_urls(url)
        _client_id = _generate_client_id()
        print(f"ComfyAPI: Base URL set to {_base_url}, WebSocket URL to {_websocket_url}, Client ID: {_client_id}")
    except ValueError as e:
        raise ConnectionError(f"Invalid server URL: {e}")

def _get_base_url():
    if not _base_url:
        raise ComfyAPIError("Base URL not set. Call set_base_url() first.")
    return _base_url

def _get_websocket_url():
    if not _websocket_url:
        raise ComfyAPIError("WebSocket URL not set. Call set_base_url() first.")
    return _websocket_url

def _get_client_id():
    if not _client_id:
        raise ComfyAPIError("Client ID not generated. Call set_base_url() first.")
    return _client_id

# --- Core API Interaction ---

def _open_websocket_connection():
    """Opens a WebSocket connection."""
    ws_url = _get_websocket_url()
    ws = websocket.WebSocket()
    try:
        # Increased timeout for potentially slow connections
        ws.connect(ws_url, timeout=90)
        print(f"WebSocket connected to {ws_url}")
        return ws
    except (websocket.WebSocketException, ConnectionRefusedError, TimeoutError, OSError) as e:
        raise ConnectionError(f"Failed to connect WebSocket to {ws_url}: {e}")

def _queue_prompt(prompt):
    """Queues a prompt using the configured base URL and client ID."""
    base_url = _get_base_url()
    client_id = _get_client_id()
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    url = f"{base_url}/prompt" # Changed from /api/prompt based on common ComfyUI setups
    print(f"Queueing prompt to {url} with client ID {client_id}")

    try:
        response = requests.post(url, data=data, headers={'Content-Type': 'application/json'}, timeout=60)
        response.raise_for_status()
        result = response.json()
        if 'prompt_id' not in result:
             raise QueueError(f"Failed to queue prompt: 'prompt_id' not in response: {result}")
        if 'error' in result:
             # Handle API-level errors if present
             error_details = result.get('node_errors', result['error'])
             raise QueueError(f"API error queueing prompt: {error_details}")
        print(f"Prompt queued successfully. Prompt ID: {result['prompt_id']}")
        return result['prompt_id']
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Timeout queueing prompt at {url}")
    except requests.exceptions.RequestException as e:
        raise QueueError(f"HTTP error queueing prompt at {url}: {e}")
    except json.JSONDecodeError:
        raise QueueError(f"Failed to decode JSON response from {url}")

def _get_history(prompt_id):
    """Fetches execution history for a given prompt_id."""
    base_url = _get_base_url()
    url = f"{base_url}/history/{prompt_id}"
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        history = response.json()
        # The history is a dictionary where the key is the prompt_id
        # print(f"[_get_history] Raw history response for {prompt_id}: {history}") # DEBUG REMOVED
        prompt_data = history.get(str(prompt_id))
        # print(f"[_get_history] Extracted history data for {prompt_id}: {prompt_data}") # DEBUG REMOVED
        return prompt_data
    except requests.exceptions.Timeout:
        print(f"Timeout fetching history for {prompt_id} from {url}")
        return None # Indicate timeout, polling might continue
    except requests.exceptions.RequestException as e:
        # Don't raise immediately, allow polling to retry
        print(f"Error fetching history for {prompt_id} from {url}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Failed to decode JSON history response from {url}")
        return None # Allow polling to retry

def _wait_for_finish_single(prompt_id, poll_interval=3, max_wait_time=600, status_callback=None):
    """
    Waits for a single prompt to finish by polling history.
    Returns a tuple containing (filename, output_url) upon success.
    """
    base_url = _get_base_url()
    start_time = time.time()
    last_status_update = 0

    while time.time() - start_time < max_wait_time:
        if status_callback and time.time() - last_status_update > 5: # Update status every 5s
             status_callback(prompt_id, "polling")
             last_status_update = time.time()

        print(f"Polling history for prompt_id: {prompt_id}...")
        prompt_history = _get_history(prompt_id)

        if prompt_history:
            filename = _find_output_in_history(prompt_history)
            if filename:
                print(f"Execution finished for {prompt_id}. Output filename: {filename}")
                # Construct the URL here
                output_url, _ = _find_output(prompt_id)
                print(f"Constructed output URL: {output_url}")
                if status_callback: status_callback(prompt_id, "finished")
                return filename, output_url # Success! Return filename and URL tuple

            # Check for errors in history (less common than WebSocket errors)
            # Note: ComfyUI history API might not always populate error details here reliably.
            # WebSocket monitoring (if implemented) is often better for catching errors early.
            if prompt_history.get('status', {}).get('status_str') == 'error':
                 # Attempt to get more details if available
                 error_info = prompt_history.get('status', {}).get('message', 'Unknown error from history status')
                 exception_info = prompt_history.get('status', {}).get('exception_message', '')
                 if exception_info: error_info += f" ({exception_info})"
                 print(f"Execution error found in history for {prompt_id}: {error_info}")
                 if status_callback: status_callback(prompt_id, "error")
                 # Raise an exception to signal failure
                 raise ExecutionError(f"Execution failed for prompt {prompt_id}: {error_info}")

            print(f"History found for {prompt_id}, but execution not complete yet.")
        else:
            print(f"History not yet available for {prompt_id}. Continuing poll.")

        time.sleep(poll_interval)

    if status_callback: status_callback(prompt_id, "timeout")
    raise TimeoutError(f"Polling timed out after {max_wait_time} seconds for prompt_id: {prompt_id}")


# --- Batch Processing ---

# Define a reasonable range for random seeds
_MIN_SEED = 0
_MAX_SEED = 2**32 - 1 # Max value for a 32-bit unsigned integer

def _generate_random_seeds(num_seeds):
    """Generates a list of random seeds."""
    if not isinstance(num_seeds, int) or num_seeds <= 0:
        raise ValueError("num_seeds must be a positive integer.")
    return [random.randint(_MIN_SEED, _MAX_SEED) for _ in range(num_seeds)]

def _batch_submit_internal(workflow, seed_node_path, seeds=None, num_seeds=None):
    """
    Internal function to submit multiple prompts with varying seeds.
    Accepts either an explicit list of seeds or a number of seeds to generate.
    """
    if seeds is not None and num_seeds is not None:
        raise ValueError("Provide either 'seeds' list or 'num_seeds', not both.")

    if seeds is not None:
        if not isinstance(seeds, list) or not seeds:
            raise ValueError("If provided, 'seeds' must be a non-empty list.")
        seed_list = seeds
    elif num_seeds is not None:
        seed_list = _generate_random_seeds(num_seeds)
        print(f"Generated {num_seeds} random seeds: {seed_list}")
    else:
        raise ValueError("Must provide either 'seeds' list or 'num_seeds'.")

    if not isinstance(seed_node_path, list) or len(seed_node_path) < 2:
         # Example: ["3", "inputs", "seed"]
        raise ValueError("seed_node_path must be a list specifying the path to the seed input.")

    uids = []
    for seed in seed_list:
        # Create a deep copy to avoid modifying the original workflow
        wf_copy = copy.deepcopy(workflow)

        # Navigate the path and set the seed
        try:
            target = wf_copy
            for key in seed_node_path[:-1]:
                target = target[key]
            target[seed_node_path[-1]] = seed
        except (KeyError, TypeError) as e:
            raise ValueError(f"Invalid seed_node_path {seed_node_path} for workflow structure: {e}")

        # Queue the modified workflow
        try:
            uid = _queue_prompt(wf_copy)
            uids.append(uid)
            print(f"Queued prompt with seed {seed}, UID: {uid}")
            time.sleep(0.1) # Small delay between submissions
        except ComfyAPIError as e:
            print(f"Failed to queue prompt for seed {seed}: {e}. Stopping batch.")
            # Optionally: Decide whether to continue or stop the whole batch on error
            raise QueueError(f"Failed during batch submission for seed {seed}: {e}")
    return uids

def _wait_and_get_all_outputs_internal(uids, status_callback=None):
    """
    Waits for multiple UIDs and fetches their outputs concurrently.
    Returns results as a list of (filename, url) tuples and errors as a list of error objects/strings.
    """
    results_list = []
    errors_list = [] # Changed from dict to list for errors
    threads = []
    result_queue = Queue() # Thread-safe queue for results/errors

    def worker(uid):
        try:
            if status_callback: status_callback(uid, "started")
            # _wait_for_finish_single now returns (filename, url)
            filename, output_url = _wait_for_finish_single(uid, status_callback=status_callback)
            result_queue.put({'uid': uid, 'filename': filename, 'url': output_url, 'status': 'success'})
        except Exception as e:
            print(f"Error processing UID {uid}: {e}")
            result_queue.put({'uid': uid, 'error': e, 'status': 'error'})

    for uid in uids:
        thread = threading.Thread(target=worker, args=(uid,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Collect results from the queue
    while not result_queue.empty():
        item = result_queue.get()
        if item['status'] == 'success':
            # Append (filename, url) tuple to the list
            results_list.append((item['filename'], item['url']))
        else:
            # Append the error object/string to the errors list
            errors_list.append(item['error'])

    if errors_list:
        # Log the errors that occurred
        error_summary = [str(err) for err in errors_list]
        print(f"Errors occurred during batch processing: {error_summary}")
        # Returning both successful results and the list of errors

    return results_list, errors_list # Return list for results and list for errors


# --- Public Function Wrappers (To be called from __init__.py) ---
# These might call the internal functions directly or add extra logic

def get_output_url(prompt_id):
     """Gets the output URL for a completed prompt ID."""
     # This might involve checking history again if the URL wasn't stored
     # For simplicity now, assume wait_for_finish returns the filename
     try:
         filename = _wait_for_finish_single(prompt_id) # Re-poll if needed, or retrieve stored result
         url, _ = _find_output(prompt_id)
         return url
     except ComfyAPIError as e:
         raise HistoryError(f"Could not get output URL for {prompt_id}: {e}")

def _download_output(output_url, save_path=".", filename=None):
    """
    Downloads the content from a ComfyUI output URL and saves it to a file.

    Args:
        output_url (str): The full URL to the output file (e.g., from find_output_url or wait_for_finish).
        save_path (str): The directory where the file should be saved. Defaults to current dir.
        filename (str, optional): The desired filename. If None, it attempts to extract
                                  from the URL or generates a unique name.

    Returns:
        str: The full path to the saved file.

    Raises:
        TimeoutError: If the download times out.
        ComfyAPIError: For HTTP errors or file system errors.
        ValueError: If output_url is invalid.
    """
    if not output_url:
        raise ValueError("output_url cannot be None or empty.")

    full_path = None # Initialize full_path to ensure it's defined in case of early error
    try:
        # Only create the directory if a specific path (not "" or ".") is provided
        if save_path and save_path != ".":
            os.makedirs(save_path, exist_ok=True)

        # Determine the target filename (user-provided or extracted)
        target_filename = None
        if filename:
            target_filename = filename # Use user-provided name first
        else:
            # Attempt to extract filename from URL query parameters
            try:
                parsed_url = urllib.parse.urlparse(output_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                extracted_filenames = query_params.get('filename', [])
                if extracted_filenames:
                    target_filename = extracted_filenames[0] # Get raw filename first
            except Exception:
                pass # Ignore parsing errors, will use fallback

        # If no filename extracted or provided, generate a fallback
        if not target_filename:
            target_filename = f"output_{_generate_client_id()}.unknown"

        # ***Crucially, sanitize the filename AFTER determining it***
        # This ensures only the final component is used as the filename.
        final_basename = os.path.basename(target_filename)

        # Construct the full path: use only the basename if save_path is "" or "."
        if not save_path or save_path == ".":
            full_path = final_basename
        else:
            full_path = os.path.join(save_path, final_basename)
        print(f"Saving to final path: {full_path}")

        # Download the content
        print(f"Downloading from {output_url} to {full_path}...")
        response = requests.get(output_url, timeout=120) # Longer timeout for download
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        # Save the file
        with open(full_path, 'wb') as f:
            f.write(response.content)
        print(f"Output saved to: {full_path}")
        return full_path

    except requests.exceptions.Timeout:
        raise TimeoutError(f"Timeout downloading output from {output_url}")
    except requests.exceptions.MissingSchema:
         raise ValueError(f"Invalid URL format (Missing Schema): {output_url}")
    except requests.exceptions.RequestException as e:
        raise ComfyAPIError(f"HTTP error downloading output from {output_url}: {e}")
    except IOError as e:
        # Ensure full_path is sensible before including in error message
        path_str = full_path if full_path else save_path
        raise ComfyAPIError(f"File system error saving output to {path_str}: {e}")
    except Exception as e: # Catch any other unexpected errors
        raise ComfyAPIError(f"An unexpected error occurred during download: {e}")
