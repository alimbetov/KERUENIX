#!/usr/bin/env python3
"""Guard the Scenario-First R0 inventory; validating JSON is NOT executing tests."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLAN="docs/contracts/r0-scenario-first-test-plan.v1.json"
BASE="docs/contracts/r0-tdd-scenarios.v1.json"
NEG="docs/contracts/r0-negative-scenarios.v1.json"
ROAD="docs/contracts/tdd-development-roadmap.v1.json"
FOUND="docs/36-r0-tdd-start-pack.md"
DOC="docs/46-r0-scenario-first-tdd-standard.md"
ORDER=["SCENARIO_DESIGN","TEST_FIRST","TEST_REVIEW","IMPLEMENTATION",
       "REFACTORING_AND_QUALIFICATION"]

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def validate(p,b,n,r,f,doc):
    problems=[]
    source=b["blockerCases"]+b["r0SafetyCases"]+b["crossRoleCases"]+n["cases"]
    ids=[x["id"] for x in source]
    found=re.findall(r"^\| `(FOUND-\d{2})` \|",f,flags=re.M)
    candidates=[f"SIG-{i:02}" for i in range(1,19)]+[f"PAY-ABS-{i:02}" for i in range(1,7)]
    required=ids+found+candidates
    if len(ids)!=132 or len(set(ids))!=132 or len(found)!=12:
        problems.append("canonical source inventory changed")
    actual=[x.get("id") for x in p.get("cases",[])]
    if actual!=required or len(set(actual))!=168:
        problems.append("inventory must match 132 R0 + 12 FOUND + 24 candidates exactly")
    if p.get("sourceCounts")!={"blocker":60,"safety":14,"e2e":10,"negative":48,
                              "found":12,"signatureCandidates":18,
                              "noPaymentCandidates":6,"total":168}:
        problems.append("case counts changed")
    if p.get("fiveStages")!=ORDER:
        problems.append("five-stage order changed")
    if p.get("status")!="S0_DRAFT_NOT_REVIEWED":
        problems.append("unreviewed inventory must not claim completion")
    for rule in ("testBeforeNewDomainCode","reviewBeforeDomainImplementation",
                 "realBehaviorRedNotCompileError","noTestWeakenForGreen",
                 "noLegalSignoffFromCI","noFalseGreen","noSilentSkip","noPayments"):
        if p.get("mandatoryRules",{}).get(rule) is not True:
            problems.append(f"missing mandatory rule {rule}")
    retired=set(r["testSelection"]["r0OutOfScopeHistory"]["caseIds"])
    if len(retired)!=11 or not retired.issubset(set(ids)):
        problems.append("canonical retired payment cases changed")
    refs={}
    for pr in r["r0Prcuts"]:
        for cid in pr["criticalCaseIds"]:
            refs.setdefault(cid,[]).append(pr["id"])
    by_id={x.get("id"):x for x in p.get("cases",[])}
    for original in source:
        cid=original["id"];row=by_id.get(cid)
        if not row:continue
        for prop,key in (("given","given"),("when","when"),("then","then"),
                         ("journey","journey"),("persistentOracle","persistentAssertions"),
                         ("sideEffectOracle","sideEffectAssertions"),
                         ("userVisibleOracle","userVisibleOutcome")):
            if row.get(prop)!=original.get(key):
                problems.append(f"{cid}: canonical {prop} oracle changed without review")
        if row.get("linkedPrs")!=refs.get(cid,[]):
            problems.append(f"{cid}: roadmap critical PR links changed")
        if row.get("designStatus")!="SOURCE_SPEC_ONLY":
            problems.append(f"{cid}: draft falsely claims designed/reviewed")
        if cid in retired:
            if row.get("applicability")!="RETIRED_NO_PAYMENTS" or row.get("executionStatus")!="RETIRED":
                problems.append(f"{cid}: out-of-scope payment test reactivated")
        elif row.get("executionStatus")!="NOT_WRITTEN":
            problems.append(f"{cid}: unexecuted case falsely promoted")
    for cid in found:
        row=by_id.get(cid)
        if row and (row.get("linkedPrs")!=["PR-01"]
                or row.get("executionStatus")!="PARTIAL_PRIOR_TEST_EVIDENCE_NOT_FULL_QUALIFICATION"):
            problems.append(f"{cid}: foundation evidence/ownership changed")
    for cid in candidates:
        row=by_id.get(cid)
        if row and (row.get("designStatus")!="DETAIL_MISSING" or
                    row.get("executionStatus")!="NOT_WRITTEN"):
            problems.append(f"{cid}: candidate incorrectly classified as executed")
    for row in p.get("cases",[]):
        cid=row.get("id","?")
        if row.get("evidence") is not None or row.get("reviewerAuthority") is not None:
            problems.append(f"{cid}: no fabricated technical/legal evidence in S0")
        if row.get("executionStatus") in ("PASS","GREEN","QUALIFIED","EXECUTED"):
            problems.append(f"{cid}: green claim requires real executable evidence")
    for name in ("Scenario Design","Test-First","Test Review",
                 "Implementation","Refactoring & Qualification"):
        if name not in doc:problems.append("standard missing "+name)
    return problems

def main():
    err=validate(load(PLAN),load(BASE),load(NEG),load(ROAD),
                 (ROOT/FOUND).read_text(encoding="utf-8"),
                 (ROOT/DOC).read_text(encoding="utf-8"))
    if err:
        for e in err:print("ERROR:",e,file=sys.stderr)
        return 1
    print("PASS: R0 132 + FOUND 12 + candidates 24 = 168 IDs; 5 ordered test-first stages; no false test qualification")
    print("WARNING: scenario inventory is S0 DRAFT; no assertion of 168 executable tests")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
