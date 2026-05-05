from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "AGENTS.md",
    "CURRENT_TASK",
    "README.md",
    "task_details.md",
    "mentor_feedback.md",
    "config/runtime_status.json",
    "docs/backend-stage4-control-plane/README.md",
    "docs/backend-stage4-control-plane/01_brief_traceability.md",
    "docs/backend-stage4-control-plane/02_execution_roadmap.md",
    "docs/backend-stage4-control-plane/03_design_with_me_protocol.md",
    "docs/backend-stage4-control-plane/04_decisions_log.md",
    "docs/backend-stage4-control-plane/05_evidence_log.md",
    "docs/backend-stage4-control-plane/06_validation_strategy.md",
    "docs/backend-stage4-control-plane/07_qa_checklist.md",
    "docs/backend-stage4-control-plane/08_interview_defense_bank.md",
    "docs/backend-stage4-control-plane/09_submission_and_diagram_plan.md",
    "drafts/insighta-labs-stage4-design.md",
    "diagrams/README.md",
    "diagrams/source/README.md",
    "diagrams/exported/README.md",
    "journal/2026-05-04-stage4-governance.md",
]

TASK_PACKETS = [
    "B4-GOV-001",
    "B4-REQ-001",
    "B4-ARCH-001",
    "B4-DATA-001",
    "B4-DECISIONS-001",
    "B4-DIAGRAM-001",
    "B4-SUBMISSION-001",
]

FORBIDDEN_EXPERIMENT_PATHS = [
    "app",
    "api",
    "backend",
    "server",
    "src",
    "tests/load",
    "benchmarks",
    "load-tests",
    "prototype",
    "prototypes",
    "Dockerfile",
    "docker-compose.yml",
    "compose.yml",
    "requirements.txt",
    "pyproject.toml",
    "package.json",
]

SUBMISSION_REQUIRED_QA_ITEMS = [
    "- [x] Functional requirements are written.",
    "- [x] Non-functional requirements are written.",
    "- [x] Architecture section is written.",
    "- [x] Data-flow section is written.",
    "- [x] Design decisions map back to requirements.",
    "- [x] Trade-offs and limitations are written.",
    "- [x] Architecture diagram source exists in `diagrams/source/`.",
    "- [x] Exported diagram asset is ready for embedding.",
    "- [x] Diagram is embedded in the Google Docs submission.",
    "- [x] Original diagram source link is included.",
    "- [x] Google Docs sharing is set to \"Anyone with the link can view\".",
    "- [x] Final draft fits within 2-7 pages.",
]


class CheckResult:
    def __init__(self) -> None:
        self.failures: list[str] = []

    def pass_(self, message: str) -> None:
        print(f"[PASS] {message}")

    def fail(self, message: str) -> None:
        print(f"[FAIL] {message}")
        self.failures.append(message)

    def require(self, condition: bool, pass_message: str, fail_message: str) -> None:
        if condition:
            self.pass_(pass_message)
        else:
            self.fail(fail_message)


def rel(path: str) -> Path:
    return ROOT / path


