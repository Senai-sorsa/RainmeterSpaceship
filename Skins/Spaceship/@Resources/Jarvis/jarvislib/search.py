"""search: moved verbatim from jarvis.py (refactor). See JARVIS-Repair-Plan.txt, REFACTOR."""
import os
import re
import threading
import time
from .base import DATA, log, setting
from .notes import vault_dir


# ------------------------------------------------------------------ smart note search (ChromaDB)
# JarvisSmartSearch=1 (default when chromadb is installed): your vault is split into passages and indexed by meaning
# in a local ChromaDB database (Data\notes_index), so "what did I write about motor torque" finds notes that never use
# those exact words. The index updates itself in the background (only changed notes) every 10 minutes and before a
# search. If ChromaDB isn't installed or fails, the keyword search below is used instead - search always works.
_chroma = {"col": None, "root": None, "seen": {}, "last": 0.0, "failed": False}
_chroma_lock = threading.Lock()
_reindexing = threading.Lock()         # a full pass over the vault is running


def _chunks(text, size=900):
    paras, out, cur = re.split(r"\n\s*\n", text), [], ""
    for p in paras:
        p = p.strip()
        if not p:
            continue
        if len(cur) + len(p) > size and cur:
            out.append(cur)
            cur = ""
        cur = (cur + "\n\n" + p).strip()
        while len(cur) > size * 1.5:
            out.append(cur[:size])
            cur = cur[size:]
    if cur:
        out.append(cur)
    return out


def chroma_index(force=False):
    """Bring the index up to date with the vault (only new / changed / deleted notes). Returns the collection or None."""
    if setting("JarvisSmartSearch", "1") != "1" or _chroma["failed"]:
        return None
    root = vault_dir()
    if not root:
        return None
    try:
        with _chroma_lock:                                     # held only briefly, so a search never waits for a reindex
            if _chroma["col"] is None or _chroma["root"] != root:
                import chromadb
                client = chromadb.PersistentClient(path=os.path.join(DATA, "notes_index"))
                _chroma["col"] = client.get_or_create_collection("notes", metadata={"hnsw:space": "cosine"})
                _chroma["root"], _chroma["seen"] = root, {}
                for m in (_chroma["col"].get(include=["metadatas"]).get("metadatas") or []):
                    if m:
                        _chroma["seen"][m["path"]] = m.get("mtime", 0)
            if not force and time.time() - _chroma["last"] < 600:
                return _chroma["col"]
        if not _reindexing.acquire(blocking=False):            # one reindex at a time; meanwhile search what is there
            return _chroma["col"]
        try:
            col, seen, t0, changed = _chroma["col"], _chroma["seen"], time.time(), 0
            present = set()
            for dirpath, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for fn in files:
                    if not fn.lower().endswith(".md"):
                        continue
                    path = os.path.join(dirpath, fn)
                    present.add(path)
                    try:
                        mt = os.path.getmtime(path)
                    except OSError:
                        continue
                    if seen.get(path) == mt:
                        continue
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            parts = _chunks(f.read(300_000))
                    except OSError:
                        continue                               # deleted or locked mid-sync: the next pass gets it
                    with _chroma_lock:                         # per note: a search waits for one note at most
                        col.delete(where={"path": path})
                        if parts:
                            name = os.path.splitext(fn)[0]
                            col.upsert(ids=[f"{path}#{i}" for i in range(len(parts))],
                                       documents=[f"{name}\n{p}" for p in parts],
                                       metadatas=[{"path": path, "name": name, "mtime": mt} for _ in parts])
                    seen[path] = mt
                    changed += 1
            for gone in [p for p in seen if p not in present]:
                with _chroma_lock:
                    col.delete(where={"path": gone})
                del seen[gone]
                changed += 1
            _chroma["last"] = time.time()
            if changed:
                log(f"notes index: {changed} note(s) updated in {time.time() - t0:.1f}s")
            return col
        finally:
            _reindexing.release()
    except ImportError:
        _chroma["failed"] = True
        log("smart search: chromadb not installed - using keyword search")
    except Exception as e:
        _chroma["failed"] = True
        log(f"smart search failed ({e!r}) - using keyword search until restart")
    return None


def smart_search(query, limit=3):
    col = chroma_index()
    if col is None:
        return None
    try:
        with _chroma_lock:
            res = col.query(query_texts=[query], n_results=limit)
        docs, metas, dists = res["documents"][0], res["metadatas"][0], res.get("distances", [[1] * limit])[0]
        return [(1 - d, m["name"], re.sub(r"\s+", " ", doc)[:600]) for doc, m, d in zip(docs, metas, dists) if d < 0.8]
    except Exception as e:
        log(f"smart search query failed: {e!r}")
        return None
