"""Concurrent collection mutations must not silently undo each other.

The web app runs sync FastAPI handlers on a thread pool inside one uvicorn
process, so two requests can mutate the same collection at once. Each test
parks request A right after it has read the collection, lets request B run to
completion (or block), then releases A. A read-modify-write that does not hold
the store lock across the whole transaction writes A's stale copy over B.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import pytest

from crest_app.models import CollectionCreate, CollectionUpdate
from crest_app.services import WorkbenchStore

# Upper bound for how long A waits to see whether B can finish while A is
# mid-transaction. With the bug, B finishes immediately and A never waits this
# long; with the fix, B is blocked on the store lock, so A proceeds after this
# bound. It is a deadlock guard, not a timing assumption for correctness.
B_BLOCKED_GRACE_SECONDS = 0.5


def _interleave(
    store: WorkbenchStore,
    op_a: Callable[[], object],
    op_b: Callable[[], object],
) -> None:
    a_has_read = threading.Event()
    b_attempting = threading.Event()
    b_done = threading.Event()
    original_get = store.get_collection
    errors: list[BaseException] = []

    def get_collection_pausing_a(collection_id: str):
        collection = original_get(collection_id)
        if threading.current_thread().name == "request-a" and not a_has_read.is_set():
            a_has_read.set()
            assert b_attempting.wait(5), "request B never started"
            b_done.wait(B_BLOCKED_GRACE_SECONDS)
        return collection

    store.get_collection = get_collection_pausing_a  # type: ignore[method-assign]

    def run(op: Callable[[], object], done: threading.Event | None) -> None:
        try:
            op()
        except BaseException as exc:  # surfaced below, never swallowed
            errors.append(exc)
        finally:
            if done is not None:
                done.set()

    thread_a = threading.Thread(target=run, args=(op_a, None), name="request-a")
    thread_a.start()
    assert a_has_read.wait(5), "request A never read the collection"

    def op_b_marked() -> object:
        b_attempting.set()
        return op_b()

    thread_b = threading.Thread(target=run, args=(op_b_marked, b_done), name="request-b")
    thread_b.start()
    thread_a.join(10)
    thread_b.join(10)
    assert not thread_a.is_alive() and not thread_b.is_alive(), "requests deadlocked"
    if errors:
        raise errors[0]


@pytest.fixture
def store_and_collection(tmp_path: Path):
    store = WorkbenchStore(tmp_path)
    collection = store.create_collection(CollectionCreate(title="Original"))
    store.replace_collection_documents(collection.id, ["doc-1"])
    return store, collection.id


def test_title_update_and_document_replace_both_survive(store_and_collection) -> None:
    store, collection_id = store_and_collection
    _interleave(
        store,
        lambda: store.update_collection(collection_id, CollectionUpdate(title="Renamed")),
        lambda: store.replace_collection_documents(collection_id, ["doc-1", "doc-2"]),
    )
    final = store.get_collection(collection_id)
    assert final.title == "Renamed"
    assert final.document_ids == ["doc-1", "doc-2"]


def test_concurrent_document_adds_both_survive(store_and_collection) -> None:
    store, collection_id = store_and_collection
    _interleave(
        store,
        lambda: store.add_collection_documents(collection_id, ["doc-2"]),
        lambda: store.add_collection_documents(collection_id, ["doc-3"]),
    )
    assert set(store.get_collection(collection_id).document_ids) == {
        "doc-1",
        "doc-2",
        "doc-3",
    }


def test_update_racing_delete_does_not_resurrect_collection(store_and_collection) -> None:
    store, collection_id = store_and_collection

    def update_tolerating_deleted() -> None:
        # Once serialized, the update either wins (then delete removes it) or
        # finds the collection gone; either way it must not recreate it.
        try:
            store.update_collection(collection_id, CollectionUpdate(title="Renamed"))
        except KeyError:
            pass

    _interleave(store, update_tolerating_deleted, lambda: store.delete_collection(collection_id))
    with pytest.raises(KeyError):
        store.get_collection(collection_id)
