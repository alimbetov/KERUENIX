#!/usr/bin/env python3
"""Validate S0 allocation draft. This does not qualify scenarios, tests or business decisions."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MATRIX="docs/contracts/r0-scenario-allocation.v1.json"
BANK="docs/contracts/r0-tdd-scenarios.v1.json"
NEGATIVE="docs/contracts/r0-negative-scenarios.v1.json"
ROADMAP="docs/contracts/tdd-development-roadmap.v1.json"
LEDGER="docs/contracts/r0-decision-readiness.v1.json"

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def validate(matrix, bank, negatives, roadmap, ledger):
    errors=[]
    def fail(s):errors.append(s)
    source={}
    for group, rows in (("BLOCKER",bank["blockerCases"]),
                        ("SAFETY",bank["r0SafetyCases"]),
                        ("E2E",bank["crossRoleCases"]),
                        ("NEGATIVE",negatives["cases"])):
        for row in rows:
            if row["id"] in source:fail("duplicate canonical case ID")
            source[row["id"]]=(group,row)
    prs={p["id"]:p for p in roadmap["r0Prcuts"]}
    decisions={d["decisionId"]:d for d in ledger["decisions"]}
    retired=set(roadmap["testSelection"]["r0OutOfScopeHistory"]["caseIds"])
    cases=matrix.get("cases",[])
    ids=[r.get("caseId") for r in cases]
    active=[r for r in cases if not r.get("retired")]
    if len(source)!=132 or len(cases)!=132 or set(ids)!=set(source) or len(set(ids))!=132:
        fail("132 canonical scenario IDs must be unique and complete")
    if len(active)!=121 or len(retired)!=11:
        fail("121 active and 11 retired payment scenarios required")
    if len(prs)!=26 or len(matrix.get("prMatrix",[]))!=26:
        fail("26 PR allocations required")
    if matrix.get("status")!="S0_ALLOCATION_PROPOSED_NOT_REVIEWED":
        fail("S0 cannot assert review approval without evidence")
    if matrix.get("sourceRegistry")!="docs/contracts/r0-scenario-first-test-plan.v1.json":
        fail("scenario-first registry source changed")
    if matrix.get("scope")!="NO PAYMENTS / no AR-AP / no SETTLED/PAID; retired payment cases cannot be revived":
        fail("NO PAYMENTS scope cannot change")
    grouped={"BLOCKER":0,"SAFETY":0,"E2E":0,"NEGATIVE":0}
    expected_by_pr={p:[] for p in prs}
    primary_by_pr={p:[] for p in prs}
    for row in cases:
        cid=row.get("caseId","?")
        if cid not in source:continue
        group,canonical=source[cid]
        grouped[group]+=1
        if row.get("group")!=group:
            fail(f"{cid}: group differs from canonical source")
        if row.get("retired")!=(cid in retired):
            fail(f"{cid}: payment/out-of-scope disposition changed")
        if row.get("reviewStatus")!="NOT_REVIEWED" or row.get("reviewer") is not None or row.get("reviewEvidence") is not None:
            fail(f"{cid}: S0 cannot fabricate reviewer signoff")
        observed=row.get("expected",{})
        for key,src in (("canonicalGiven","given"),
                        ("canonicalWhen","when"),
                        ("canonicalThen","then")):
            if observed.get(key)!=canonical.get(src):
                fail(f"{cid}: canonical GWT oracle changed")
        for prop in ("dbOracle","outboxOracle","httpUiOracle"):
            if not isinstance(observed.get(prop),str) or not observed[prop].strip():
                fail(f"{cid}: {prop} missing")
        missing=[k for k in ("given","when","then") if not canonical.get(k)]
        if cid not in retired and row.get("gwtMissing")!=missing:
            fail(f"{cid}: missing-GWT status not accurate")
        if cid in retired:
            if row.get("primaryPr") is not None or row.get("impactedPrs")!=[] or row.get("assignedStatus")!="RETIRED_SCOPE_EXCLUSION" or observed.get("oracleStatus")!="RETIRED":
                fail(f"{cid}: retired payment case reactivated")
            continue
        pid=row.get("primaryPr")
        if pid not in prs:
            fail(f"{cid}: active scenario lacks canonical primary PR")
            continue
        if row.get("primaryOwner")!=prs[pid]["owner"] or row.get("primaryModule")!=prs[pid]["owner"]:
            fail(f"{cid}: primary owner does not match roadmap")
        if row.get("assignedStatus")!="PROPOSED_FOR_TEST_REVIEW" or observed.get("oracleStatus")!="PROPOSED_PENDING_REVIEW":
            fail(f"{cid}: proposal incorrectly promoted to approved")
        affected=row.get("impactedPrs")
        if not isinstance(affected,list) or len(affected)!=len(set(affected)) or any(p not in prs for p in affected):
            fail(f"{cid}: invalid impacted PR references")
            continue
        anchors=[p["id"] for p in roadmap["r0Prcuts"] if cid in p["criticalCaseIds"]]
        if row.get("originalRoadmapCriticalPrs")!=anchors:
            fail(f"{cid}: critical case anchors altered")
        if pid not in affected or not set(anchors).issubset(set(affected)):
            fail(f"{cid}: impacted PR list drops canonical owner/critical anchor")
        for ap in affected:
            expected_by_pr[ap].append(cid)
        primary_by_pr[pid].append(cid)
        refset=row.get("businessDecisionRefs",[])+row.get("architecturalDecisionRefs",[])
        if len(refset)!=len(set(refset)) or any(ref not in decisions for ref in refset):
            fail(f"{cid}: unknown/duplicated business/architectural decision")
        if canonical.get("decisionId") and canonical["decisionId"] not in refset:
            fail(f"{cid}: canonical BR dependency removed")
        pending=[ref for ref in refset if decisions[ref]["readiness"]!="APPROVED"]
        if row.get("blockingPendingDecisionRefs")!=pending:
            fail(f"{cid}: missing pending decision blocker")
        if not isinstance(row.get("designGaps"),list):
            fail(f"{cid}: design review gaps not recorded")
    if grouped!={"BLOCKER":60,"SAFETY":14,"E2E":10,"NEGATIVE":48}:
        fail("group totals diverge from canonical 60+14+10+48")
    if set(r.get("prId") for r in matrix.get("prMatrix",[]))!=set(prs):
        fail("PR allocation matrix missing canonical PRs")
    for row in matrix.get("prMatrix",[]):
        pid=row.get("prId")
        if pid not in prs:continue
        canonical=prs[pid]
        if row.get("canonicalOwner")!=canonical["owner"] or row.get("phase")!=canonical["phase"]:
            fail(f"{pid}: roadmap owner/phase drift")
        if row.get("canonicalCriticalCaseIds")!=canonical["criticalCaseIds"]:
            fail(f"{pid}: canonical PR critical case IDs drift")
        if set(row.get("primaryCaseIds",[]))!=set(primary_by_pr[pid]):
            fail(f"{pid}: primary scenario coverage wrong")
        if set(row.get("impactedCaseIds",[]))!=set(expected_by_pr[pid]):
            fail(f"{pid}: impacted scenario coverage wrong")
        if row.get("acceptance")!="S0_PROPOSED_NOT_APPROVED":
            fail(f"{pid}: cannot auto-approve scenario allocation")
        for ref in row.get("pendingDecisionRefs",[]):
            if ref not in decisions or decisions[ref]["readiness"]=="APPROVED":
                fail(f"{pid}: bogus decision blocker")
        if not row.get("primaryCaseIds") and "NO_PRIMARY_CANONICAL_SCENARIO_FOR_PR" not in row.get("gaps",[]):
            fail(f"{pid}: unmapped primary gap hidden")
        if not row.get("impactedCaseIds") and "NO_IMPACTED_ACTIVE_SCENARIO" not in row.get("gaps",[]):
            fail(f"{pid}: empty PR coverage gap hidden")
    reported=matrix.get("counts",{})
    actual={
        "groups":grouped,
        "blockedByAnyPendingDecision":sum(bool(x.get("blockingPendingDecisionRefs")) for x in active),
        "missingGwt":sum(bool(x.get("gwtMissing")) for x in active),
        "missingPersistentOracleFromOriginal":sum("PERSISTENT_ORACLE_REVIEW" in x.get("designGaps",[]) for x in active),
        "missingOutboxOracleFromOriginal":sum("OUTBOX_SIDE_EFFECT_ORACLE_REVIEW" in x.get("designGaps",[]) for x in active),
        "unanchoredToOriginalRoadmap":sum(not x.get("originalRoadmapCriticalPrs") for x in active),
        "pendingPrReview":26
    }
    if reported!=actual:
        fail("summary coverage/gap counts differ from case matrix")
    if matrix.get("canonicalTotal")!=132 or matrix.get("activeCount")!=121 or matrix.get("retiredCount")!=11:
        fail("canonical and active/out-of-scope totals modified")
    if matrix.get("decisionReadiness",{}).get("noHumanSignoffFabricated") is not True:
        fail("signoff evidence may not be fabricated")
    if matrix.get("decisionReadiness",{}).get("accepted")!=sum(x["readiness"]=="APPROVED" for x in ledger["decisions"]):
        fail("business readiness must match live ledger")
    return errors

def main():
    errors=validate(load(MATRIX),load(BANK),load(NEGATIVE),
                    load(ROADMAP),load(LEDGER))
    if errors:
        for err in errors:print("ERROR:",err,file=sys.stderr)
        return 1
    print("PASS: all 132 canonical scenarios allocated/retired; 121 active to 26 PRs; BR/DEC and GWT/oracle gaps visible")
    print("NOTE: these are review PROPOSALS; no test execution or business approval is certified")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
