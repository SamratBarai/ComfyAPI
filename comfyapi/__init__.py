import json
import copy
import os
import urllib

# Import core functions and exceptions from the client module
from .client import (
    set_base_url as _set_base_url,
    _queue_prompt,
    _wait_for_finish_single,
    _batch_submit_internal,
    _wait_and_get_all_outputs_internal,
    _download_output,
    _generate_client_id, # Need this for fallback filename generation
    _find_output,
    ComfyAPIError,
    ConnectionError,
    QueueError,
    HistoryError,
    ExecutionError,
    TimeoutError,
    _get_history,
    _find_output_in_history
)
import requests # Need requests here now
import urllib.parse # Need urllib here now

# --- Public API Functions ---

# Expose exceptions directly
__all__ = [
    "ComfyAPIError",
    "ConnectionError",
    "QueueError",
    "HistoryError",
    "ExecutionError",
    "TimeoutError",
    "ComfyAPIManager"
]

class ComfyAPIManager:
    def __init__(self):
        self.workflow = None
        self.base_url = None
        # Track queued jobs: list of dicts {"prompt_id": str, "status": str}
        self.queue = []

    def set_base_url(self, url):
        self.base_url = url
        _set_base_url(url)

    def load_workflow(self, filepath):
        """Loads a workflow from a JSON file and stores it locally."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.workflow = json.load(f)
        except FileNotFoundError:
            raise ComfyAPIError(f"Workflow file not found: {filepath}")
        except json.JSONDecodeError:
            raise ComfyAPIError(f"Failed to decode JSON from workflow file: {filepath}")
        except Exception as e:
            raise ComfyAPIError(f"Error loading workflow file {filepath}: {e}")

    def edit_workflow(self, path, value):
        """
        Edits the stored workflow in place and updates self.workflow.
        """
        if self.workflow is None:
            raise ValueError("No workflow loaded.")
        wf_copy = copy.deepcopy(self.workflow)
        try:
            target = wf_copy
            for key in path[:-1]:
                if isinstance(target, list) and isinstance(key, str) and key.isdigit():
                    key = int(key)
                target = target[key]
            final_key = path[-1]
            if isinstance(target, list) and isinstance(final_key, str) and final_key.isdigit():
                final_key = int(final_key)
            target[final_key] = value
            self.workflow = wf_copy
        except (KeyError, IndexError, TypeError) as e:
            raise ValueError(f"Invalid path {path} for workflow structure: {e}")

    def submit_workflow(self):
        """
        Submits the stored workflow and tracks it in the manager queue.
        """
        if self.workflow is None:
            raise ValueError("No workflow loaded.")
        prompt_id = _queue_prompt(self.workflow)
        self.queue.append({"prompt_id": prompt_id, "status": "queued"})
        return prompt_id

    def batch_submit(self, num_seeds=None, seeds=None, seed_node_path=["3", "inputs", "seed"], random_seeds=False):
        """
        Submits multiple instances of the stored workflow, varying the seed for each instance.
        If random_seeds is True, generates random seeds for each workflow.
        Tracks all prompt_ids in the manager queue.
        """
        if self.workflow is None:
            raise ValueError("No workflow loaded.")
        if random_seeds:
            import random
            seeds = [random.randint(0, 2**32 - 1) for _ in range(num_seeds)]
        prompt_ids = _batch_submit_internal(self.workflow, seed_node_path, seeds=seeds, num_seeds=(None if seeds else num_seeds))
        for pid in prompt_ids:
            self.queue.append({"prompt_id": pid, "status": "queued"})
        return prompt_ids

    def wait_for_finish(self, prompt_id, poll_interval=3, max_wait_time=600, status_callback=None):
        """
        Waits for a single submitted job (prompt_id) to finish execution.
        Updates the status in the manager queue.
        """
        result = _wait_for_finish_single(prompt_id, poll_interval, max_wait_time, status_callback)
        # Update status to finished
        for job in self.queue:
            if job["prompt_id"] == prompt_id:
                job["status"] = "finished"
        return result

    def check_queue(self, prompt_id):
        """
        Checks the status of a queued prompt_id (non-blocking, single check).
        Returns True if finished, False otherwise. Updates the queue status.
        """
        # Find job in queue
        for job in self.queue:
            if job["prompt_id"] == prompt_id:
                # Check if already finished
                if job["status"] == "finished":
                    return True
                # Check current status (non-blocking)
                history = None
                try:
                    history = _get_history(prompt_id)
                except Exception:
                    pass
                filename = None
                if history:
                    filename = _find_output_in_history(history)
                if filename:
                    job["status"] = "finished"
                    return True
                else:
                    job["status"] = "queued"
                    return False
        return False  # Not found

    def find_output(self, prompt_id, with_filename=False):
        """
        Returns the output URL and, if requested, the filename for a completed job.
        If with_filename=True, returns (url, filename). Otherwise, returns url only.
        """
        url, filename = _find_output(prompt_id)
        if with_filename:
            return url, filename
        return url

    def wait_and_get_all_outputs(self, uids, status_callback=None):
        """
        Waits for multiple submitted jobs (UIDs) to finish concurrently and retrieves their output URLs.
        """
        return _wait_and_get_all_outputs_internal(uids, status_callback)

    def download_output(self, output_url, save_path=".", filename=None):
        return _download_output(output_url, save_path=save_path, filename=filename)
