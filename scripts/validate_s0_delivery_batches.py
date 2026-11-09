#!/usr/bin/env python3
"""S0 delivery-phase design validator: specs ≠ executable tests ≠ business approval."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ALLOC="docs/contracts/r0-scenario-allocation.v1.json"
EXT="docs/contracts/r0-s0-extension-gwt.v1.json"
LEDGER="docs/contracts/r0-decision-readiness.v1.json"
BATCHES={
 "execution_custody_pod":{
   "file":"docs/contracts/r0-s0-execution-pod-case-contracts.v1.json",
   "report":"docs/54-s0-execution-pod-test-design.md",
   "prs":["PR-13","PR-14"],
   "localKind":None,"counts":(22,3,0,25),
   "requiredRules":["noNewDomainCode","custodyOwnerNeverAmbiguous","handlingUnitConservation",
                    "partialPodNotCompleted","immutableOriginalEvidence","offlineReplayDedup",
                    "unapprovedBindingActionsDenyOrHold","noPayments","reviewCannotBeIssuedByCi"]},
 "tracking_documents_cost":{
   "file":"docs/contracts/r0-s0-tracking-documents-cost-case-contracts.v1.json",
   "report":"docs/55-s0-tracking-documents-cost-test-design.md",
   "prs":["PR-15","PR-16","PR-16R","PR-17"],
   "localKind":"COMMERCIAL_COST_LOCAL_GAP","counts":(6,7,4,17),
   "requiredRules":["noNewDomainCode","tenantAccountTrackingScope","staleLocationNotConfirmed",
                    "originalProofImmutable","signedUrlTtlExplicit","reviewOnlyAfterVerifiedComplete",
                    "costWithoutSettlement","noPayments","reviewCannotBeIssuedByCi"]},
 "resilience_release":{
   "file":"docs/contracts/r0-s0-resilience-release-case-contracts.v1.json",
   "report":"docs/56-s0-resilience-release-test-design.md",
   "prs":["PR-18","PR-19","PR-20"],
   "localKind":"RELEASE_LOCAL_GAP","counts":(18,7,4,29),
   "requiredRules":["noNewDomainCode","suspensionSafetyScopeNotGeneralAuth","noBookingDuringSuspension",
                    "noLostCustodyOnCrash","outboxInboxIdempotent","exactShaReleaseEvidence",
                    "restoreDrillRequired","twoTenantPilotRequired","noPayments","reviewCannotBeIssuedByCi"]}
}

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def validate(batch,plan,allocation,extensions,ledger,report):
    errors=[]
    def fail(msg):errors.append(msg)
    cfg=BATCHES[batch];scope=set(cfg["prs"])
    base=allocation["cases"]
    primary=[x for x in base if not x["retired"] and x["primaryPr"] in scope]
    impacted=[x for x in base if not x["retired"] and x["primaryPr"] not in scope
              and scope.intersection(x["impactedPrs"])]
    local=[x for x in extensions["cases"] if x["kind"]==cfg["localKind"]] if cfg["localKind"] else []
    source=primary+impacted+local
    exp=[x["caseId"] for x in source]
    rows=plan.get("cases",[])
    names=[x.get("id") for x in rows]
    n=(len(primary),len(impacted),len(local),len(rows))
    if n!=cfg["counts"] or names!=exp or len(set(names))!=cfg["counts"][3]:
        fail(f"{batch}: missing/duplicate case, expected scope {cfg['counts']} got {n}")
    if plan.get("batch")!=batch or plan.get("phase")!="S0_SCENARIO_DESIGN" or plan.get("status")!="PROPOSED_NOT_REVIEWED":
        fail(f"{batch}: cannot bypass S0 draft review")
    if plan.get("scopePrs")!=cfg["prs"] or plan.get("sourceAllocation")!=ALLOC:
        fail(f"{batch}: original PR allocation/owner changed")
    count=plan.get("count",{})
    if tuple(count.get(k) for k in ("primary","impacted","local","total"))!=cfg["counts"]:
        fail(f"{batch}: summary count drift")
    rules=plan.get("rules",{})
    for name in cfg["requiredRules"]:
        if rules.get(name) is not True:
            fail(f"{batch}: missing safety rule {name}")
    decision_state={x["decisionId"]:x["readiness"] for x in ledger["decisions"]}
    for i,source_row in enumerate(source):
        if i>=len(rows):break
        r=rows[i]
        cid=source_row["caseId"]
        is_local=i>=len(primary)+len(impacted)
        if is_local:
            canonical={k:source_row[k] for k in ("given","when","then")}
            original_pr=source_row["ownerPr"];owner=source_row["owner"]
            affected=[original_pr];pending=[]
        else:
            canonical={k:source_row["expected"]["canonical"+k.title()] for k in ("given","when","then")}
            original_pr=source_row["primaryPr"];owner=source_row["primaryOwner"]
            affected=[x for x in source_row["impactedPrs"] if x in scope]
            pending=source_row["blockingPendingDecisionRefs"]
        if r.get("canonical")!=canonical:
            fail(f"{cid}: canonical Given/When/Then changed")
        if r.get("primaryPr")!=original_pr or r.get("ownerModule")!=owner:
            fail(f"{cid}: original module owner changed")
        if r.get("impactedPrs")!=affected or r.get("batchPrimary")!=(i<len(primary) or is_local):
            fail(f"{cid}: impacted/primary PR coverage modified")
        proposal=r.get("proposal",{})
        if proposal.get("pendingDecisionRefs")!=pending:
            fail(f"{cid}: BR/DEC blockers hidden")
        if proposal.get("activation")!=("DENY_HOLD_UNTIL_BR_DEC" if pending else "TECHNICAL_SCOPE_PROPOSAL"):
            fail(f"{cid}: unauthorized positive activation")
        for prop in ("dbOracle","eventOracle","httpUiOracle"):
            text=proposal.get(prop)
            if not isinstance(text,str) or len(text.strip())<34:
                fail(f"{cid}: missing observable {prop}")
        when=proposal.get("whenSteps")
        if not isinstance(when,list) or not when or not all(isinstance(x,str) and len(x.strip())>9 for x in when):
            fail(f"{cid}: missing actionable steps")
        negatives=proposal.get("negativeVariants")
        if not isinstance(negatives,list) or len(negatives)<2:
            fail(f"{cid}: missing negative/failure variants")
        if not isinstance(proposal.get("testHarness"),str) or "#" not in proposal["testHarness"]:
            fail(f"{cid}: test harness plan missing")
        if r.get("status")!="S0_DRAFT_UNREVIEWED" or r.get("testStatus")!="NOT_WRITTEN":
            fail(f"{cid}: cannot claim Test Review or GREEN")
        if r.get("reviewer") is not None or r.get("evidence") is not None:
            fail(f"{cid}: fabricated reviewer/evidence")
        if any(decision_state.get(ref)!="PENDING" for ref in pending):
            fail(f"{cid}: source BR/DEC changed; new review required")
    for name in ("S0","PR-13","PR-14") if batch=="execution_custody_pod" else ("S0", "PR-17" if batch=="tracking_documents_cost" else "PR-20"):
        if name not in report:fail(f"{batch}: missing report coverage {name}")
    return errors

def main(argv):
    batch=argv[1] if len(argv)>1 else "execution_custody_pod"
    if batch not in BATCHES:
        print(f"unknown batch {batch}",file=sys.stderr);return 2
    cfg=BATCHES[batch]
    errors=validate(batch,load(cfg["file"]),load(ALLOC),load(EXT),load(LEDGER),
                    (ROOT/cfg["report"]).read_text(encoding="utf-8"))
    if errors:
        for e in errors:print("ERROR:",e,file=sys.stderr)
        return 1
    print(f"PASS: {batch} S0 designs match canonical source, negative/failure oracles, pending decision and no false approval")
    print("NOTE: test design contracts are not executable tests, legal signoff, or accepted S0")
    return 0

if __name__=="__main__":
    raise SystemExit(main(sys.argv))
