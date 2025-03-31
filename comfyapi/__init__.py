import json
import copy
import os
import urllib

# Import core functions and exceptions from the client module
from .client import (
    set_base_url as _set_base_url,
    _queue_prompt,
    _wait_for_finish_single,
    _get_history,
    _find_output_in_history,
    _batch_submit_internal,
    _wait_and_get_all_outputs_internal,
    # download_output as _download_output, # Removed internal import
    _get_base_url,
    _generate_client_id, # Need this for fallback filename generation
    ComfyAPIError,
    ConnectionError,
    QueueError,
    HistoryError,
    ExecutionError,
    TimeoutError
)
import requests # Need requests here now
import urllib.parse # Need urllib here now

# --- Public API Functions ---

# Expose exceptions directly
__all__ = [
    "load_workflow",
    "edit_workflow",
    "set_base_url",
    "submit",
    "batch_submit",
    "wait_for_finish",
    "find_output_url",
    "wait_and_get_all_outputs",
    "download_output",
    "ComfyAPIError",
    "ConnectionError",
    "QueueError",
    "HistoryError",
    "ExecutionError",
    "TimeoutError",
]

def load_workflow(filepath):
    """Loads a workflow from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise ComfyAPIError(f"Workflow file not found: {filepath}")
    except json.JSONDecodeError:
        raise ComfyAPIError(f"Failed to decode JSON from workflow file: {filepath}")
    except Exception as e:
        raise ComfyAPIError(f"Error loading workflow file {filepath}: {e}")

def edit_workflow(workflow, path, value):
    """
    Edits a value within the workflow dictionary using a path list.
    Returns a *new* modified workflow dictionary.

    Args:
        workflow (dict): The workflow dictionary.
        path (list): A list of keys/indices representing the path to the value.
                     Example: ["6", "inputs", "text"]
        value: The new value to set.

    Returns:
        dict: A deep copy of the workflow with the value modified.

    Raises:
        ValueError: If the path is invalid for the workflow structure.
    """
    if not isinstance(path, list) or len(path) < 1:
        raise ValueError("Path must be a non-empty list.")

    # Create a deep copy to avoid modifying the original workflow dict
    wf_copy = copy.deepcopy(workflow)

    try:
        target = wf_copy
        for key in path[:-1]:
            # Handle potential string indices for list access if needed, though keys are usually strings
            if isinstance(target, list) and isinstance(key, str) and key.isdigit():
                 key = int(key)
            target = target[key]

        final_key = path[-1]
        if isinstance(target, list) and isinstance(final_key, str) and final_key.isdigit():
            final_key = int(final_key)

        target[final_key] = value
        return wf_copy
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError(f"Invalid path {path} for workflow structure: {e}")

def set_base_url(url):
    """
    Sets the base URL for the ComfyUI server. Must be called before other API interactions.

    Args:
        url (str): The full URL of the ComfyUI server (e.g., "http://127.0.0.1:8188").
    """
    _set_base_url(url)

def submit(workflow):
    """
    Submits a single workflow to the ComfyUI server.

    Args:
        workflow (dict): The workflow dictionary to submit.

    Returns:
        str: The prompt ID assigned by the server.

    Raises:
        ComfyAPIError: If the base URL is not set or if queueing fails.
    """
    return _queue_prompt(workflow)

def batch_submit(workflow, num_seeds=None, seeds=None, seed_node_path=["3", "inputs", "seed"]):
    """
    Submits multiple instances of a workflow, varying the seed for each instance.
    You must provide either a list of seeds to use (`seeds`) or the number
    of random seeds to generate (`num_seeds`).

    Args:
        workflow (dict): The base workflow dictionary.
        seed_node_path (list): The path within the workflow to the seed input node.
                               Example: ["3", "inputs", "seed"]
        seeds (list, optional): A list of specific seed values to use.
        num_seeds (int, optional): The number of random seeds to generate and use.

    Returns:
        list: A list of prompt IDs assigned by the server for each submitted job.

    Raises:
        ValueError: If neither or both `seeds` and `num_seeds` are provided,
                    if `seeds` list is empty, if `num_seeds` is not positive,
                    or if `seed_node_path` is invalid.
        ComfyAPIError: If the base URL is not set or if any queueing fails.
    """
    return _batch_submit_internal(workflow, seed_node_path, seeds=seeds, num_seeds=num_seeds)

def wait_for_finish(prompt_id, poll_interval=3, max_wait_time=600, status_callback=None):
    """
    Waits for a single submitted job (prompt_id) to finish execution.

    Args:
        prompt_id (str): The ID of the prompt to wait for.
        poll_interval (int): Seconds between polling checks.
        max_wait_time (int): Maximum seconds to wait before timing out.
        status_callback (callable, optional): A function to call with status updates.
                                              It receives (prompt_id, status_string).
                                              Statuses: "polling", "finished", "error", "timeout".

    Returns:
        tuple: A tuple containing (filename, output_url) if successful.

    Raises:
        TimeoutError: If the job doesn't finish within max_wait_time.
        ExecutionError: If the server reports an execution error for the job.
        ComfyAPIError: For other API or connection issues.
    """
    return _wait_for_finish_single(prompt_id, poll_interval, max_wait_time, status_callback)

def find_output_url(prompt_id):
    """
    Finds the output image URL for a completed job by checking its history.
    Note: This polls history; use after confirming completion with wait_for_finish
          or if checking a potentially already completed job.

    Args:
        prompt_id (str): The ID of the prompt.

    Returns:
        str or None: The URL of the first found output image, or None if not found or not complete.

    Raises:
        ComfyAPIError: For API or connection issues during history fetch.
    """
    history = _get_history(prompt_id)
    filename = _find_output_in_history(history)
    if filename:
        base_url = _get_base_url()
        # Ensure filename is URL-encoded
        encoded_filename = urllib.parse.quote(filename)
        return f"{base_url}/view?filename={encoded_filename}&type=output"
    return None

def wait_and_get_all_outputs(uids, status_callback=None):
    """
    Waits for multiple submitted jobs (UIDs) to finish concurrently and retrieves their output URLs.

    Args:
        uids (list): A list of prompt IDs to wait for.
        status_callback (callable, optional): A function called with status updates for each UID.
                                              Receives (prompt_id, status_string).
                                              Statuses: "started", "polling", "finished", "error", "timeout".

    Returns:
        tuple: A tuple containing:
               - results_list (list): A list of `(filename, output_url)` tuples for successfully completed jobs.
               - errors_list (list): A list of error objects/strings for jobs that failed or timed out.

    Raises:
        ComfyAPIError: For initial setup issues (like base URL not set). Errors during
                       individual job processing are collected in the errors dictionary.
    """
    return _wait_and_get_all_outputs_internal(uids, status_callback)


def download_output(output_url, save_path=".", filename=None):
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
