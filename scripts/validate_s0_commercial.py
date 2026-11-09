#!/usr/bin/env python3
"""S0 Commercial case-design contract guard (not Test Review or test execution)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DESIGN="docs/contracts/r0-s0-commercial-case-contracts.v1.json"
ALLOC="docs/contracts/r0-scenario-allocation.v1.json"
EXT="docs/contracts/r0-s0-extension-gwt.v1.json"
LEDGER="docs/contracts/r0-decision-readiness.v1.json"
REPORT="docs/52-s0-commercial-test-design-review.md"
SCOPE={"PR-04","PR-05","PR-06","PR-06S","PR-07","PR-11"}

def read_json(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def validate(plan,alloc,extension,ledger,report):
    errs=[]
    def fail(text):errs.append(text)
    core=[x for x in alloc["cases"] if not x["retired"] and x["primaryPr"] in SCOPE]
    cross=[x for x in alloc["cases"] if not x["retired"] and x["primaryPr"] not in SCOPE
           and SCOPE.intersection(x["impactedPrs"])]
    signatures=[x for x in extension["cases"] if x["kind"]=="SIGNATURE_CANDIDATE"]
    src=core+cross+signatures
    rows=plan.get("cases",[])
    names=[x.get("id") for x in rows]
    expected=[x.get("caseId") for x in src]
    if (len(core),len(cross),len(signatures),len(rows))!=(30,9,18,57) or names!=expected or len(set(names))!=57:
        fail("Commercial S0 must preserve exact 30 primary + 9 cross-PR + 18 SIG IDs")
    if plan.get("stage")!="S0_SCENARIO_DESIGN" or plan.get("status")!="PROPOSED_NOT_REVIEWED":
        fail("Commercial S0 cannot claim completed Test Review")
    if set(plan.get("scopePrs",[]))!=SCOPE:
        fail("Commercial PR scope changed")
    if plan.get("sourceAllocation")!=ALLOC or plan.get("sourceSignatures")!=EXT:
        fail("source contract path drift")
    rules=plan.get("rules",{})
    for name in ("noBusinessCodeThisStep","realSignatureAuthorityNotAssumed","quoteImmutable",
                 "carrierSelectionNotBooking","noPayments","allLegalBindingActionsFailClosedUntilSignoff","noFakeGreen"):
        if rules.get(name) is not True:fail("required Commercial safety rule missing: "+name)
    decisions={x["decisionId"]:x["readiness"] for x in ledger["decisions"]}
    all_refs=set()
    for idx,record in enumerate(src):
        x=rows[idx] if idx<len(rows) else {}
        key=record["caseId"]
        is_sign=idx>=39
        if is_sign:
            expected_canonical={k:record[k] for k in ("given","when","then")}
            owner=record["owner"]
            primary=record["ownerPr"]
            refs=[]
            impacted=["PR-06S"]
        else:
            expected_canonical={k:record["expected"]["canonical"+k.title()] for k in ("given","when","then")}
            owner=record["primaryOwner"]
            primary=record["primaryPr"]
            refs=record["blockingPendingDecisionRefs"]
            impacted=[p for p in record["impactedPrs"] if p in SCOPE]
        if x.get("canonical")!=expected_canonical:
            fail(f"{key}: canonical GWT modified")
        if x.get("canonicalPrimaryPr")!=primary or x.get("canonicalOwner")!=owner:
            fail(f"{key}: canonical owner reassigned")
        if x.get("commercialImpactedPrs")!=impacted:
            fail(f"{key}: commercial impacted PR links changed")
        if x.get("primaryCommercialScenario")!=(idx<30 or is_sign):
            fail(f"{key}: primary vs dependency case assignment invalid")
        draft=x.get("draft",{})
        if draft.get("pendingDecisionRefs")!=refs:
            fail(f"{key}: BR/DEC dependency changed")
        all_refs.update(refs)
        expected_activation=("DENY_HOLD_UNTIL_LEGAL_PROFILE_SIGNOFF" if is_sign else
                             "DENY_HOLD_UNTIL_BR_DEC_SIGNOFF" if refs else "SAFE_DESIGN_PROPOSAL")
        if draft.get("expectedActivation")!=expected_activation:
            fail(f"{key}: fail-closed activation changed")
        if is_sign and draft.get("additionalLegalGate")!="LEGAL_PROFILE_AND_SIGNER_AUTHORITY_PENDING":
            fail(f"{key}: signature profile is still legally gated")
        for prop in ("persistedOracle","sideEffectOracle","httpUiOracle","specificReviewPoint"):
            value=draft.get(prop)
            if not isinstance(value,str) or len(value.strip())<34:
                fail(f"{key}: missing concrete {prop}")
        if not isinstance(draft.get("proposedTestMethod"),str) or "#" not in draft["proposedTestMethod"]:
            fail(f"{key}: test-method candidate missing")
        if x.get("approval")!="DRAFT_NOT_REVIEWED" or x.get("execution")!="NOT_WRITTEN_IN_THIS_S0_PACKAGE":
            fail(f"{key}: false Test Review or executable test claim")
        if x.get("reviewAuthority") is not None or x.get("reviewEvidence") is not None:
            fail(f"{key}: reviewer signature/evidence fabricated")
    summary=plan.get("summary",{})
    if (summary.get("canonicalPrimary"),summary.get("canonicalImpacted"),
        summary.get("signatureCandidates"),summary.get("total"))!=(30,9,18,57):
        fail("Commercial summary counts changed")
    if set(summary.get("pendingDecisions",[]))!=all_refs:
        fail("pending decision coverage incomplete")
    if any(decisions.get(ref)!="PENDING" for ref in all_refs):
        fail("business decision readiness no longer matches source; manual review required")
    for token in ("PR-04","PR-05","PR-06S","PR-07","PR-11","QuoteVersion","SIG-01","BR-01","S0"):
        if token not in report:
            fail("Commercial review report misses "+token)
    return errs

def main():
    errors=validate(read_json(DESIGN),read_json(ALLOC),read_json(EXT),read_json(LEDGER),
                    (ROOT/REPORT).read_text(encoding="utf-8"))
    if errors:
        for e in errors:print("ERROR:",e,file=sys.stderr)
        return 1
    print("PASS: Commercial S0 30 primary + 9 cross-PR + 18 signature case designs; no false approval")
    print("WARNING: GWT/oracles are proposals, not signed BR/legal acceptance or executable S1 tests")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
