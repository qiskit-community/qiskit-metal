# MetalGUI crash defenses — read before touching GUI startup or teardown

Issue [#1048](https://github.com/qiskit-community/qiskit-metal/issues/1048) and
its descendants took five releases, several PRs, and a lot of reporter testing
on hardware none of the maintainers own. The defenses that came out of it look
like scattered defensive noise if you meet them cold, and several of them look
removable. They are not.

**Read this file before changing anything in `_gui/` startup, teardown,
stylesheet handling, or persisted window state.** Then read the source
comments, which carry the per-line detail.

---

## The failure modes

Four distinct bugs wore the same shirt ("MetalGUI segfaults"). Telling them
apart is most of the work.

| # | Failure | Status |
|---|---------|--------|
| 1 | **At-exit teardown segfault.** `Py_FinalizeEx` destroys `QApplication` while the window is alive; `~QWidget` dispatches an event through a half-deleted `QMenuBar::eventFilter` into a null vtable. | Fixed, v0.7.4 (PR #1104) |
| 2 | **On-screen init crash at `show()`.** Root cause was **persisted-state corruption**, not the GPU. Stale `QSettings` geometry replayed into `show()`. On Windows: `0xC0000409 STATUS_STACK_BUFFER_OVERRUN` / `FAST_FAIL_FATAL_APP_EXIT` inside `ucrtbase.dll`. | Fixed, v0.7.5–v0.7.6 (PRs #1122, #1128, #1129) |
| 3 | **Cross-kernel restore crash.** Kernel A saves a layout, kernel B restores it under a changed display config. `restoreState()` does *not* raise, so a try/except never fires. | Fixed, v0.7.6 (PR #1128) |
| 4 | **Mid-session GC teardown segfault.** Same null-vtable mechanism as (1) but triggered by ordinary garbage collection, which `atexit` never covers. | **Open.** Nondeterministic — a 32-variant sweep crashed 16/32 once, then ran clean 10× at the same commit. Consistent with heap corruption. |

The GPU theory for (2) was **explicitly falsified**: the reporter got 0/5 with
`QT_OPENGL=software` after normal usage, then a clean pass after deleting the
registry key. Don't re-derive it.

---

## The defenses, and what each guards

### Persisted-state invalidation — `restore_window_settings`

Checks, **in this order**, each clearing settings and returning:

0. Startup **journal** file left behind (see next section) — handled in
   `MetalGUI.__init__` before Qt is touched, not in this method
1. `QISKIT_METAL_RESET_UI_SETTINGS=1` — user escape hatch
2. `metal_version` newer than saved — cross-version state
3. `qt_version` mismatch — Qt has no version tag on its own state blob
4. `display_fingerprint` mismatch — monitor hot-swap, DPI change, undock
5. legacy `restore_in_progress` cookie found set — written by pre-journal
   versions; still honoured once on upgrade

Then — **only if `QISKIT_METAL_RESTORE_LAYOUT=1`** — it runs
`restoreGeometry`/`restoreState`. Layout restore became opt-in in the
fourth iteration of this defense: replaying a stale geometry/state blob
into a changed display environment is the root trigger of the on-screen
`show()` crash class (failure mode 2), and no invalidation heuristic can
enumerate every way a display environment differs. Default startup uses
the default layout and cannot be poisoned by persisted geometry at all.
The stylesheet (theme) is still restored either way. Any exception during
the guarded restore clears settings.

`_display_fingerprint()` is `name:x,y,w,h@dpr` per screen. It returns `""` on
error, and an empty value on either side short-circuits to a plain restore.

The `metal_version` check compares **parsed versions**, not strings. It was a
string compare until 2026-08-07 — correct only while every component stays
single-digit, since `'0.10.0' > '0.9.0'` is `False`. From v0.10.0 the guard
would have stopped firing with no error and no symptom: a defense quietly
switched off, and pre-0.10 layouts restored into a newer GUI. Any doubt now
resolves to "newer", because discarding state that might have been fine is the
cheap failure and restoring state that is not is the expensive one.

This guard doubles as the mechanism that gives users **new layout defaults on
upgrade**. Changing a dock's default visibility needs no migration code: the
saved layout is discarded on the version bump anyway. Worth knowing before
writing one.

### The startup journal — the ordering constraint that matters most

A plain flag file (`~/.quantum-metal/gui_startup.journal`,
`_gui/startup_journal.py`), written **and fsync'd as the first Python
instruction of `MetalGUI.__init__`**, removed only by
`mark_startup_complete()` after `main_window.show()` returns. A journal
found at startup means the previous launch died somewhere inside init:
persisted UI state is cleared before Qt is touched and the launch
proceeds with defaults.

It replaced the `restore_in_progress` QSettings cookie after CI hit both
of the cookie's structural holes on PR #1180:

- **Opened too late.** The cookie was set inside
  `restore_window_settings()`; a native crash *before* that point (QPA
  platform-plugin init, early widget construction) left no cookie, so the
  next launch replayed the same crash. CI's exact failure signature:
  "kernel C crashed during restore but did not leave the crash cookie
  set." The journal opens before any Qt call, so no crash inside init can
  escape it.
- **Not crash-durable.** `QSettings.sync()` is not a synchronous disk
  barrier everywhere — macOS routes writes through the `cfprefsd` daemon,
  which flushes asynchronously, so a native crash right after `sync()`
  could lose the write meant to record it. The journal is `flush()` +
  `os.fsync()`, and "the file exists" is the entire protocol.

The cookie's hard-won ordering lesson carries over unchanged: the
protected window must stay open **across `show()`** (PR #1129, `a04ab68`
— the crash site is first paint, not `restoreState()`).
**Never narrow the journal window.**

### Windows software OpenGL

`src/qiskit_metal/__init__.py` sets `QT_OPENGL=software` on `os.name == "nt"`
**before any PySide6 import**. Opt out with `QISKIT_METAL_QT_HARDWARE_GL=1`.

It must be the environment variable, not `Qt.AA_UseSoftwareOpenGL`: the
attribute is only a *hint*, read at `QGuiApplication` construction, and was
observed being silently ignored on the affected driver.

### Teardown

`_teardown_qt_widgets` runs via `atexit`, using `deleteLater()` — never
`close()`, which triggers the "save unsaved changes?" modal and blocks forever
headless. Order matters, and each step exists for a reason:

1. **Stop every `QTimer` under every top-level widget** before queueing any
   deletion: the `processEvents()` pass that drains the `deleteLater` queue
   also dispatches due timers, and a timer callback interleaving with the
   deletions lands on a half-destroyed widget — a native use-after-free at
   interpreter exit (the pristine-subprocess `-11` exits in the CI matrix).
2. `deleteLater()` all top-level widgets, then `processEvents()`.
3. **Drain the deferred-delete queue explicitly** with
   `sendPostedEvents(None, QEvent.DeferredDelete)` — DeferredDelete events
   are only handled by `exec()` loops or this exact call, not by a plain
   `processEvents()` (see the `deleteLater` trap below).
4. **Destroy the `QApplication` itself** (`shiboken6.delete(app)`) while
   the interpreter is still fully alive. Without this, the C++ app — and
   with it the QPA platform plugin and Qt's internal threads — is
   destroyed during `Py_FinalizeEx` in whatever order module teardown
   happens to produce; that destructor-ordering race was the residue
   behind "completed everything, then exited −11" on slow runners.
   `logging.raiseExceptions` is switched off first, since log emission
   racing stream closure at exit produces un-suppressable
   "`--- Logging error ---`" spam via `Handler.handleError`.

### Deferred-callback discipline (failure mode 4's fuel)

Every delayed call in `_gui/` must use `single_shot(parent, ms, callback)`
from `_gui/utility/_toolbox_qt.py` — a `QTimer` **parented to the object
the callback touches** — never a naked `QTimer.singleShot(ms,
bound_method)`. Parenting makes Qt destroy the armed timer with its owner,
so the callback can never fire on a dead object, in every teardown
ordering (PySide6's receiver-context auto-cancel covers clean mid-session
destruction, but not the chaotic at-exit/GC orderings where mode 4 lives).
Recurring timers likewise: always `QTimer(self)`, and models that poll a
view must liveness-check it (`shiboken6.isValid`) each tick — see
`QTreeModel_Base._view_alive`.

**Full-MetalGUI lifecycle tests run in subprocesses, never in the main
pytest process.** Two CI rounds proved why: the in-process stress test
and then the in-process click-and-arrow test each lost the mode-4 race
on a slow runner and segfaulted the entire pytest process, cancelling
the matrix. The pattern: the child proves its contract via printed
markers (strict -- a missing marker fails); a native death *after* the
contract is proven is reported as an attributed teardown NOTE. Related
QTest gotcha: matplotlib transforms yield PHYSICAL pixels while Qt
mouse events take LOGICAL coordinates -- divide by
``devicePixelRatioF()`` or synthetic clicks silently miss on HiDPI
displays (CI's ratio-1 runners will not catch the omission).

`tests/test_gui_lifecycle_stress.py` cycles build → close → pump-past-
every-timer-deadline and fails on any "already deleted" in the captured
output. Treat **any** `Internal C++ object ... already deleted` anywhere —
including "cosmetic" ones after a passing suite — as a live use-after-free
report, never as noise: one was dismissed as a benign at-exit artifact
here and CI then demonstrated the same leak class as real segfaults.
(Sensitivity: on a fast dev machine the stress cycles rarely lose the
race — PySide6 auto-cancels bound-method singleShots on clean mid-session
destruction — but on a slow macOS CI runner the first, in-process version
of this test reproduced mode 4 as a native `-11` that killed the whole
pytest process. It now runs its cycles in a subprocess so a native loss
of the race is attributed and reported instead of destroying the run.)

### Bisection toggles

These exist so a reporter can bisect a native crash without a debugger. Keep
them working:

| Variable | Effect |
|---|---|
| `QISKIT_METAL_DEBUG_INIT=1` | Trace each init step to stderr, flushed. Last line = failing call. |
| `QISKIT_METAL_GUI_NO_STYLESHEET=1` | Skip the stylesheet (it affects every paint). |
| `QISKIT_METAL_GUI_NO_PLOT=1` | Skip the matplotlib canvas embed. |
| `QISKIT_METAL_RESET_UI_SETTINGS=1` | Start from clean persisted state. |
| `QISKIT_METAL_RESTORE_LAYOUT=1` | Opt in to automatic window-layout restore at startup (off by default since the journal iteration). |
| `QISKIT_METAL_GUI_NO_ACTIVATE=1` | Quiet mode for automated on-screen runs: `AA_PluginApplication`, so the process never becomes the active app (no focus steal). Used by the pre-push hook; never default — focus-dependent tests need real activation. |
| `QISKIT_METAL_QT_HARDWARE_GL=1` | Undo the Windows software-GL default. |
| `QISKIT_METAL_GUI_FORCE_CLOSE=1` | Sets `main_window.force_close = True` at construction, so any `gui.main_window.close()` call skips `ok_to_close()`'s modal instead of hanging headless (see Teardown, above). Some frozen-Qt tutorial notebooks call `close()` as their last cell to demo the API; `_dev/rerun_auto.py` sets this for its `--write-frozen` Qt-display runs. Never set it for an interactive session — the modal is correct there. |

---

## Traps — changes that look safe and are not

- **`deleteLater()` is a false positive as a teardown fix.** It zeroes the
  crash in any test with no subsequent event loop, because the deletion never
  happens. Verify with `app.exec()`, never `processEvents()`. Seven candidate
  fixes were falsified this way; the table is in
  `tests/test_gui_logger_lifecycle.py`.

- **Moving the stylesheet load out of `restore_window_settings`.** Attempted
  2026-08-07 and reverted. The theme is genuinely skipped on all five
  early-return paths, so a fresh profile opens unstyled — a real, if cosmetic,
  bug. But applying it unconditionally turned `tests/test_gui_init.py` and
  `tests/test_gui_teardown.py` from 5 passed to 5 failed with `SIGBUS`. The
  early returns were accidentally protecting a known crash trigger. If this is
  revisited it needs the theme applied *inside* the cookie window and proof on
  Windows and Linux, not just macOS.

- **Log handlers must detach on `destroyed`, not `closeEvent`.** `close()`
  only hides; detaching there left a permanently dead log pane (reverted in
  `80f3655`).

- **Don't mark the GC reproducer `expectedFailure`** — it yields flaky
  "unexpected success". It is `@unittest.skip`ped deliberately.

- **A single clean run proves nothing** in either direction. The crash depends
  on memory layout.

- **Rejected outright in #1128:** disabling layout persistence on Windows,
  per-PID registry keys (breaks Jupyter), writer-PID detection (stale locks).

- **Check `qiskit_metal.__version__` in every report.** Two "still broken"
  reports were on 0.5.3.post1 and a 0.7.3 fork — neither had the fixes.

---

## Cross-platform reality

- The exit segfault (1) reproduces on Linux/Xvfb.
- The Windows `show()` crash (2) never reproduced under Xvfb or on GitHub
  Windows runners — runners start with an empty registry, which is exactly the
  state that works.
- macOS CI is what caught the cookie-scope gap.
- PySide6 version is **not** implicated: 6.6.0, 6.8.3 and 6.10.1 behave
  identically on the dangling-wrapper probe.

Consequence: **CI passing does not mean the crash is fixed.** Reporter
confirmation on the affected hardware is the only real signal, and that is how
v0.7.5 and v0.7.6 were validated (6/6 clean, then clean in JupyterLab and
VS Code with no fallbacks).

---

## Tests and the guarantee each encodes

`tests/test_gui_teardown.py`
- `test_metalgui_process_exits_cleanly` — builds a GUI, a second GUI, and
  `rebuild()` in a subprocess; asserts marker + exit code 0. Was `-11` before
  PR #1104.

`tests/test_gui_init.py` — each runs a real save subprocess, tampers exactly
one field, then re-reads on-disk state to prove the *correct* branch fired:
- `test_metalgui_init_completes` — marker catches silent abandonment, return
  code catches segfault.
- `test_metalgui_init_self_heals_across_kernel_switch` — the A→B→C kernel
  sequence. B may crash; C must always build.
- `test_metalgui_init_with_stale_fingerprint` — the display-fingerprint branch.
- `test_metalgui_init_recovers_from_crashed_restore` — the cookie branch.

`tests/test_gui_logger_lifecycle.py` — handler leaks, timer lifecycle, and the
skipped `test_dropping_metalgui_does_not_segfault`, which carries the gdb
backtrace and the falsified-candidate table as living documentation of
failure mode (4).

CI: `tests-gui-display` (Linux Xvfb) and `tests-gui-display-windows`
(`windows-2025`, `continue-on-error: true`).

---

## Still open

- Failure mode (4), the GC teardown segfault, on all versions —
  **substantially narrowed** by the deferred-callback discipline and the
  completed atexit teardown (explicit `QApplication` destruction, step 4
  above), but nondeterministic by nature, so treated as reduced rather
  than proven gone until the CI matrix stays quiet over many runs.
- **At-exit native crashes on slow runners** (`access violation` /
  `-11`, `<no Python frame>`, after startup completed): same story —
  the explicit `QApplication` destruction removes the finalize-time
  destructor race that produced them. The init/self-heal tests
  attribute any recurrence as a stderr NOTE (teardown, not startup),
  and `test_gui_teardown.py` remains the strict exit-cleanliness gate.
  Two earlier CI rounds misfiled these teardown crashes as startup
  failures; the marker-printed protocol prevents that.
- Whether the macOS `show()` → `QLayout::activate()` crash reported against a
  0.7.3 fork is resolved on 0.8.0 — the reporter never confirmed.
- ~~The at-exit `QCompleter already deleted` artifact~~ — **resolved, and
  the "benign" classification was wrong.** It was first dismissed as
  cosmetic noise (exit code stayed 0 locally); CI on PR #1180 then showed
  the same leak class as real `-11` segfaults on the macOS matrix and
  self-heal failures on the display jobs. Root causes fixed: the
  view-polling timers (liveness guard in `QTreeModel_Base`), the naked
  `QTimer.singleShot` sweep (`single_shot()` helper), and
  `_teardown_qt_widgets` stopping all timers before deletion. See
  "Deferred-callback discipline" above. The lasting rule: an "already
  deleted" anywhere in output is a use-after-free report, never noise.
