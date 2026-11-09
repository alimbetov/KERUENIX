#!/usr/bin/env python3
"""S0 Platform/Tenancy case design integrity; never marks a test or business decision approved."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DESIGN="docs/contracts/r0-s0-platform-tenancy-case-contracts.v1.json"
ALLOC="docs/contracts/r0-scenario-allocation.v1.json"
REGISTRY="docs/contracts/r0-scenario-first-test-plan.v1.json"
LEDGER="docs/contracts/r0-decision-readiness.v1.json"
REPORT="docs/51-s0-platform-tenancy-test-design-review.md"
SCOPE={"PR-01","PR-02","PR-03C","PR-03"}

def read_json(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def validate(plan,alloc,registry,ledger,report):
    err=[]
    def fail(s):err.append(s)
    fnd=[x for x in registry["cases"] if x["group"]=="FOUNDATION"]
    active=[x for x in alloc["cases"] if not x["retired"] and (
        x["primaryPr"] in SCOPE or SCOPE.intersection(x["impactedPrs"]))]
    expected=[x["id"] for x in fnd]+[x["caseId"] for x in active]
    cases=plan.get("caseContracts",[])
    ids=[x.get("id") for x in cases]
    if len(fnd)!=12 or len(active)!=20 or len(cases)!=32 or ids!=expected or len(set(ids))!=32:
        fail("scope requires 12 FOUND + 20 active canonical scenarios, exact IDs/order")
    if plan.get("stage")!="S0_SCENARIO_DESIGN" or plan.get("reviewStatus")!="PROPOSED_NOT_REVIEWED":
        fail("review status cannot imply completed Test Review")
    if plan.get("summary",{}).get("caseIds")!=expected or plan.get("summary",{}).get("cases")!=32:
        fail("summary case coverage drift")
    if set(plan.get("summary",{}).get("scopePrs",[]))!=SCOPE:
        fail("scope must cover PR-01, PR-02, PR-03C, PR-03")
    if plan.get("sourceAllocation")!=ALLOC or plan.get("sourceFoundation")!=REGISTRY:
        fail("canonical source references changed")
    rules=plan.get("invariants",{})
    for k in ("productionDenyAll","noPayments","tenantRlsInsufficientForCustomerScope",
              "customerAccountSingleWriterProposedPendingAdr","revokeRequiresNewAuthDenial",
              "technicalCiCannotApproveBusinessRules"):
        if rules.get(k) is not True:fail(f"missing safety invariant {k}")
    if plan.get("fixtureContract",{}).get("privacy")!="synthetic-only":
        fail("test fixture may not use real personal data")
    dec={x["decisionId"]:x for x in ledger["decisions"]}
    allocations={x["caseId"]:x for x in active}
    found={x["id"]:x for x in fnd}
    accumulated=set()
    for row in cases:
        cid=row.get("id","?")
        if cid not in expected:continue
        original=found.get(cid)
        if original:
            if row.get("primaryPr")!="PR-01":
                fail(f"{cid}: foundation primary PR must be PR-01")
            expected_canon={k:original.get(k) for k in ("given","when","then")}
            expected_refs=[]
            expected_impacted=["PR-01"]
        else:
            src=allocations[cid]
            if row.get("primaryPr")!=src["primaryPr"] or row.get("primaryOwner")!=src["primaryOwner"]:
                fail(f"{cid}: primary owner differs from canonical allocation")
            expected_canon={"given":src["expected"]["canonicalGiven"],
                            "when":src["expected"]["canonicalWhen"],
                            "then":src["expected"]["canonicalThen"]}
            expected_refs=src["blockingPendingDecisionRefs"]
            expected_impacted=src["impactedPrs"]
        if row.get("canonical")!=expected_canon:
            fail(f"{cid}: canonical GWT modified")
        if row.get("impactedPrs")!=expected_impacted:
            fail(f"{cid}: original impacted PR coverage changed")
        proposal=row.get("proposed",{})
        if proposal.get("legalOrBusinessGates")!=expected_refs:
            fail(f"{cid}: pending BR/DEC gates changed")
        accumulated.update(expected_refs)
        if proposal.get("activation")!=("DENY_OR_HOLD_UNTIL_SIGNOFF" if expected_refs else "TECHNICAL_FAIL_CLOSED_PROPOSAL"):
            fail(f"{cid}: fail-closed pending activation mismatch")
        for key in ("persistent","outboxInbox","httpUi"):
            val=proposal.get("assertions",{}).get(key)
            if not isinstance(val,str) or len(val.strip())<36:
                fail(f"{cid}: missing concrete {key} oracle")
        if not isinstance(proposal.get("testMethodCandidate"),str) or "#" not in proposal["testMethodCandidate"]:
            fail(f"{cid}: executable test method candidate missing")
        if row.get("evidenceStatus")!="NOT_EXECUTED_BY_S0" or row.get("s0Status")!="PROPOSED_PENDING_TECH_REVIEW":
            fail(f"{cid}: S0 draft cannot claim tests executed or approved")
        if row.get("reviewerAuthority") is not None or row.get("reviewRef") is not None:
            fail(f"{cid}: no fabricated reviewer authority")
        if row.get("primaryPr")=="PR-03C" and not any(
                "Commercial" in v and "DEC-R0-02" in v for v in proposal.get("caveats",[])):
            fail(f"{cid}: Commercial canonical CustomerAccount owner remains proposed")
        if cid in ("FOUND-08","NEG-R0-005","TDD-SIM-05-G03-05") and not any(
                "tenant-only RLS" in v for v in proposal.get("caveats",[])):
            fail(f"{cid}: customer X/Y requires additional account scope")
        if cid in ("NEG-R0-006","TDD-R0-E2E-09") and not any(
                "signed URL" in v for v in proposal.get("caveats",[])):
            fail(f"{cid}: cannot invent immediate signed URL revoke")
    if set(plan.get("summary",{}).get("pendingDecisionRefs",[]))!=accumulated:
        fail("pending decision summary incomplete")
    if any(dec.get(x,{}).get("readiness")!="PENDING" for x in accumulated):
        fail("decision readiness changed; review and update design before accepting")
    if not all(x in report for x in ["FOUND-01","FOUND-12","BR-03","DEC-R0-02","CustomerAccount","S0"]):
        fail("S0 review report incomplete")
    return err

def main():
    errors=validate(read_json(DESIGN),read_json(ALLOC),read_json(REGISTRY),
                    read_json(LEDGER),(ROOT/REPORT).read_text(encoding="utf-8"))
    if errors:
        for e in errors:print("ERROR:",e,file=sys.stderr)
        return 1
    print("PASS: 12 FOUND + 20 scoped R0, 32 proposed multi-layer case designs, reviewed-source parity and BR/DEC fail-closed")
    print("WARNING: this proves document consistency only, no real Test Review or executable S1 evidence")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
