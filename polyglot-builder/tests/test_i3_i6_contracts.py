"""Contract tests for the gated write tasks I3 (safe change) and I6 (bug diagnosis).

These tasks let the agent modify an unfamiliar repo, so their TaskSpecs must enforce
the eval's safety requirements: gated permissions, minimal diffs, reproduce-before-fix,
source-cited root causes, and an explicit agent-suggested-vs-manually-verified note.
The tests below pin those guarantees so a future edit can't silently weaken them.
"""

from __future__ import annotations

import pytest

from polyglot_eval.tasks.i3_safe_change import SPEC as I3
from polyglot_eval.tasks.i6_bug_diagnosis import SPEC as I6
from polyglot_eval.tasks.registry import TASK_REGISTRY, get_task


# ----------------------------------------------------------------------------- #
# Shared safety guarantees                                                       #
# ----------------------------------------------------------------------------- #

@pytest.mark.parametrize("spec", [I3, I6], ids=["I3", "I6"])
def test_write_tasks_are_gated(spec):
    """Both write tasks run in the gated ('default') permission mode, not auto-accept."""
    assert spec.writes_repo is True
    assert spec.permission_mode == "default"


@pytest.mark.parametrize("spec", [I3, I6], ids=["I3", "I6"])
def test_write_tasks_forbid_history_mutation(spec):
    """The system prompt must forbid commit/push/merge so the agent can't alter history."""
    prompt = spec.system_prompt.lower()
    for forbidden in ("commit", "push", "merge"):
        assert forbidden in prompt, f"{spec.id} prompt should mention {forbidden!r}"
    assert "never" in prompt or "do not" in prompt or "not run" in prompt


@pytest.mark.parametrize("spec", [I3, I6], ids=["I3", "I6"])
def test_write_tasks_have_verification_note(spec):
    """Every write task must surface the 'agent suggested vs manually verified' deliverable."""
    keys = spec.required_section_keys
    assert "verification_note" in keys
    label = next(d.label for d in spec.deliverables if d.key == "verification_note").lower()
    assert "manual" in label and "agent" in label


@pytest.mark.parametrize("spec", [I3, I6], ids=["I3", "I6"])
def test_write_tasks_do_not_expose_destructive_tools(spec):
    """Allowed built-in tools must not include anything beyond read/edit/run primitives."""
    allowed = set(spec.allowed_tools)
    assert allowed.issubset({"Read", "Grep", "Glob", "Edit", "Write", "Bash"})


@pytest.mark.parametrize("spec", [I3, I6], ids=["I3", "I6"])
def test_write_tasks_demand_minimal_diff(spec):
    """The prompt must constrain scope to a minimal diff (no broad refactors)."""
    prompt = spec.system_prompt.lower()
    assert "minimal" in prompt
    assert "refactor" in prompt  # appears as "do not refactor ..."


# ----------------------------------------------------------------------------- #
# I3 — safe change specifics                                                     #
# ----------------------------------------------------------------------------- #

def test_i3_requires_test_and_diff_deliverables():
    keys = set(I3.required_section_keys)
    assert {"branch", "files_changed", "diff_summary", "test_command", "test_result"} <= keys


def test_i3_kickoff_carries_self_contained_change():
    assert "validation" in I3.kickoff.lower()
    assert "[describe" not in I3.kickoff


def test_i3_prompt_requests_diff_artifact():
    assert "diff.patch" in I3.system_prompt


# ----------------------------------------------------------------------------- #
# I6 — bug diagnosis specifics                                                   #
# ----------------------------------------------------------------------------- #

def test_i6_requires_reproduce_before_fix():
    prompt = I6.system_prompt.lower()
    assert "reproduce" in prompt
    # The rule must order reproduction before the fix.
    assert prompt.index("reproduce") < prompt.index("fix")


def test_i6_root_cause_requires_file_and_line_citation():
    label = next(d.label for d in I6.deliverables if d.key == "root_cause").lower()
    assert "file" in label and "line" in label


def test_i6_requires_verification_and_regression():
    keys = set(I6.required_section_keys)
    assert {"repro_steps", "root_cause", "verification_output", "regression_check"} <= keys


def test_i6_prompt_requests_fix_artifact():
    assert "fix.patch" in I6.system_prompt


# ----------------------------------------------------------------------------- #
# Registry wiring                                                                #
# ----------------------------------------------------------------------------- #

def test_registry_returns_gated_write_specs():
    assert get_task("I3") is I3
    assert get_task("I6") is I6
    assert TASK_REGISTRY["I3"].writes_repo
    assert TASK_REGISTRY["I6"].writes_repo


def test_report_filenames_are_unique_and_well_formed():
    assert I3.report_filename == "I3_safe_change.md"
    assert I6.report_filename == "I6_bug_diagnosis.md"
