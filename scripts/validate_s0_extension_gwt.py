#!/usr/bin/env python3
"""Validate S0 extension GWT draft; never confuse case contracts with executed tests."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLAN="docs/contracts/r0-s0-extension-gwt.v1.json"
REGISTRY="docs/contracts/r0-scenario-first-test-plan.v1.json"
ROAD="docs/contracts/tdd-development-roadmap.v1.json"

def load(p):
    return json.loads((ROOT/p).read_text(encoding="utf-8"))

def validate(plan,registry,road):
    problems=[]
    prs={p["id"]:p for p in road["r0Prcuts"]}
    cases=plan.get("cases",[])
    ids=[c.get("caseId") for c in cases]
    source={c["id"] for c in registry["cases"]}
    sig=[f"SIG-{i:02d}" for i in range(1,19)]
    pay=[f"PAY-ABS-{i:02d}" for i in range(1,7)]
    cargo=[f"PR08-CARGO-{i:02d}" for i in range(1,7)]
    cost=[f"PR17-COST-{i:02d}" for i in range(1,5)]
    release=[f"PR20-REL-{i:02d}" for i in range(1,5)]
    gov=[f"PR00-GOV-{i:02d}" for i in range(1,3)]
    if ids!=sig+pay+cargo+cost+release+gov or len(set(ids))!=40:
        problems.append("S0 must contain 18 SIG + 6 PAY-ABS + 16 local GWT exactly")
    if not set(sig+pay).issubset(source) or set(cargo+cost+release+gov)&source:
        problems.append("candidate vs new local test source status changed")
    counts={"signature":18,"paymentAbsence":6,"cargo":6,
            "commercialCost":4,"release":4,"governance":2,"total":40}
    if plan.get("counts")!=counts:
        problems.append("GWT count or group partition changed")
    if plan.get("status")!="S0_EXTENSION_GWT_PROPOSED_NOT_APPROVED":
        problems.append("S0 extension may not claim review approval")
    if (plan.get("scope")!="NO_PAYMENTS" or plan.get("noTestExecution") is not True or
        plan.get("noLegalApproval") is not True or plan.get("sourceBankModification") is not False):
        problems.append("no-payments / no-false-execution invariants changed")
    for row in cases:
        cid=row.get("caseId","?")
        pid=row.get("ownerPr")
        if pid not in prs or row.get("owner")!=prs[pid]["owner"]:
            problems.append(f"{cid}: wrong canonical PR owner")
        if row.get("status")!="S0_GWT_DRAFT_NOT_REVIEWED" or row.get("testExecution")!="NOT_WRITTEN" or row.get("reviewerEvidence") is not None:
            problems.append(f"{cid}: cannot fake test completion or stakeholder review")
        for key in ("title","given","when","then","dbOracle","sideEffectOracle","httpUiOracle","fixture"):
            if not isinstance(row.get(key),str) or len(row[key].strip())<12:
                problems.append(f"{cid}: missing concrete {key} contract")
        if cid.startswith("SIG-") and (pid!="PR-06S" or row.get("legalDependency")!="LEGAL_PROFILE_AND_SIGNER_AUTHORITY_PENDING"):
            problems.append(f"{cid}: signature approval must remain legally gated")
        if cid.startswith("PAY-ABS-") and row.get("kind")!="NO_PAYMENT_ABSENCE":
            problems.append(f"{cid}: payment absence must never activate payment feature")
        if cid.startswith("PR08-") and pid!="PR-08":problems.append(f"{cid}: cargo ownership drift")
        if cid.startswith("PR17-") and pid!="PR-17":problems.append(f"{cid}: costing ownership drift")
        if cid.startswith("PR20-") and pid!="PR-20":problems.append(f"{cid}: release ownership drift")
        if cid.startswith("PR00-") and pid!="PR-00":problems.append(f"{cid}: governance ownership drift")
    return problems

def main():
    errors=validate(load(PLAN),load(REGISTRY),load(ROAD))
    if errors:
        for x in errors:print("ERROR:",x,file=sys.stderr)
        return 1
    print("PASS: 18 SIG + 6 PAY-ABS + 6 cargo + 4 commercial-cost + 4 release + 2 governance S0 contracts")
    print("NOTE: 24 candidate IDs already existed, 16 are new proposed local IDs; none are executable or approved tests")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
