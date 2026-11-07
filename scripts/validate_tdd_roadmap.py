#!/usr/bin/env python3
"""CI contract verification for KERUENIX TDD Roadmap v1.1.

Standard library only; checks documentary consistency, NOT executable-domain
qualification or real stakeholder signoff.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/contracts/tdd-development-roadmap.v1.json"


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def main() -> int:
    problems: list[str] = []
    road = load("docs/contracts/tdd-development-roadmap.v1.json")
    modules = load("docs/contracts/module-boundaries.v1.json")
    br = load("docs/contracts/r0-blocker-decisions.v1.json")
    base_tests = load("docs/contracts/r0-tdd-scenarios.v1.json")
    neg_tests = load("docs/contracts/r0-negative-scenarios.v1.json")
    sdb = load("docs/contracts/backend-query-soft-delete.v1.json")
    access = load("docs/contracts/access-policy-matrix.v2.json")
    bsc_text = (ROOT / "docs/25-business-scenario-book.md").read_text(encoding="utf-8")
    main_doc = (ROOT / road["roadmapRef"]).read_text(encoding="utf-8")

    def check(condition: bool, message: str) -> None:
        if not condition:
            problems.append(message)

    def unique(records: list[dict], attr: str, label: str) -> set[str]:
        values = [item[attr] for item in records]
        check(len(values) == len(set(values)), f"Duplicate {label} ID")
        return set(values)

    check(road["schemaVersion"] == "1.1.0", "Roadmap schema version must be 1.1.0")
    check("v1.1" in main_doc[:400], "Roadmap Markdown version and JSON must match")
    module_ids = unique(modules["modules"], "id", "business module")
    check(len(module_ids) == 17, f"Expected 17 business module IDs, got {len(module_ids)}")
    phase_ids = unique(road["phases"], "id", "phase")
    check(all(f"RD-{i:02d}" in phase_ids for i in range(13)), "Missing required RD-00..RD-12")
    check(all(f"RX-{i:02d}" in phase_ids for i in range(1, 4)), "Missing RX-01..03")
    phase_map = {p["id"]: p for p in road["phases"]}
    bsc_ids = set(re.findall(r"^## (BSC-\d{3}) — ", bsc_text, re.MULTILINE))
    br_ids = unique(br["decisions"], "decisionId", "BR decision")
    check(len(br_ids) == 12, "Expected exactly twelve existing blocking BR decisions")
    # Real approvals may arrive later: permit promotion ONLY with evidence, not
    # by rewriting a status string in the contract.
    accepted_br_states = {"PENDING_REAL_STAKEHOLDER", "BUSINESS_APPROVED", "REJECTED", "REVISED"}
    for decision in br["decisions"]:
        state = decision["businessApproval"]
        check(state in accepted_br_states,
              f"{decision['decisionId']}: unrecognized business approval status {state}")
        if state == "BUSINESS_APPROVED":
            check(bool(decision.get("approvalEvidenceRef")),
                  f"{decision['decisionId']}: approved without approvalEvidenceRef")
            check(bool(decision.get("approverAuthorityRef")),
                  f"{decision['decisionId']}: approved without approverAuthorityRef")

    for p in road["phases"]:
        pid = p["id"]
        for dep in p["dependsOn"]:
            check(dep in phase_ids, f"{pid}: unknown dependency {dep}")
            check(dep != pid, f"{pid}: self dependency")
        for module_id in p["modules"]:
            check(module_id in module_ids, f"{pid}: unknown business module {module_id}")
        for owner in p.get("primaryWriteOwners", []):
            check(owner in module_ids | {"platform", "architecture", "business analysts", "cross-functional", "release"},
                  f"{pid}: unrecognized ownership label {owner}")
        for scenario in p.get("bsc", []):
            check(scenario in bsc_ids, f"{pid}: unknown BSC scenario {scenario}")
        for decision in p.get("br", []):
            check(decision in br_ids, f"{pid}: unknown BR decision {decision}")
        allowed_phase_states = {"PLANNED_NOT_QUALIFIED", "DESIGNED", "RED", "GREEN", "QUALIFIED"}
        check(p["status"] in allowed_phase_states,
              f"{pid}: unrecognized phase status {p['status']}")
        if p["status"] in {"GREEN", "QUALIFIED"}:
            evidence = p.get("evidence", {})
            for field in ("commitSha", "ciRunUrl", "testReportPath"):
                check(bool(evidence.get(field)),
                      f"{pid}: {p['status']} without {field}")
            check(p.get("testExecutionStatus") == "EXECUTED_VERIFIED",
                  f"{pid}: {p['status']} requires verified test execution")
            if p["status"] == "QUALIFIED":
                if pid != "RD-00":
                    for field in ("migrationVersion", "securityTestRefs"):
                        check(bool(evidence.get(field)),
                              f"{pid}: QUALIFIED without {field}")
                if p.get("br"):
                    check(bool(evidence.get("businessDecisionRefs")),
                          f"{pid}: QUALIFIED without applicable businessDecisionRefs")
                    approved = {d["decisionId"] for d in br["decisions"]
                                if d["businessApproval"] == "BUSINESS_APPROVED"}
                    check(set(p["br"]).issubset(approved),
                          f"{pid}: QUALIFIED with unapproved business decisions")
                if pid in {"RD-11", "RD-12"}:
                    check(bool(evidence.get("frontendE2eEvidence")),
                          f"{pid}: QUALIFIED without frontendE2eEvidence")
        elif p["status"] == "PLANNED_NOT_QUALIFIED":
            check(p.get("testExecutionStatus") == "NOT_RUN_THIS_ROADMAP",
                  f"{pid}: planned phase inaccurately claims tests were run")
        check(f"### {pid} —" in main_doc, f"{pid}: missing Markdown phase passport")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            problems.append(f"Phase DAG has a cycle at {node}")
            return
        visiting.add(node)
        for dep in phase_map[node]["dependsOn"]:
            if dep in phase_map:
                visit(dep)
        visiting.remove(node)
        visited.add(node)

    for phase in phase_ids:
        visit(phase)
    check(set(road["blockedUntilSignoff"]) == br_ids,
          "Blocked-until-signoff catalog differs from 12 BR decisions")
    if road["currentVerifiedState"]["latestHeadR0Qualified"]:
        release = road.get("releaseQualification", {})
        for field in ("commitSha", "builtArtifactDigest", "ciRunUrl",
                      "businessApprovalRefs", "migrationVersion",
                      "postgresRlsEvidence", "restorationEvidence", "frontendE2eEvidence"):
            check(bool(release.get(field)),
                  f"R0 release promoted without {field}")
        check(phase_map["RD-12"]["status"] == "QUALIFIED",
              "R0 release requires qualified RD-12")
    if road["currentVerifiedState"]["domainCodeQualified"]:
        check(any(p["status"] == "QUALIFIED" and p["id"] in {"RD-02","RD-03","RD-04","RD-05"}
                  for p in road["phases"]),
              "Domain code qualified without any implemented, evidence-backed domain phase")

    cuts = road["r0Prcuts"]
    pr_ids = unique(cuts, "id", "PR cut")
    check(len(cuts) == 21, f"Expected 21 slices, got {len(cuts)}")
    check(pr_ids == {f"PR-{i:02d}" for i in range(21)}, "PR IDs missing or reused")
    for pr in cuts:
        pid = pr["phase"]
        check(pid in phase_ids, f"{pr['id']}: unknown phase {pid}")
        if pid in phase_map:
            check(pr["id"] in phase_map[pid].get("deliveryPrs", []),
                  f"{pr['id']}: phase deliveryPrs mismatched")
        check(pr["owner"] in module_ids | {"platform", "architecture", "cross-functional", "release"},
              f"{pr['id']}: unrecognized owner {pr['owner']}")
        check(pr["outcome"].strip() != "" and pr["testGate"].strip() != "",
              f"{pr['id']}: missing outcome/test gate")
        check(f"`{pr['id']}`" in main_doc, f"{pr['id']}: missing in Markdown cuts table")
    for phase in road["phases"]:
        for pr_id in phase["deliveryPrs"]:
            check(pr_id in pr_ids, f"{phase['id']}: unknown PR {pr_id}")

    inf_ids = unique(road["earlyInfrastructure"], "id", "foundation infrastructure item")
    check(len(inf_ids) == 5, "Foundation should record five minimum infrastructure contracts")
    check(phase_map["RD-01"]["modules"] == [], "Platform baseline must not pretend to be Tenancy module")
    check(any("outbox" in x["contract"].lower() for x in road["earlyInfrastructure"]),
          "No early Outbox/Inbox infrastructure contract")
    check("RD-10" in phase_ids and "hardening" in phase_map["RD-10"]["scope"].lower(),
          "RD-10 should harden existing jobs, not first introduce them")

    counts = road["testSelection"]["knownCounts"]
    check(len(base_tests["blockerCases"]) == counts["blocker"], "Blocker test count drift")
    check(len(base_tests["r0SafetyCases"]) == counts["safety"], "R0 safety count drift")
    check(len(base_tests["crossRoleCases"]) == counts["e2e"], "E2E count drift")
    check(len(neg_tests["cases"]) == counts["negative"], "Negative test count drift")
    check(sum(counts[k] for k in ("blocker", "safety", "e2e", "negative")) ==
          counts["individualPlanned"], "Total individual test specs drift")
    check(len(sdb["plannedAcceptance"]) == counts["backendAnchors"], "SDB anchor count drift")
    check(len(access["entries"]) == 67, "Baseline draft permission catalog drift — review explicitly")

    full_case_ids = unique(
        base_tests["blockerCases"] + base_tests["r0SafetyCases"] +
        base_tests["crossRoleCases"] + neg_tests["cases"], "id", "test case")
    check(len(full_case_ids) == counts["individualPlanned"],
          "Planned test case identity total drift")
    for path in road["testBanks"]:
        check((ROOT / path).is_file(), f"Missing linked test source {path}")
    for item in road["r0Prcuts"]:
        check(item["phase"].startswith("RD-"), f"Unexpected R1/R2 PR in R0: {item['id']}")
    check(road["noAutoActivationOfExtensionModules"] is True,
          "R1/R2 modules must not auto-activate in R0")

    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        print(f"FAILED: {len(problems)} roadmap contract checks", file=sys.stderr)
        return 1
    print(f"PASS: {len(road['phases'])} phases, {len(cuts)} PR cuts, "
          f"{len(module_ids)} business modules, {len(br_ids)} BR, "
          f"{len(full_case_ids)} candidate tests, {len(inf_ids)} early infrastructure contracts")
    print("NOTE: contract validation is NOT a Java build, domain TDD run or business signoff.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
