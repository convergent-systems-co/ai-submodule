#!/usr/bin/env python3
"""Verify the integrity of a hash-chained audit trail.

Usage:
    python governance/bin/verify-audit-chain.py <log-file>
    python governance/bin/verify-audit-chain.py .artifacts/state/sessions/20260302-session-1.jsonl

Exit codes:
    0 = Chain is valid
    1 = Chain is broken (tamper detected)
    2 = File not found
"""

import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root))

from governance.engine.orchestrator.audit import AuditLog


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python governance/bin/verify-audit-chain.py <log-file>", file=sys.stderr)
        return 2

    log_path = Path(sys.argv[1])
    if not log_path.exists():
        print(f"File not found: {log_path}", file=sys.stderr)
        return 2

    audit_log = AuditLog(log_path)
    result = audit_log.verify_chain()

    if result.valid:
        print(f"VALID: Hash chain verified. {result.total_entries} entries, all intact.")
        return 0
    else:
        print(f"BROKEN: {result.reason}")
        print(f"  Total entries: {result.total_entries}")
        print(f"  Verified before break: {result.verified_entries}")
        print(f"  Break detected at index: {result.broken_at_index}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
