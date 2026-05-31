"""Re-execute whitelisted tutorial notebooks under the lite install.

Two whitelists, two policies:

  ↻  ``_dev/notebooks-auto-refresh.txt``  → run with ``--inplace``.
     Outputs are written back into the source ``.ipynb``. Used for
     pure-matplotlib / pure-Python tutorials where the headless render
     is the canonical published artefact.

  ✱  ``_dev/notebooks-frozen-qt.txt``     → run with outputs to /tmp.
     Source ``.ipynb`` is NOT touched. Used for tutorials whose
     committed outputs are hand-curated full Qt-window screenshots
     of the desktop ``MetalGUI``; the published docs rely on those
     for the "look at the full IDE" effect. CI still runs them so a
     pass/fail signal catches regressions, but never clobbers the
     curated screenshots with headless matplotlib renders.

Both lists feed the same CI job (``tests-lite → Execute whitelisted
tutorial notebooks`` in ``.github/workflows/main.yml``), keeping the
local "did my change break a tutorial?" check bit-identical to CI.

USAGE
-----

  # dry-run — list what would execute, don't run anything
  uv run python _dev/rerun_auto.py

  # actually execute, in parallel (default: 4 workers)
  uv run python _dev/rerun_auto.py --run

  # serial execution (helpful for debugging a hung notebook)
  uv run python _dev/rerun_auto.py --run --jobs 1

  # restrict to a single section
  uv run python _dev/rerun_auto.py --run --filter 1-Overview

The same whitelist drives the CI ``tutorials-execute`` job in
``.github/workflows/main.yml`` so the local "did my change break a
notebook?" check is bit-identical to what CI will do.

WHAT THIS DOES NOT DO
---------------------

Re-execute external-gated notebooks (Ansys / gmsh / Elmer / Cross-
Resonance). Those need the relevant toolchain installed and a license;
the maintainer re-runs them locally when those tools change. See the
``🟡 External-gated`` block in the whitelist file for the list.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AUTO_REFRESH_LIST = REPO / "_dev" / "notebooks-auto-refresh.txt"
FROZEN_QT_LIST = REPO / "_dev" / "notebooks-frozen-qt.txt"
TIMEOUT_SEC = 240  # per-notebook hard cap


def _load_list(path: Path) -> list[Path]:
    if not path.exists():
        return []
    paths: list[Path] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = REPO / line
        if not p.exists():
            print(f"  ! whitelist entry not found on disk: {line}")
            continue
        paths.append(p)
    return paths


def run_one(nb_path: Path, inplace: bool = True) -> tuple[Path, bool, str, float]:
    """Execute a single notebook. Returns (path, ok, log_excerpt, seconds).

    When ``inplace`` is False, outputs land in ``/tmp/<basename>.executed.ipynb``
    instead of being written back into the source — used for the
    frozen-Qt set, where committed outputs are hand-curated and must
    not be clobbered by headless re-runs.
    """
    t0 = time.monotonic()
    env = {
        **os.environ,
        "QISKIT_METAL_HEADLESS": "1",
        "QISKIT_METAL_HEADLESS_QUIET": "1",
        "MPLBACKEND": "Agg",
    }
    # In CI the lite venv was created with ``uv venv`` and a custom
    # ipykernel name; honour ``JUPYTER_KERNEL_NAME`` so nbconvert
    # uses that kernel instead of the (absent) default ``python3``.
    cmd = [
        "jupyter",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        f"--ExecutePreprocessor.timeout={TIMEOUT_SEC}",
    ]
    if inplace:
        cmd.append("--inplace")
    else:
        # Pipe outputs into /tmp so the source notebook stays untouched.
        cmd.extend(
            [
                "--output-dir",
                "/tmp",
                "--output",
                f"{nb_path.stem}.executed.ipynb",
            ]
        )
    kernel = os.environ.get("JUPYTER_KERNEL_NAME")
    if kernel:
        cmd.append(f"--ExecutePreprocessor.kernel_name={kernel}")
    cmd.append(str(nb_path))
    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO),
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SEC + 30,
        )
        ok = result.returncode == 0
        log = result.stderr if not ok else "OK"
        return nb_path, ok, log[-800:], time.monotonic() - t0
    except subprocess.TimeoutExpired:
        return nb_path, False, f"TIMEOUT (> {TIMEOUT_SEC + 30}s)", time.monotonic() - t0
    except Exception as exc:
        return nb_path, False, f"{type(exc).__name__}: {exc}", time.monotonic() - t0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run", action="store_true", help="actually execute (default is dry-run)"
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=4,
        help="parallel workers (default 4; pass 1 for serial debugging)",
    )
    parser.add_argument(
        "--filter",
        default="",
        help="only execute notebooks whose path contains this substring",
    )
    args = parser.parse_args()

    auto_refresh = _load_list(AUTO_REFRESH_LIST)
    frozen_qt = _load_list(FROZEN_QT_LIST)
    if args.filter:
        auto_refresh = [p for p in auto_refresh if args.filter in str(p)]
        frozen_qt = [p for p in frozen_qt if args.filter in str(p)]

    print(f"Auto-refresh (--inplace): {len(auto_refresh)}")
    for p in auto_refresh:
        print(f"  ↻ {p.relative_to(REPO)}")
    print(f"\nFrozen Qt (check-only):   {len(frozen_qt)}")
    for p in frozen_qt:
        print(f"  ✱ {p.relative_to(REPO)}")

    if not args.run:
        print("\nDry-run. Pass --run to execute.")
        return 0

    print(f"\nExecuting with {args.jobs} parallel worker(s)...\n")
    work = [(p, True) for p in auto_refresh] + [(p, False) for p in frozen_qt]

    def _exec(item):
        nb, inplace = item
        return run_one(nb, inplace=inplace)

    if args.jobs == 1:
        results = [_exec(it) for it in work]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            results = list(pool.map(_exec, work))

    print("\n=== Summary ===")
    passed = failed = 0
    for path, ok, log, secs in results:
        rel = path.relative_to(REPO)
        if ok:
            passed += 1
            print(f"  ✓ {secs:5.1f}s  {rel}")
        else:
            failed += 1
            print(f"  ✗ {secs:5.1f}s  {rel}")
            print(f"      ...{log[-400:]}")

    print(f"\n{passed} passed, {failed} failed.")
    if failed:
        print(
            "\nThis is a real signal. If a notebook in the whitelist no longer\n"
            "runs under the lite install, either fix the notebook or move its\n"
            "entry into the External-gated comment block at the bottom of\n"
            "_dev/auto-runnable-notebooks.txt.\n"
        )
        return 1
    print("After this run, sync the tutorials/ mirror:")
    print("    uv run python _dev/sync_two_folders.py --write")
    return 0


if __name__ == "__main__":
    sys.exit(main())
