# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pyyaml>=6.0",
#     "packaging>=23.0",
# ]
# ///
"""Check that ``environment.yml`` and ``pyproject.toml`` agree on
version constraints for shared dependencies.

Both files declare dependency floors and ceilings independently. When
they drift, conda users (who follow ``environment.yml``) end up with a
different supported version range than pip users (who follow
``pyproject.toml``). This silently broke ``qutip`` and ``scqubits``
support in past releases.

The script extracts the floor (lowest version allowed) and ceiling
(highest, if any) from each spec, then for every package present in
both files asserts:

    env_floor   >= pyproject_floor
    env_ceiling <= pyproject_ceiling  (if pyproject has one)

Exits 0 if consistent, 1 otherwise. Designed to run in CI; also
runnable locally as ``uv run scripts/check_env_consistency.py``.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

import yaml
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_pyproject() -> dict[str, SpecifierSet]:
    """Map package name (normalised, lowercase) to its SpecifierSet
    from ``pyproject.toml``'s ``[project.dependencies]``."""
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    result = {}
    for raw in data["project"]["dependencies"]:
        req = Requirement(raw)
        result[normalise(req.name)] = req.specifier
    return result


def load_environment_yml() -> dict[str, SpecifierSet]:
    """Map package name (normalised, lowercase) to its SpecifierSet
    from ``environment.yml`` (both the top-level conda deps and the
    nested ``pip:`` deps)."""
    data = yaml.safe_load((REPO_ROOT / "environment.yml").read_text())
    result = {}
    for entry in data["dependencies"]:
        if isinstance(entry, str):
            parsed = parse_conda_spec(entry)
            if parsed is not None:
                name, spec = parsed
                result[normalise(name)] = spec
        elif isinstance(entry, dict) and "pip" in entry:
            for raw in entry["pip"]:
                req = Requirement(raw)
                result[normalise(req.name)] = req.specifier
    return result


def parse_conda_spec(entry: str) -> tuple[str, SpecifierSet] | None:
    """Parse a single conda-style dependency string into
    ``(name, SpecifierSet)``.

    Handles PEP-440-compatible operators (``>=``, ``~=``, ``<``, etc.).
    Returns ``None`` for entries that aren't real package specs
    (``python``, channel-like ``pip``).
    """
    # Strip inline comments.
    spec_str = entry.split("#", 1)[0].strip()
    if not spec_str:
        return None
    # Skip bare package names with no operator like "jupyter" — we have
    # no version to compare. Skip "python" entirely (handled by
    # `requires-python` in pyproject.toml, not project deps).
    match = re.match(r"^([A-Za-z0-9_.\-]+)\s*(.*)$", spec_str)
    if not match:
        return None
    name, rest = match.group(1), match.group(2).strip()
    if name.lower() == "python":
        return None
    if not rest:
        return name, SpecifierSet("")
    # conda allows commas and PEP-440 operators; packaging.SpecifierSet
    # handles all of these.
    try:
        return name, SpecifierSet(rest)
    except Exception:
        return None


def normalise(name: str) -> str:
    return name.lower().replace("_", "-")


def floor_of(spec: SpecifierSet) -> Version | None:
    """Return the smallest version allowed by ``spec``, or ``None`` if
    the spec has no lower bound."""
    candidates: list[Version] = []
    for s in spec:
        if s.operator in (">=", "==", "~="):
            candidates.append(Version(s.version))
        elif s.operator == ">":
            # Approximate: next patch above s.version.
            candidates.append(Version(s.version))
    return max(candidates) if candidates else None


def ceiling_of(spec: SpecifierSet) -> Version | None:
    """Return the largest version *not* allowed by ``spec`` (the upper
    bound), or ``None`` if the spec has no upper bound."""
    candidates: list[Version] = []
    for s in spec:
        if s.operator == "<":
            candidates.append(Version(s.version))
        elif s.operator == "<=":
            candidates.append(Version(s.version))
        elif s.operator == "~=":
            # ~=X.Y means >=X.Y, <X+1.0. ~=X.Y.Z means >=X.Y.Z, <X.Y+1.0.
            v = Version(s.version)
            parts = v.release
            if len(parts) >= 2:
                # Bump the second-to-last component.
                new_parts = parts[:-1]
                new_parts = new_parts[:-1] + (new_parts[-1] + 1,)
                candidates.append(Version(".".join(str(p) for p in new_parts)))
    return min(candidates) if candidates else None


def main() -> int:
    pyproject = load_pyproject()
    env = load_environment_yml()

    shared = sorted(set(pyproject) & set(env))
    if not shared:
        print(
            "No shared packages between pyproject.toml and environment.yml.",
            file=sys.stderr,
        )
        return 1

    failures: list[str] = []

    for pkg in shared:
        pp_spec = pyproject[pkg]
        env_spec = env[pkg]

        pp_floor = floor_of(pp_spec)
        env_floor = floor_of(env_spec)
        if pp_floor and env_floor and env_floor < pp_floor:
            failures.append(
                f"  {pkg}: environment.yml floor {env_floor} < "
                f"pyproject.toml floor {pp_floor}"
                f"  (env={env_spec}, pyproject={pp_spec})"
            )
        if pp_floor and not env_floor:
            failures.append(
                f"  {pkg}: pyproject.toml requires >={pp_floor} but "
                f"environment.yml has no floor"
                f"  (env={env_spec}, pyproject={pp_spec})"
            )

        pp_ceil = ceiling_of(pp_spec)
        env_ceil = ceiling_of(env_spec)
        if pp_ceil and not env_ceil:
            failures.append(
                f"  {pkg}: pyproject.toml requires <{pp_ceil} but "
                f"environment.yml has no ceiling"
                f"  (env={env_spec}, pyproject={pp_spec})"
            )
        elif pp_ceil and env_ceil and env_ceil > pp_ceil:
            failures.append(
                f"  {pkg}: environment.yml ceiling {env_ceil} > "
                f"pyproject.toml ceiling {pp_ceil}"
                f"  (env={env_spec}, pyproject={pp_spec})"
            )

    if failures:
        print(
            "environment.yml drifts from pyproject.toml:\n" + "\n".join(failures),
            file=sys.stderr,
        )
        print(
            "\nFix the constraints in environment.yml so a conda "
            "install picks up the same versions a pip install does.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: {len(shared)} shared packages, no drift.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