def load_runtime(result: CheckResult) -> dict[str, Any]:
    runtime_path = rel("config/runtime_status.json")
    try:
        data = json.loads(runtime_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        result.fail("config/runtime_status.json is missing")
        return {}
    except json.JSONDecodeError as exc:
        result.fail(f"config/runtime_status.json is invalid JSON: {exc}")
        return {}

    result.pass_("config/runtime_status.json is valid JSON")
    return data if isinstance(data, dict) else {}


def read_text_or_empty(path: str) -> str:
    file_path = rel(path)
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")


def check_required_files(result: CheckResult) -> None:
    for file_name in REQUIRED_FILES:
        result.require(
            rel(file_name).is_file(),
            f"required file exists: {file_name}",
            f"required file missing: {file_name}",
        )

    for packet_id in TASK_PACKETS:
        packet_path = rel(f"docs/backend-stage4-control-plane/task-packets/{packet_id}.yaml")
        result.require(
            packet_path.is_file(),
            f"task packet exists: {packet_id}",
            f"task packet missing: {packet_id}",
        )


def check_current_task(result: CheckResult, runtime: dict[str, Any]) -> None:
    current_task_path = rel("CURRENT_TASK")
    if not current_task_path.exists():
        result.fail("CURRENT_TASK is missing")
        return

    current_task = current_task_path.read_text(encoding="utf-8").strip()
    runtime_packet = str(runtime.get("current_packet", "")).strip()
    result.require(
        current_task == runtime_packet,
        "CURRENT_TASK matches runtime_status.current_packet",
        f"CURRENT_TASK ({current_task!r}) does not match runtime_status.current_packet ({runtime_packet!r})",
    )

    if runtime_packet:
        packet_path = rel(f"docs/backend-stage4-control-plane/task-packets/{runtime_packet}.yaml")
        result.require(
            packet_path.is_file(),
            f"current packet file exists: {runtime_packet}",
            f"current packet file missing: {runtime_packet}",
        )


def check_experiment_guard(result: CheckResult, runtime: dict[str, Any]) -> None:
    experiments_allowed = bool(runtime.get("experiments_allowed", False))
    if experiments_allowed:
        result.pass_("experiment and prototype paths are allowed by runtime status")
        return

    found = [path for path in FORBIDDEN_EXPERIMENT_PATHS if rel(path).exists()]
    result.require(
        not found,
        "no forbidden experiment or implementation paths exist while experiments_allowed is false",
        "forbidden experiment or implementation paths exist while experiments_allowed is false: "
        + ", ".join(found),
    )


def check_closed_gate_evidence(result: CheckResult, runtime: dict[str, Any]) -> None:
    evidence_text = read_text_or_empty("docs/backend-stage4-control-plane/05_evidence_log.md")
    gates = runtime.get("gates", {})
    if not isinstance(gates, dict):
        result.fail("runtime_status.gates must be an object")
        return

    closed_gate_count = 0
    for gate_name, gate_value in gates.items():
        if not isinstance(gate_value, dict):
            result.fail(f"gate {gate_name} must be an object")
            continue

        if gate_value.get("status") != "closed":
            continue

        closed_gate_count += 1
        evidence_ids = gate_value.get("evidence", [])
        has_evidence = isinstance(evidence_ids, list) and bool(evidence_ids)
        result.require(
            has_evidence,
            f"closed gate {gate_name} has evidence ids",
            f"closed gate {gate_name} has no evidence ids",
        )
        if not has_evidence:
            continue

        for evidence_id in evidence_ids:
            evidence_id_text = str(evidence_id)
            result.require(
                evidence_id_text in evidence_text,
                f"evidence id {evidence_id_text} is present in evidence log",
                f"evidence id {evidence_id_text} is missing from evidence log",
            )

    if closed_gate_count == 0:
        result.pass_("no closed gates require evidence yet")


def check_submission_gate(result: CheckResult, runtime: dict[str, Any]) -> None:
    gates = runtime.get("gates", {})
    submission_gate = gates.get("submission", {}) if isinstance(gates, dict) else {}
    if not isinstance(submission_gate, dict) or submission_gate.get("status") != "closed":
        result.pass_("submission gate is not closed; final submission checks are not required yet")
        return

    qa_text = read_text_or_empty("docs/backend-stage4-control-plane/07_qa_checklist.md")
    for item in SUBMISSION_REQUIRED_QA_ITEMS:
        result.require(
            item in qa_text,
            f"submission QA item complete: {item[6:]}",
            f"submission QA item is not complete: {item}",
        )

    draft_text = read_text_or_empty("drafts/insighta-labs-stage4-design.md")
    result.require(
        "## 1. Requirements" in draft_text
        and "## 2. Architecture" in draft_text
        and "## 3. Data Flow" in draft_text
        and "## 4. Design Decisions" in draft_text
        and "## 5. Trade-Offs And Limitations" in draft_text,
        "draft contains all required major sections",
        "draft is missing one or more required major sections",
    )

    traceability_text = read_text_or_empty("docs/backend-stage4-control-plane/01_brief_traceability.md")
    result.require(
        "Google Docs link" in traceability_text or "Google Docs" in traceability_text,
        "traceability references Google Docs submission proof",
        "traceability does not reference Google Docs submission proof",
    )

    result.require(
        rel("diagrams/source").is_dir() and rel("diagrams/exported").is_dir(),
        "diagram source and export directories exist",
        "diagram source or export directory is missing",
    )


def check_guardrail_language(result: CheckResult) -> None:
    draft_text = read_text_or_empty("drafts/insighta-labs-stage4-design.md").lower()
    forbidden_core_phrases = [
        "true natural language queries are supported",
        "llm-powered query engine",
        "multi-region active-active",
        "microservices architecture by default",
    ]
    found = [phrase for phrase in forbidden_core_phrases if phrase in draft_text]
    result.require(
        not found,
        "draft does not contain known unsupported core-design claims",
        "draft contains unsupported core-design claim(s): " + ", ".join(found),
    )


def main() -> int:
    result = CheckResult()
    check_required_files(result)
    runtime = load_runtime(result)
    check_current_task(result, runtime)
    check_experiment_guard(result, runtime)
    check_closed_gate_evidence(result, runtime)
    check_submission_gate(result, runtime)
    check_guardrail_language(result)

    if result.failures:
        print(f"\nControl-plane check failed: {len(result.failures)} issue(s).")
        return 1

    print("\nControl-plane check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
