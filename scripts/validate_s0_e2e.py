#!/usr/bin/env python3
"""Validate S0 cross-role E2E draft without pretending the tests have executed."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DRAFT="docs/contracts/r0-e2e-s0-draft.v1.json"
BANK="docs/contracts/r0-tdd-scenarios.v1.json"
ALLOCATION="docs/contracts/r0-scenario-allocation.v1.json"

def load(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))

def validate(plan,bank,allocation):
    errors=[]
    source=bank["crossRoleCases"]
    cases=plan.get("cases",[])
    if len(source)!=10 or len(cases)!=10 or [x.get("caseId") for x in cases]!=[x["id"] for x in source]:
        errors.append("all 10 canonical E2E IDs required in source order")
    if (plan.get("status")!="S0_E2E_GIVEN_WHEN_DRAFT" or
        plan.get("count")!=10 or plan.get("active")!=9 or plan.get("retired")!=1):
        errors.append("E2E draft may not claim approval or wrong counts")
    if plan.get("noPayments") is not True:
        errors.append("no-payments invariant missing")
    alloc={x["caseId"]:x for x in allocation["cases"]}
    for case,orig in zip(cases,source):
        cid=orig["id"]
        if case.get("caseId")!=cid:continue
        if case.get("canonicalJourney")!=orig.get("journey") or case.get("canonicalThen")!=orig.get("then"):
            errors.append(f"{cid}: canonical E2E journey/oracle modified")
        if case.get("stage")!="S0_DRAFT_NOT_APPROVED" or case.get("testExecution")!="NOT_WRITTEN" or case.get("reviewerEvidence") is not None:
            errors.append(f"{cid}: false Test Review or execution evidence")
        if cid=="TDD-R0-E2E-06":
            if not case.get("retired") or case.get("proposed") is not None:
                errors.append(f"{cid}: payment E2E must remain retired")
            if case.get("replacedBy")!=[f"PAY-ABS-{i:02d}" for i in range(1,7)]:
                errors.append(f"{cid}: payment absence replacement incomplete")
            continue
        if case.get("retired") is not False:
            errors.append(f"{cid}: active E2E incorrectly retired")
        proposal=case.get("proposed")
        if not isinstance(proposal,dict):
            errors.append(f"{cid}: missing proposed GWT")
            continue
        for key in ("actors","given","whenSteps","negativeVariants"):
            x=proposal.get(key)
            # Actor names such as 'receiver' are meaningful even when short.
            min_length = 3 if key == "actors" else 12
            if not isinstance(x,list) or len(x)<2 or any(not isinstance(v,str) or len(v.strip())<min_length for v in x):
                errors.append(f"{cid}: incomplete actor/precondition/action/failure {key}")
        expected=proposal.get("expected",{})
        if expected.get("canonicalThen")!=orig.get("then"):
            errors.append(f"{cid}: canonical result changed in draft")
        for key in ("http","db","events","ui"):
            if not isinstance(expected.get(key),str) or len(expected[key].strip())<20:
                errors.append(f"{cid}: missing specific {key} oracle")
        if proposal.get("pendingDecisionRefs")!=alloc[cid]["blockingPendingDecisionRefs"]:
            errors.append(f"{cid}: BR/DEC pending list must stay synchronized with S0 allocation")
    return errors

def main():
    problems=validate(load(DRAFT),load(BANK),load(ALLOCATION))
    if problems:
        for problem in problems:print("ERROR:",problem,file=sys.stderr)
        return 1
    print("PASS: 9 R0 E2E have proposed roles/preconditions/actions/negative variants and HTTP/DB/Outbox/UI oracles; payment E2E remains retired")
    print("WARNING: proposals require separate S0 and legal review; they are not executable E2E tests")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
