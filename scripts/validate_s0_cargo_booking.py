#!/usr/bin/env python3
"""S0 Cargo/Compliance/Fleet/Booking design parity and fail-closed gate."""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PLAN="docs/contracts/r0-s0-cargo-fleet-booking-case-contracts.v1.json"
ALLOC="docs/contracts/r0-scenario-allocation.v1.json"
EXT="docs/contracts/r0-s0-extension-gwt.v1.json"
LEDGER="docs/contracts/r0-decision-readiness.v1.json"
REPORT="docs/53-s0-cargo-fleet-booking-test-design.md"
SCOPE={"PR-08","PR-09","PR-10V","PR-10","PR-12","PR-12C"}

def load(path):return json.loads((ROOT/path).read_text(encoding="utf-8"))

def validate(plan,alloc,ext,ledger,report):
    errors=[]
    def fail(msg):errors.append(msg)
    core=[x for x in alloc["cases"] if not x["retired"] and x["primaryPr"] in SCOPE]
    cross=[x for x in alloc["cases"] if not x["retired"] and x["primaryPr"] not in SCOPE and SCOPE.intersection(x["impactedPrs"])]
    cargo=[x for x in ext["cases"] if x["kind"]=="CARGO_LOCAL_GAP"]
    src=core+cross+cargo
    case_ids=[c.get("id") for c in plan.get("cases",[])]
    expected=[c["caseId"] for c in src]
    if (len(core),len(cross),len(cargo),len(case_ids))!=(27,4,6,37) or case_ids!=expected or len(set(case_ids))!=37:
        fail("S0 scope must exactly contain 27 primary + 4 impacted + 6 Cargo GWT")
    if plan.get("stage")!="S0_SCENARIO_DESIGN" or plan.get("reviewStatus")!="PROPOSED_NOT_REVIEWED":
        fail("S0 cannot claim reviewed or executed status")
    if set(plan.get("scopePrs",[]))!=SCOPE or plan.get("sourceAllocation")!=ALLOC or plan.get("sourceCargo")!=EXT:
        fail("canonical source paths or scope changed")
    for k in ("noDomainImplementation","unknownComplianceBlocks","noDoubleExclusiveCapacity",
              "ownFleetNotExternalCarrier","cancelDoesNotReleaseActiveCustody",
              "noBookingWithoutAcceptedCapacity","noPayments","legalDecisionsNotApprovedByCi"):
        if plan.get("guardrails",{}).get(k) is not True:
            fail(f"missing safety gate {k}")
    decisions={x["decisionId"]:x["readiness"] for x in ledger["decisions"]}
    encountered=set()
    for i,source in enumerate(src):
        cid=source["caseId"]
        row=plan["cases"][i] if i<len(plan.get("cases",[])) else {}
        is_cargo=i>=31
        if is_cargo:
            original={k:source[k] for k in ("given","when","then")}
            owner,primary=source["owner"],source["ownerPr"]
            affected=["PR-08"];refs=[]
        else:
            original={k:source["expected"]["canonical"+k.title()] for k in ("given","when","then")}
            owner,primary=source["primaryOwner"],source["primaryPr"]
            affected=[p for p in source["impactedPrs"] if p in SCOPE]
            refs=source["blockingPendingDecisionRefs"]
        if row.get("canonical")!=original:
            fail(f"{cid}: canonical GWT changed")
        if row.get("originalPrimaryPr")!=primary or row.get("originalOwner")!=owner:
            fail(f"{cid}: original data owner rewritten")
        if row.get("applicablePrs")!=affected or row.get("thisBatchPrimary")!=(i<27 or is_cargo):
            fail(f"{cid}: cross-PR scope or primary/impacted ownership changed")
        draft=row.get("proposed",{})
        if draft.get("pendingDecisionRefs")!=refs:
            fail(f"{cid}: canonical BR/DEC blockers hidden")
        encountered.update(refs)
        if draft.get("activation")!=("DENY_HOLD_UNTIL_BR_DEC" if refs else "PROPOSED_TECH_CONTRACT"):
            fail(f"{cid}: unauthorized positive activation")
        for key in ("dbOracle","eventOracle","uiOracle","mandatoryNegativeCheck"):
            value=draft.get(key)
            if not isinstance(value,str) or len(value.strip())<30:
                fail(f"{cid}: missing concrete {key}")
        if not isinstance(draft.get("plannedTestMethod"),str) or "#" not in draft["plannedTestMethod"]:
            fail(f"{cid}: executable test candidate missing")
        if row.get("reviewStatus")!="DRAFT_NOT_APPROVED" or row.get("executionStatus")!="NOT_WRITTEN_BY_THIS_DESIGN":
            fail(f"{cid}: false Test Review or executable test claim")
        if row.get("reviewerEvidence") is not None:
            fail(f"{cid}: fabricated reviewer authority")
    summary=plan.get("summary",{})
    if tuple(summary.get(k) for k in ("primary","impacted","cargoLocal","total"))!=(27,4,6,37):
        fail("incorrect counts in S0 summary")
    if set(summary.get("pendingDecisions",[]))!=encountered:
        fail("pending decision summary does not match case dependencies")
    if any(decisions.get(ref)!="PENDING" for ref in encountered):
        fail("stakeholder decision changed; design requires re-review")
    for phrase in ("PR-08","PR-09","PR-10V","PR-10","PR-12","PR-12C","UNKNOWN","BR-07","S0"):
        if phrase not in report:fail("review report missing "+phrase)
    return errors

def main():
    errors=validate(load(PLAN),load(ALLOC),load(EXT),load(LEDGER),(ROOT/REPORT).read_text(encoding="utf-8"))
    if errors:
        for e in errors:print("ERROR:",e,file=sys.stderr)
        return 1
    print("PASS: S0 27 Cargo/Fleet/Compliance/Booking primary + 4 cross-owner E2E + 6 Cargo GWT, no false approval")
    print("WARNING: this is scenario design, not executable tests or business/legal Test Review")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
