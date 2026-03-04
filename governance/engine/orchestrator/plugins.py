"""Plugin architecture for prompt/skill extensibility.

Allows consuming repos to register custom extensions via ``project.yaml``:

- **Custom phases:** Scripts that execute as additional orchestrator phases.
- **Custom panel types:** Prompts that act as additional review panels.
- **Hooks:** Scripts triggered at lifecycle points (post-merge, pre-dispatch, etc.).

Extensions are loaded at orchestrator init time and run within the same
containment and capacity constraints as built-in phases.

Example project.yaml:

.. code-block:: yaml

    governance:
      extensions:
        phases:
          - name: deploy
            script: scripts/deploy-phase.py
            after_phase: 5
        panel_types:
          - name: custom-security
            prompt: prompts/custom-security-review.md
            weight: 0.10
        hooks:
          post_merge:
            - scripts/post-merge.sh
          pre_dispatch:
            - scripts/pre-dispatch.sh
"""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class PhasePlugin:
    """A custom phase that extends the orchestrator pipeline.

    Attributes:
        name: Human-readable name for the phase.
        script: Path to the script to execute (relative to repo root).
        after_phase: Phase number after which this plugin runs.
        timeout_seconds: Maximum execution time.
        required: If True, failure blocks the pipeline. If False, advisory only.
    """

    name: str = ""
    script: str = ""
    after_phase: int = 5
    timeout_seconds: int = 300
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PanelPlugin:
    """A custom review panel type.

    Attributes:
        name: Panel identifier (e.g., ``custom-security``).
        prompt: Path to the prompt markdown file (relative to repo root).
        weight: Confidence weight for policy engine aggregation.
        required: If True, emission is required for merge decisions.
    """

    name: str = ""
    prompt: str = ""
    weight: float = 0.05
    required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HookConfig:
    """Lifecycle hook configuration.

    Attributes:
        post_merge: Scripts to run after PR merge.
        pre_dispatch: Scripts to run before agent dispatch.
        post_review: Scripts to run after review collection.
        on_shutdown: Scripts to run on orchestrator shutdown.
    """

    post_merge: list[str] = field(default_factory=list)
    pre_dispatch: list[str] = field(default_factory=list)
    post_review: list[str] = field(default_factory=list)
    on_shutdown: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExtensionsConfig:
    """Top-level extensions configuration.

    Parsed from ``governance.extensions`` in ``project.yaml``.
    """

    phases: list[PhasePlugin] = field(default_factory=list)
    panel_types: list[PanelPlugin] = field(default_factory=list)
    hooks: HookConfig = field(default_factory=HookConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ExtensionsConfig:
        """Parse extensions config from a dictionary.

        Args:
            data: Dictionary from ``governance.extensions`` in project.yaml.

        Returns:
            ExtensionsConfig instance.
        """
        if not data:
            return cls()

        phases = [
            PhasePlugin(
                name=p.get("name", ""),
                script=p.get("script", ""),
                after_phase=p.get("after_phase", 5),
                timeout_seconds=p.get("timeout_seconds", 300),
                required=p.get("required", True),
            )
            for p in data.get("phases", [])
        ]

        panel_types = [
            PanelPlugin(
                name=pt.get("name", ""),
                prompt=pt.get("prompt", ""),
                weight=pt.get("weight", 0.05),
                required=pt.get("required", False),
            )
            for pt in data.get("panel_types", [])
        ]

        hooks_data = data.get("hooks", {}) or {}
        hooks = HookConfig(
            post_merge=hooks_data.get("post_merge", []),
            pre_dispatch=hooks_data.get("pre_dispatch", []),
            post_review=hooks_data.get("post_review", []),
            on_shutdown=hooks_data.get("on_shutdown", []),
        )

        return cls(phases=phases, panel_types=panel_types, hooks=hooks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phases": [p.to_dict() for p in self.phases],
            "panel_types": [pt.to_dict() for pt in self.panel_types],
            "hooks": self.hooks.to_dict(),
        }

    @property
    def has_extensions(self) -> bool:
        """True if any extensions are configured."""
        return bool(self.phases) or bool(self.panel_types) or bool(
            self.hooks.post_merge
            or self.hooks.pre_dispatch
            or self.hooks.post_review
            or self.hooks.on_shutdown
        )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_extensions(
    config: ExtensionsConfig,
    repo_root: str | Path,
) -> list[str]:
    """Validate extensions configuration.

    Checks that referenced scripts and prompts exist, names are unique,
    and configurations are well-formed.

    Args:
        config: Extensions configuration to validate.
        repo_root: Repository root for resolving relative paths.

    Returns:
        List of error messages. Empty if valid.
    """
    errors: list[str] = []
    root = Path(repo_root)

    # Validate phase plugins
    phase_names: set[str] = set()
    for phase in config.phases:
        if not phase.name:
            errors.append("Phase plugin missing 'name'.")
        elif phase.name in phase_names:
            errors.append(f"Duplicate phase plugin name: '{phase.name}'.")
        else:
            phase_names.add(phase.name)

        if not phase.script:
            errors.append(f"Phase plugin '{phase.name}' missing 'script'.")
        elif not (root / phase.script).exists():
            errors.append(
                f"Phase plugin '{phase.name}' script not found: {phase.script}"
            )

        if phase.after_phase < 0 or phase.after_phase > 7:
            errors.append(
                f"Phase plugin '{phase.name}' after_phase must be 0-7, "
                f"got {phase.after_phase}."
            )

        if phase.timeout_seconds < 0:
            errors.append(
                f"Phase plugin '{phase.name}' timeout_seconds must be non-negative."
            )

    # Validate panel plugins
    panel_names: set[str] = set()
    for panel in config.panel_types:
        if not panel.name:
            errors.append("Panel plugin missing 'name'.")
        elif panel.name in panel_names:
            errors.append(f"Duplicate panel plugin name: '{panel.name}'.")
        else:
            panel_names.add(panel.name)

        if not panel.prompt:
            errors.append(f"Panel plugin '{panel.name}' missing 'prompt'.")
        elif not (root / panel.prompt).exists():
            errors.append(
                f"Panel plugin '{panel.name}' prompt not found: {panel.prompt}"
            )

        if panel.weight < 0.0 or panel.weight > 1.0:
            errors.append(
                f"Panel plugin '{panel.name}' weight must be 0.0-1.0, "
                f"got {panel.weight}."
            )

    # Validate hook scripts
    all_hooks = {
        "post_merge": config.hooks.post_merge,
        "pre_dispatch": config.hooks.pre_dispatch,
        "post_review": config.hooks.post_review,
        "on_shutdown": config.hooks.on_shutdown,
    }
    for hook_name, scripts in all_hooks.items():
        for script in scripts:
            if not (root / script).exists():
                errors.append(
                    f"Hook '{hook_name}' script not found: {script}"
                )

    return errors


# ---------------------------------------------------------------------------
# Plugin registry
# ---------------------------------------------------------------------------


class PluginRegistry:
    """Registry for loaded plugins.

    Holds validated extension configurations and provides lookup methods
    for the orchestrator and policy engine.
    """

    def __init__(self, config: ExtensionsConfig):
        self._config = config
        self._phase_map: dict[str, PhasePlugin] = {
            p.name: p for p in config.phases
        }
        self._panel_map: dict[str, PanelPlugin] = {
            p.name: p for p in config.panel_types
        }

    @property
    def config(self) -> ExtensionsConfig:
        return self._config

    @property
    def has_extensions(self) -> bool:
        return self._config.has_extensions

    def get_phase_plugins(self, after_phase: int | None = None) -> list[PhasePlugin]:
        """Get phase plugins, optionally filtered by after_phase.

        Args:
            after_phase: If set, only return plugins for this phase position.

        Returns:
            List of matching PhasePlugin objects.
        """
        if after_phase is None:
            return list(self._config.phases)
        return [p for p in self._config.phases if p.after_phase == after_phase]

    def get_panel_plugins(self) -> list[PanelPlugin]:
        """Get all panel plugins."""
        return list(self._config.panel_types)

    def get_panel_by_name(self, name: str) -> PanelPlugin | None:
        """Look up a panel plugin by name."""
        return self._panel_map.get(name)

    def get_hook_scripts(self, hook_name: str) -> list[str]:
        """Get scripts for a lifecycle hook.

        Args:
            hook_name: One of post_merge, pre_dispatch, post_review, on_shutdown.

        Returns:
            List of script paths.
        """
        return getattr(self._config.hooks, hook_name, [])

    def to_dict(self) -> dict[str, Any]:
        """Serialize the registry for audit/debug."""
        return self._config.to_dict()


# ---------------------------------------------------------------------------
# Hook executor
# ---------------------------------------------------------------------------


@dataclass
class HookResult:
    """Result of executing a hook script."""

    script: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    success: bool = True
    timed_out: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def execute_hook(
    script: str,
    repo_root: str | Path,
    timeout_seconds: int = 60,
    env: dict[str, str] | None = None,
    dry_run: bool = False,
) -> HookResult:
    """Execute a hook script.

    Args:
        script: Relative path to the script.
        repo_root: Repository root directory.
        timeout_seconds: Maximum execution time.
        env: Additional environment variables.
        dry_run: If True, simulate execution.

    Returns:
        HookResult with execution details.
    """
    if dry_run:
        return HookResult(
            script=script,
            exit_code=0,
            stdout="dry run",
            success=True,
        )

    root = Path(repo_root)
    script_path = root / script

    if not script_path.exists():
        return HookResult(
            script=script,
            exit_code=127,
            stderr=f"Script not found: {script}",
            success=False,
        )

    try:
        result = subprocess.run(
            [str(script_path)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )
        return HookResult(
            script=script,
            exit_code=result.returncode,
            stdout=result.stdout[:2000],
            stderr=result.stderr[:2000],
            success=result.returncode == 0,
        )
    except subprocess.TimeoutExpired:
        return HookResult(
            script=script,
            exit_code=-1,
            stderr=f"Timed out after {timeout_seconds}s",
            success=False,
            timed_out=True,
        )
    except (OSError, FileNotFoundError) as exc:
        return HookResult(
            script=script,
            exit_code=-1,
            stderr=str(exc),
            success=False,
        )


def execute_hooks(
    hook_name: str,
    registry: PluginRegistry,
    repo_root: str | Path,
    timeout_seconds: int = 60,
    dry_run: bool = False,
) -> list[HookResult]:
    """Execute all scripts for a given lifecycle hook.

    Args:
        hook_name: Hook name (post_merge, pre_dispatch, etc.).
        registry: Plugin registry with hook configurations.
        repo_root: Repository root directory.
        timeout_seconds: Max time per script.
        dry_run: If True, simulate execution.

    Returns:
        List of HookResult objects, one per script.
    """
    scripts = registry.get_hook_scripts(hook_name)
    results: list[HookResult] = []

    for script in scripts:
        result = execute_hook(
            script=script,
            repo_root=repo_root,
            timeout_seconds=timeout_seconds,
            dry_run=dry_run,
        )
        results.append(result)

    return results
