"""Streamlit-side glue for ai/jobs.py background calls.

The page submits work under a job key, then calls poll_result() on every
rerun. While the job runs this shows a 'safe to navigate' banner and triggers
a gentle auto-poll; when it finishes it returns the worker's result once (the
page parses/stores it). Navigating away simply stops the poll loop -- the
background thread keeps running and the result is waiting when you return.
"""

from __future__ import annotations

import time
from typing import Any

import streamlit as st

from pets_bizops.ai import jobs

_RUNNING_MSG = "⏳ Running in the background — you can switch tabs and come back; this call won't be cancelled."


def poll_result(job_key: str, running_msg: str = _RUNNING_MSG, poll_secs: float = 1.5) -> Any:
    """Returns the finished result exactly once (then the page should store it),
    or None while idle/running/errored. Handles the running banner, the error
    message, and the auto-poll rerun internally.
    """
    status, payload = jobs.poll(job_key)
    if status == "running":
        st.info(running_msg)
        time.sleep(poll_secs)
        st.rerun()
    elif status == "error":
        st.error(f"The model call failed: {payload}")
        jobs.clear(job_key)
    elif status == "done":
        jobs.clear(job_key)
        return payload
    return None
