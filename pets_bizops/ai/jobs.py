"""Tiny background-job runner so long LLM calls survive page navigation.

Streamlit stops a page's script run when you switch pages, which would cancel
a synchronous in-flight API call. Running the call in a background thread
(tracked in a process-global dict, NOT tied to the script run) lets it keep
going; the page polls by job key and picks up the result when it returns.

The worker function must be pure-Python and must NOT touch streamlit (no st.*)
-- it runs off the script-runner thread. client.run_tool_loop fits: it only
calls the Anthropic API and our data tools.
"""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable

_executor = ThreadPoolExecutor(max_workers=4)
_futures: dict[str, Future] = {}


def submit(job_key: str, fn: Callable[..., Any], *args, **kwargs) -> None:
    """Start the job if one isn't already tracked for this key (idempotent --
    safe to call on the rerun that follows the button click)."""
    if job_key in _futures:
        return
    _futures[job_key] = _executor.submit(fn, *args, **kwargs)


def poll(job_key: str) -> tuple[str, Any]:
    """Return one of:
    ("idle", None)      -- no job tracked
    ("running", None)   -- still in flight
    ("done", result)    -- finished; result is the worker's return value
    ("error", exception)
    """
    fut = _futures.get(job_key)
    if fut is None:
        return ("idle", None)
    if not fut.done():
        return ("running", None)
    try:
        return ("done", fut.result())
    except Exception as e:  # surfaced to the page, then cleared
        return ("error", e)


def clear(job_key: str) -> None:
    _futures.pop(job_key, None)


def is_running(job_key: str) -> bool:
    fut = _futures.get(job_key)
    return fut is not None and not fut.done()
