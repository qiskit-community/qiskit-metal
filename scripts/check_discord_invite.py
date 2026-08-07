# /// script
# requires-python = ">=3.10"
# ///
"""Check that every Discord invite advertised in the repo is alive and permanent.

The community invite is hardcoded in a dozen places — README, ROADMAP, the
docs landing page, the issue-template chooser, the tutorials index. Discord
invites expire after 7 days unless explicitly created with "Expire after:
Never", so a temporary invite silently kills every one of those links at
once, and nobody notices until a newcomer says so on a discussion thread.
That has already happened once (invite ``kaZ3UFuq``).

This script scans the repo for ``discord.gg/<code>`` links and asks Discord
about each unique code. A code fails if it is:

- **dead** — the invite has expired or was revoked, or
- **temporary** — it resolves but carries an ``expires_at``, meaning it is
  on a countdown and will become the previous case.

The second check is the important one: it catches a bad invite while the
link still works, rather than after it breaks.

Run it directly::

    uv run scripts/check_discord_invite.py

Exits 0 if every invite is alive and permanent, 1 otherwise. Runs weekly in
CI (``.github/workflows/link-health.yml``), not per-PR — a lapsed invite is
not caused by the pull request that happens to run next, and gating every
PR on a third-party API would trade one flaky link for a flaky pipeline.
"""

import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

INVITE_RE = re.compile(r"discord\.gg/([A-Za-z0-9-]+)")
API = "https://discord.com/api/v10/invites/{code}"
TIMEOUT = 15


def tracked_files():
    """Every file git knows about — avoids scanning .git/ and build output."""
    out = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    )
    return out.stdout.splitlines()


def find_invites():
    """Map each invite code to the ``path:line`` locations that reference it."""
    found = {}
    for path in tracked_files():
        try:
            text = open(path, encoding="utf-8", errors="ignore").read()
        except (OSError, IsADirectoryError):
            continue
        if "discord.gg/" not in text:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for code in INVITE_RE.findall(line):
                found.setdefault(code, []).append(f"{path}:{lineno}")
    return found


def probe(code):
    """Ask Discord about one invite.

    Returns (ok, detail). ``ok`` is False for a dead invite, an invite with
    an expiry, or an unreadable response.
    """
    req = urllib.request.Request(
        API.format(code=code), headers={"User-Agent": "quantum-metal-link-check"}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return False, "dead — Discord returns 404 Unknown Invite"
        return False, f"HTTP {exc.code} from Discord"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return False, f"could not reach Discord ({exc})"

    guild = (data.get("guild") or {}).get("name", "?")
    expires = data.get("expires_at")
    if expires:
        return False, f"temporary — '{guild}' invite expires at {expires}"
    return True, f"alive and permanent — '{guild}'"


def main():
    invites = find_invites()
    if not invites:
        print("No discord.gg links found — nothing to check.")
        return 0

    failures = []
    for code, locations in sorted(invites.items()):
        ok, detail = probe(code)
        mark = "OK  " if ok else "FAIL"
        print(f"{mark} discord.gg/{code}: {detail}  ({len(locations)} reference(s))")
        if not ok:
            failures.append((code, detail, locations))

    if failures:
        print(
            "\nERROR: one or more advertised Discord invites are unusable.",
            file=sys.stderr,
        )
        for code, detail, locations in failures:
            print(f"\n  discord.gg/{code} — {detail}", file=sys.stderr)
            for loc in locations:
                print(f"      {loc}", file=sys.stderr)
        print(
            "\nMint a replacement in Discord with 'Expire after: Never' and\n"
            "'Max uses: No limit', then update every location listed above.\n"
            "Leave 'Bypass Join Applications' OFF — this link is published\n"
            "publicly, and the application step is the spam gate.",
            file=sys.stderr,
        )
        return 1

    print(f"\n✓ All {len(invites)} advertised invite(s) alive and permanent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
