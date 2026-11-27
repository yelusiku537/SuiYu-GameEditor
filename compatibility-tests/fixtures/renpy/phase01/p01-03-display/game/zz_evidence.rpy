## Phase 01 evidence harness.
##
## This file is the single source of truth for how phase01 fixtures record
## observable behaviour. Every fixture under
## compatibility-tests/fixtures/renpy/phase01/<fixture>/game/ carries a
## byte-identical copy of this file so that a bare
##
##     renpy.exe <fixture> test <testcase> --savedir <dir>
##
## produces evidence without the check script.
##
## Contract (keep this comment verbatim in every copy):
##  * Evidence is written as JSON Lines, one object per line, keys sorted.
##  * `SUIYU_EVIDENCE` selects the output path; default is
##    <basedir>/evidence/actual.jsonl.
##  * Statement and label callbacks only record nodes whose source file lives
##    under game/ and is not this harness file, so Ren'Py's own common/ labels
##    never pollute the trace.
##  * `import renpy` is deliberately done inside functions. Importing it at
##    module scope of an `init python:` block shadows Ren'Py's lazy module
##    proxy and breaks later `renpy.music` access.
##  * Recording is armed per testcase via `$ arm()` and stopped via
##    `$ disarm()`, so setup/teardown noise is excluded.

init python:
    import json
    import os

    _ev_state = {"armed": False, "file": None}

    def _ev_resolve_path():
        path = os.environ.get("SUIYU_EVIDENCE")
        if not path:
            path = os.path.join(config.basedir, "evidence", "actual.jsonl")
        directory = os.path.dirname(path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        return path

    def _ev_ensure_open():
        if _ev_state["file"] is None:
            _ev_state["file"] = open(_ev_resolve_path(), "w", encoding="utf-8")
        return _ev_state["file"]

    def _ev_write(record):
        if not _ev_state["armed"]:
            return
        handle = _ev_ensure_open()
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, default=str) + "\n")
        handle.flush()

    def arm():
        """Begin recording the next statements. Truncates any prior content."""
        handle = _ev_ensure_open()
        handle.seek(0)
        handle.truncate()
        _ev_state["armed"] = True

    def disarm():
        """Stop recording. Later statements are ignored."""
        _ev_state["armed"] = False

    def finish():
        """Emit a completion marker and stop recording.

        Place this as the last statement of a traced flow (immediately before
        the terminal `return`). Ren'Py re-enters `label start` after the script
        returns to the main menu; disarming here keeps the trace to exactly one
        logical pass and makes the flow boundary explicit.
        """
        _ev_write({"kind": "flow_complete"})
        _ev_state["armed"] = False

    def emit(kind, **fields):
        """Record a custom observation under an arbitrary kind."""
        record = {"kind": kind}
        record.update(fields)
        _ev_write(record)

    def shot(name):
        """Record screenshot metadata after a `screenshot` node succeeded.

        Call this with a `$ shot("<name>")` line placed immediately after the
        matching `screenshot "<name>"` statement. The PNG itself stays under
        `_test.screenshot_directory`; only name/size/sha256 are recorded so the
        repository carries no binary images.
        """
        import hashlib

        directory = os.path.join(config.basedir, _test.screenshot_directory)
        filename = name if name.lower().endswith(".png") else name + ".png"
        path = os.path.join(directory, filename)
        if not os.path.isfile(path):
            _ev_write({"kind": "screenshot", "name": name, "present": False})
            return
        with open(path, "rb") as handle:
            data = handle.read()
        _ev_write(
            {
                "kind": "screenshot",
                "name": name,
                "present": True,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )

    def _ev_on_statement(name):
        if not _ev_state["armed"]:
            return
        import renpy  # function-local to avoid shadowing the lazy proxy

        context = renpy.game.context()
        node = None
        if context.current is not None:
            try:
                node = renpy.game.script.lookup(context.current)
            except Exception:
                node = None
        filename = (getattr(node, "filename", "") or "").replace("\\", "/")
        basedir = (config.basedir or "").replace("\\", "/").rstrip("/")
        if basedir and filename.startswith(basedir + "/"):
            filename = filename[len(basedir) + 1:]
        if filename.endswith("zz_evidence.rpy"):
            return
        if not filename.startswith("game/"):
            return
        node_type = type(node).__name__ if node is not None else "None"
        record = {
            "kind": "stmt",
            "node": node_type,
            "file": filename,
            "line": getattr(node, "linenumber", None),
            "who": getattr(node, "who", None),
            "what": getattr(node, "what", None),
            "ret": len(context.return_stack),
        }
        if node_type == "Label":
            record["label"] = getattr(node, "name", None)
        _ev_write(record)

    def _ev_on_label(label, abnormal):
        if not _ev_state["armed"] or label.startswith("_"):
            return
        _ev_write({"kind": "label", "label": label, "abnormal": abnormal})

    config.statement_callbacks.append(_ev_on_statement)
    config.label_callback = _ev_on_label