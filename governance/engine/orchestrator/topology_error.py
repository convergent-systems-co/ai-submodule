"""TopologyError -- hard-blocking exception for PM mode topology violations.

Replaces advisory TopologyWarning for enforcement paths. When PM mode topology
invariants are violated at phase transitions, TopologyError is raised to block
the transition.

TopologyWarning remains in agent_registry.py for backward compatibility, but
enforcement paths now use TopologyError exclusively.
"""

from __future__ import annotations


class TopologyError(RuntimeError):
    """Hard-blocking topology violation error.

    Raised when PM mode topology invariants are violated at phase transitions.
    Unlike TopologyWarning (advisory), this exception blocks the transition.

    Attributes:
        phase: The phase being transitioned to.
        rule: Short identifier for the violated rule (e.g. ``'missing_devops_engineer'``).
        detail: Human-readable description of the violation.
        missing_personas: List of persona names that are missing or misconfigured.
    """

    def __init__(
        self,
        phase: int,
        rule: str,
        detail: str = "",
        missing_personas: list[str] | None = None,
    ):
        self.phase = phase
        self.rule = rule
        self.detail = detail
        self.missing_personas = missing_personas or []
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        msg = f"Topology enforcement blocked phase {self.phase} [{self.rule}]"
        if self.detail:
            msg += f": {self.detail}"
        if self.missing_personas:
            msg += f" (missing: {', '.join(self.missing_personas)})"
        return msg

    def to_dict(self) -> dict:
        """Serialize for JSON output and audit logging."""
        return {
            "phase": self.phase,
            "rule": self.rule,
            "detail": self.detail,
            "missing_personas": self.missing_personas,
        }

    def __repr__(self) -> str:
        return (
            f"TopologyError(phase={self.phase}, rule={self.rule!r}, "
            f"detail={self.detail!r}, missing_personas={self.missing_personas})"
        )
