#!/usr/bin/env python3
"""CI contract verification for KERUENIX TDD Roadmap v1.4.

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



def audit_v14_pr_contract(road: dict, known_cases: set[str],
                          valid_permissions: dict[str, str],
                          known_br: set[str]) -> list[str]:
    """Check v1.4 PR risk claims; these are planned contracts, not executed tests."""
    issues: list[str] = []
    required_ui = {
        "PR-02", "PR-03C", "PR-03", "PR-04", "PR-05", "PR-06", "PR-07",
        "PR-10V", "PR-10", "PR-11", "PR-12", "PR-12C", "PR-13", "PR-14", "PR-15",
        "PR-16", "PR-16R", "PR-17", "PR-17S", "PR-18", "PR-19", "PR-20",
    }
    valid_modes = {
        "DOCUMENTATION_ONLY", "FOUNDATION_FAIL_CLOSED", "POLICY_SCOPED",
        "BLOCKED_UNTIL_BUSINESS_SIGNOFF", "BLOCKED_UNTIL_PERMISSION_APPROVED",
        "SAFE_DRAFT_ONLY", "FAIL_CLOSED_LEGAL_SIGNOFF", "PURE_DOMAIN_INPUT",
        "RELEASE_ACCEPTANCE", "RELEASE_SIGNOFF",
        "BLOCKED_UNTIL_OWNER_ADR_AND_RELATED_BR",
        "BLOCKED_UNTIL_BUSINESS_SIGNOFF_AND_VERIFIED_SOURCE",
    }
    cuts = {p["id"]: p for p in road["r0Prcuts"]}
    for pr in road["r0Prcuts"]:
        pid = pr["id"]
        gate = pr.get("activationGate") or {}
        if gate.get("mode") not in valid_modes:
            issues.append(f"{pid}: invalid or missing activationGate.mode")
        for br in gate.get("br", []):
            if br not in known_br:
                issues.append(f"{pid}: unknown activation business rule {br}")
        cases = pr.get("criticalCaseIds")
        if not isinstance(cases, list):
            issues.append(f"{pid}: missing criticalCaseIds list")
        else:
            if len(cases) != len(set(cases)):
                issues.append(f"{pid}: duplicate criticalCaseIds")
            for case_id in cases:
                if case_id not in known_cases:
                    issues.append(f"{pid}: unknown critical case {case_id}")
            if not cases and not pr.get("caseCoverageNote"):
                issues.append(f"{pid}: missing rationale for empty critical cases")
        ui = pr.get("uiAcceptance") or {}
        if pid in required_ui and ui.get("required") is not True:
            issues.append(f"{pid}: missing mandatory role-UI acceptance")
        if ui.get("required"):
            if not ui.get("deliverables"):
                issues.append(f"{pid}: required UI has no deliverable")
            if ui.get("requiredTest") != "ROLE_API_UI_AND_FAILURE_STATES":
                issues.append(f"{pid}: UI missing role/error-state test contract")
        if not pr.get("caseCoverageNote"):
            issues.append(f"{pid}: per-PR case applicability rationale missing")
    if cuts.get("PR-04", {}).get("activationGate", {}).get("mode") != "SAFE_DRAFT_ONLY":
        issues.append("PR-04 must be safe DRAFT only")
    if "DRAFT" not in cuts.get("PR-04", {}).get("outcome", ""):
        issues.append("PR-04 must explicitly limit write to DRAFT")
    if cuts.get("PR-05", {}).get("activationGate", {}).get("mode") != "BLOCKED_UNTIL_PERMISSION_APPROVED":
        issues.append("PR-05 submit must remain blocked until policy approval")
    permission_gate = road.get("authorizationGates", {})
    for key in ("rfqDraft", "rfqList", "rfqDetail", "providerInbox"):
        value = permission_gate.get(key) or {}
        if valid_permissions.get(value.get("catalogRef")) != value.get("permission"):
            issues.append(f"authorizationGates.{key}: unknown/mismatched policy ID")
    submit = permission_gate.get("rfqSubmit") or {}
    if submit.get("currentPolicy") != "NOT_GRANTED_BY_EXISTING_MATRIX" or submit.get("activation") != "DENY_UNTIL_OWNER_AND_SECURITY_ACCEPT":
        issues.append("RFQ submit policy unexpectedly enabled without explicit approval")
    owners = {x.get("resource"): x for x in road.get("domainOwnershipDecisions", [])}
    ca = owners.get("CustomerAccount", {})
    if (ca.get("canonicalWriter") != "commercial" or ca.get("otherOwner") != "tenancy"
            or ca.get("decision") != "PROPOSED_ADR_REQUIRED_BEFORE_PR_03C"):
        issues.append("CustomerAccount owner/grant split must remain explicitly proposed pending ADR")
    evidence = road.get("proofIntegrityProtocol") or {}
    if evidence.get("writeOwner") != "execution" or not evidence.get("storageTransactionRule") or len(evidence.get("required", [])) < 8:
        issues.append("Missing original POD/custody evidence and external object consistency protocol")
    settlement = road.get("financeSettlementGate") or {}
    if "SIMULATED" not in settlement.get("mockRule", "") or not settlement.get("withoutVerifiedProvider"):
        issues.append("Finance settlement gate permits false production PAID")
    if not road.get("tddExecutableSelection", {}).get("requiredManifestFields"):
        issues.append("Missing per-PR actual TDD applicability evidence schema")
    fleet = cuts.get("PR-10V", {})
    if (fleet.get("owner") != "fleet" or "PR-02" not in fleet.get("dependsOnPrs", [])
            or "NO capacity commitment" not in fleet.get("outcome", "")):
        issues.append("PR-10V Fleet registry must not imply a binding capacity hold")
    cancellation = cuts.get("PR-12C", {})
    if (cancellation.get("owner") != "booking"
            or cancellation.get("activationGate", {}).get("br") != ["BR-11"]
            or "NEG-R0-046" not in cancellation.get("criticalCaseIds", [])):
        issues.append("PR-12C cancellation requires BR-11, custody race and Booking ownership")
    review = cuts.get("PR-16R", {})
    if (review.get("owner") != "commercial"
            or "private" not in review.get("outcome", "").lower()
            or "NEG-R0-048" not in review.get("criticalCaseIds", [])
            or not review.get("uiAcceptance", {}).get("required")):
        issues.append("PR-16R must remain Commercial-owned, private, proof-verified feedback")
    e2e_deps = cuts.get("PR-19", {}).get("dependsOnPrs", [])
    if not {"PR-12C", "PR-16R"}.issubset(set(e2e_deps)):
        issues.append("PR-19 R0 E2E missing cancellation/review dependency")
    if cuts.get("PR-13", {}).get("dependsOnPrs") != ["PR-12"]:
        issues.append("PR-13 must not wait for optional cancellation BR")
    if cuts.get("PR-17", {}).get("dependsOnPrs") != ["PR-07"]:
        issues.append("PR-17 blanket-POD prerequisite blocks valid advance-invoice design")
    return issues


def audit_v14_markdown_pr_table(road: dict, main_doc: str) -> list[str]:
    """Compare rendered PR DAG table to the machine graph, not just ID presence."""
    issues: list[str] = []
    if "## 16. Executable delivery increments" not in main_doc or "## 17. Mandatory ownership" not in main_doc:
        return ["Roadmap Markdown missing PR table boundaries"]
    section = main_doc.split("## 16. Executable delivery increments", 1)[1].split(
        "## 17. Mandatory ownership", 1)[0]
    rows = {}
    for line in section.splitlines():
        if not re.match(r"^\|\s*"+ chr(96) + r"PR-\d{2}[A-Z]?" + chr(96), line):
            continue
        cols = [x.strip() for x in line.split("|")[1:-1]]
        if len(cols) < 5:
            issues.append("Malformed PR table row")
            continue
        pid, phase, owner, deps = [x.replace(chr(96), "") for x in cols[:4]]
        if pid in rows:
            issues.append(f"Duplicate Markdown PR {pid}")
        rows[pid] = {"phase": phase, "owner": owner,
                     "dependsOnPrs": re.findall(r"PR-\d{2}[A-Z]?", deps)}
    expected = {p["id"]: p for p in road["r0Prcuts"]}
    if set(rows) != set(expected):
        issues.append("Markdown PR IDs differ from JSON r0Prcuts")
    for pid in sorted(set(rows) & set(expected)):
        actual, planned = rows[pid], expected[pid]
        for field in ("phase", "owner"):
            if actual[field] != planned[field]:
                issues.append(f"{pid}: Markdown {field} differs from machine contract")
        if actual["dependsOnPrs"] != planned.get("dependsOnPrs", []):
            issues.append(f"{pid}: Markdown prerequisites differ from machine DAG")
    return issues


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

    check(road["schemaVersion"] == "1.4.0", "Roadmap schema version must be 1.4.0")
    check("v1.4" in main_doc[:400], "Roadmap Markdown version and JSON must match")
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
                    if pid != "RD-00":
                        check(set(p["br"]).issubset(approved),
                              f"{pid}: QUALIFIED with unapproved business decisions")
                if pid in {"RD-03", "RD-07", "RD-11", "RD-12"}:
                    check(bool(evidence.get("frontendE2eEvidence")),
                          f"{pid}: QUALIFIED without required frontendE2eEvidence")
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
    check(len(cuts) == 26, f"Expected 26 slices, got {len(cuts)}")
    check(pr_ids == ({f"PR-{i:02d}" for i in range(21)} | {"PR-03C", "PR-10V", "PR-12C", "PR-16R", "PR-17S"}), "PR IDs missing or reused")
    check(road["audit"]["findingsTotal"] == 27, "Expected 27 audited findings")
    pr_map = {pr["id"]: pr for pr in cuts}
    # New v1.4 R0 clarity contract: each decision must have a real owner, gate
    # and safe fallback. These are proposed decisions, NEVER approval evidence.
    delivery = load("docs/contracts/r0-delivery-contract.v1.json")
    check(delivery["schemaVersion"] == "1.0.0", "Delivery contract schema mismatch")
    decision_ids = unique(delivery["decisions"], "id", "R0 delivery decision")
    check(decision_ids == {f"DEC-R0-{i:02d}" for i in range(1, 9)},
          "Expected eight numbered and distinct R0 delivery decisions")
    check(road.get("r0Delivery", {}).get("decisionIds") == sorted(decision_ids),
          "Roadmap R0 decision references are missing or unordered")
    check(road.get("r0Delivery", {}).get("handbookRef") == delivery.get("handbook"),
          "R0 handbook reference differs from contract")
    check((ROOT / delivery["handbook"]).is_file(), "R0 handbook missing")
    for d in delivery["decisions"]:
        check(d["mustDecideBy"] in pr_ids, f"{d['id']}: unknown before-PR gate")
        check(bool(d.get("owner")) and bool(d.get("failSafe")) and bool(d.get("checks")),
              f"{d['id']}: missing owner/failSafe/acceptance checks")
        check(d["status"] != "APPROVED", f"{d['id']}: approval cannot be fabricated by documentation")
    check(all(new_id in pr_ids for new_id in ["PR-10V", "PR-12C", "PR-16R"]),
          "Three previously missing R0 PRs must have named gates")
    check("PR-10V" in pr_map["PR-10"]["dependsOnPrs"],
          "Capacity reservation must require qualified Fleet registry")
    check("PR-12C" in pr_map["PR-19"]["dependsOnPrs"] and
          "PR-16R" in pr_map["PR-19"]["dependsOnPrs"],
          "Full R0 E2E must cover cancellation and private review")
    check(pr_map["PR-13"]["dependsOnPrs"] == ["PR-12"],
          "Execution must not wait for unapproved cancellation BR")
    check(pr_map["PR-17"]["dependsOnPrs"] == ["PR-07"],
          "Invoice engine must not blanket-block permitted ADVANCE on POD")
    check(pr_map["PR-16R"]["owner"] == "commercial" and
          pr_map["PR-12C"]["owner"] == "booking" and
          pr_map["PR-10V"]["owner"] == "fleet",
          "New PR canonical write owners are inconsistent")
    for pr in cuts:
        for upstream in pr.get("dependsOnPrs", []):
            check(upstream in pr_ids, f"{pr['id']}: unknown PR dependency {upstream}")
            check(upstream != pr["id"], f"{pr['id']}: self dependency")

    seen_pr: set[str] = set()
    open_pr: set[str] = set()

    def visit_pr(pr_id: str) -> None:
        if pr_id in seen_pr:
            return
        if pr_id in open_pr:
            problems.append(f"PR dependency cycle at {pr_id}")
            return
        open_pr.add(pr_id)
        for ancestor in pr_map[pr_id].get("dependsOnPrs", []):
            if ancestor in pr_map:
                visit_pr(ancestor)
        open_pr.remove(pr_id)
        seen_pr.add(pr_id)

    for pr_id in pr_ids:
        visit_pr(pr_id)
    for pr in cuts:
        pid = pr["phase"]
        check(pid in phase_ids, f"{pr['id']}: unknown phase {pid}")
        if pid in phase_map:
            check(pr["id"] in phase_map[pid].get("deliveryPrs", []),
                  f"{pr['id']}: phase deliveryPrs mismatched")
        check(pr["owner"] in module_ids | {"platform", "architecture", "cross-functional", "release"},
              f"{pr['id']}: unrecognized owner {pr['owner']}")
        if pid in phase_map:
            check(pr["owner"] in phase_map[pid].get("primaryWriteOwners", []),
                  f"{pr['id']}: PR owner {pr['owner']} not a declared phase writer")
        check(pr["outcome"].strip() != "" and pr["testGate"].strip() != "",
              f"{pr['id']}: missing outcome/test gate")
        check(f"`{pr['id']}`" in main_doc, f"{pr['id']}: missing in Markdown cuts table")
    for phase in road["phases"]:
        for pr_id in phase["deliveryPrs"]:
            check(pr_id in pr_ids, f"{phase['id']}: unknown PR {pr_id}")
    # Verify that published Markdown PR table faithfully mirrors JSON dependencies,
    # not merely that every PR number appears somewhere in the document.
    pr_table = {}
    for line in main_doc.splitlines():
        if not line.startswith("| `PR-"):
            continue
        parts = [piece.strip() for piece in line.strip().split("|")[1:-1]]
        if len(parts) < 5:
            continue
        pr_id = parts[0].strip("`")
        if pr_id in pr_table:
            problems.append(f"Markdown duplicate PR table row {pr_id}")
        pr_table[pr_id] = parts
    check(set(pr_table) == pr_ids, "Markdown PR rows differ from JSON PR cuts")
    for pr in cuts:
        row = pr_table.get(pr["id"])
        if row:
            check(row[1].strip("`") == pr["phase"],
                  f"{pr['id']}: Markdown phase mismatch")
            check(row[2].strip("`") == pr["owner"],
                  f"{pr['id']}: Markdown owner mismatch")
            markdown_deps = set(re.findall(r"`(PR-[0-9]{2}[A-Z]?)`", row[3]))
            check(markdown_deps == set(pr.get("dependsOnPrs", [])),
                  f"{pr['id']}: Markdown dependency mismatch")
    # RD-00 records a truthful BR signoff backlog; it does not require every BR signed.
    if phase_map["RD-00"]["status"] == "QUALIFIED":
        check(bool(phase_map["RD-00"].get("evidence", {}).get("traceabilityReport")),
              "RD-00 QUALIFIED without proof of traceability report")


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
    # Critical cases must resolve to a real, stable test ID, never a guessed prefix.
    for pr in cuts:
        for case in pr.get("criticalCaseIds", []):
            check(case in full_case_ids, f"{pr['id']}: unknown critical TDD case {case}")
        check("criticalCaseIds" in pr, f"{pr['id']}: no criticalCaseIds/none justification")
        activation = pr.get("activationGate", {})
        check(bool(activation.get("mode")), f"{pr['id']}: no activation mode")
        check(bool(activation.get("effect")), f"{pr['id']}: no activation effect")
        for decision in activation.get("br", []):
            check(decision in br_ids, f"{pr['id']}: unknown activation BR {decision}")
        ui = pr.get("uiAcceptance", {})
        check(isinstance(ui.get("required"), bool), f"{pr['id']}: missing UI obligation")
        check(bool(ui.get("requiredTest")), f"{pr['id']}: UI test contract missing")
        if ui.get("required"):
            check(bool(ui.get("deliverables")), f"{pr['id']}: required UI deliverables absent")
        check(bool(pr.get("caseCoverageNote")) or pr["id"] in {"PR-00", "PR-01", "PR-08"},
              f"{pr['id']}: test case-selection rationale missing")

    problems.extend(audit_v14_pr_contract(
        road, full_case_ids, {e["id"]: e["permission"] for e in access["entries"]}, br_ids))
    problems.extend(audit_v14_markdown_pr_table(road, main_doc))
    for path in road["testBanks"]:
        check((ROOT / path).is_file(), f"Missing linked test source {path}")
    for item in road["r0Prcuts"]:
        check(item["phase"].startswith("RD-"), f"Unexpected R1/R2 PR in R0: {item['id']}")
    check(road["noAutoActivationOfExtensionModules"] is True,
          "R1/R2 modules must not auto-activate in R0")
    owners = {d["resource"]: d for d in road.get("domainOwnershipDecisions", [])}
    check(owners.get("CustomerAccount", {}).get("canonicalWriter") == "commercial",
          "CustomerAccount must have an explicit Commercial canonical writer proposal")
    check(pr_map["PR-03C"]["owner"] == "commercial" and
          "PR-03C" in pr_map["PR-03"]["dependsOnPrs"],
          "Tenancy grants must depend on canonical Commercial CustomerAccount")
    check("PR-17S" in pr_map["PR-18"]["dependsOnPrs"] and
          "PR-17S" in pr_map["PR-19"]["dependsOnPrs"],
          "Recovery/E2E depend on qualified verified settlement path")
    proof = road.get("proofIntegrityProtocol", {})
    check("EvidenceBlobGateway" in proof.get("immutableObjectOwner", ""),
          "Proof bytes must be verified through non-cyclic platform EvidenceBlobGateway")
    check(road["audit"]["findingsTotal"] ==
          len(re.findall(r"^\| `AUD-RD-[0-9]{2}` \|", (ROOT / "docs/34-tdd-roadmap-technical-audit.md").read_text(encoding="utf-8"), re.M)),
          "Audit Markdown rows must match the machine finding count")

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
