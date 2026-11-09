#!/usr/bin/env python3
"""Cross-pack R0 Scenario Design audit: completeness only; never business/test approval."""
from __future__ import annotations
import json,sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ALLOC="docs/contracts/r0-scenario-allocation.v1.json"
EXT="docs/contracts/r0-s0-extension-gwt.v1.json"
REG="docs/contracts/r0-scenario-first-test-plan.v1.json"
ROAD="docs/contracts/tdd-development-roadmap.v1.json"
LEDGER="docs/contracts/r0-decision-readiness.v1.json"
PACKS={
"platform":"docs/contracts/r0-s0-platform-tenancy-case-contracts.v1.json",
"commercial":"docs/contracts/r0-s0-commercial-case-contracts.v1.json",
"cargo":"docs/contracts/r0-s0-cargo-fleet-booking-case-contracts.v1.json",
"execution":"docs/contracts/r0-s0-execution-pod-case-contracts.v1.json",
"downstream":"docs/contracts/r0-s0-tracking-documents-cost-case-contracts.v1.json",
"reliability":"docs/contracts/r0-s0-resilience-release-case-contracts.v1.json"}
EXPECTED_LOCAL={"SIGNATURE_CANDIDATE":18,"NO_PAYMENT_ABSENCE":6,"CARGO_LOCAL_GAP":6,
                "COMMERCIAL_COST_LOCAL_GAP":4,"RELEASE_LOCAL_GAP":4,"GOVERNANCE_LOCAL_GAP":2}
EXPECTED_TOTAL_CASES=197
REPORT="docs/57-s0-completeness-audit.md"

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def cases_by_pack(packs):
    return {
      "platform":packs["platform"]["caseContracts"],
      **{name:packs[name]["cases"] for name in ("commercial","cargo","execution","downstream","reliability")}
    }

def validate(allocation,extension,registry,roadmap,ledger,packs,report):
    errors=[]
    def fail(s):errors.append(s)
    active={x["caseId"]:x for x in allocation["cases"] if not x["retired"]}
    retired={x["caseId"] for x in allocation["cases"] if x["retired"]}
    if len(active)!=121 or len(retired)!=11 or len(allocation["cases"])!=132:
        fail("canonical 121 active + 11 retired historical cases required")
    if len(registry["cases"])!=168:
        fail("initial canonical R0 inventory must remain 168 before 16 new local cases")
    if len(packs)!=6 or set(packs)!=set(PACKS):
        fail("all six module S0 review packages required")
    entries=cases_by_pack(packs)
    if sum(map(len,entries.values()))!=EXPECTED_TOTAL_CASES:
        fail("six S0 packages require 197 case appearances including impacted-owner references")
    primary=[]
    all_ids=[]
    for name,rows in entries.items():
        stage=packs[name].get("reviewStatus",packs[name].get("status"))
        if stage!="PROPOSED_NOT_REVIEWED":
            fail(f"{name}: S0 test design cannot be auto-qualified")
        for row in rows:
            cid=row["id"]
            all_ids.append(cid)
            if cid in retired:
                fail(f"{cid}: retired positive payment case revived")
            if cid not in active:
                continue
            if name=="platform":
                owned=row["primaryPr"] in {"PR-01","PR-02","PR-03C","PR-03"}
                owner=row.get("primaryPr")
            elif name=="commercial":
                owned=row["primaryCommercialScenario"]
                owner=row.get("canonicalPrimaryPr")
            elif name=="cargo":
                owned=row["thisBatchPrimary"]
                owner=row.get("originalPrimaryPr")
            else:
                owned=row["batchPrimary"]
                owner=row.get("primaryPr")
            if owned:
                primary.append(cid)
                if owner!=active[cid]["primaryPr"]:
                    fail(f"{cid}: canonical primary owner changed across packs")
    counted=Counter(primary)
    if set(counted)!=set(active) or any(n!=1 for n in counted.values()):
        missing=sorted(set(active)-set(counted))
        duplicated=sorted(cid for cid,n in counted.items() if n>1)
        fail(f"each active canonical R0 case needs exactly one PRIMARY design: missing={missing[:10]} duplicates={duplicated[:10]}")
    present=Counter(all_ids)
    local={k:{x["caseId"] for x in extension["cases"] if x["kind"]==k} for k in EXPECTED_LOCAL}
    for kind,count in EXPECTED_LOCAL.items():
        if len(local[kind])!=count:
            fail(f"{kind}: candidate/local inventory count drift")
    expected_packed={
      "SIGNATURE_CANDIDATE":"commercial","CARGO_LOCAL_GAP":"cargo",
      "COMMERCIAL_COST_LOCAL_GAP":"downstream","RELEASE_LOCAL_GAP":"reliability"}
    for kind,pack in expected_packed.items():
        actual={x["id"] for x in entries[pack]}
        if not local[kind].issubset(actual) or any(present[cid]!=1 for cid in local[kind]):
            fail(f"{kind}: local scenario must occur once and be owned by {pack}")
    if any(present[x]!=0 for kind in ("NO_PAYMENT_ABSENCE","GOVERNANCE_LOCAL_GAP") for x in local[kind]):
        fail("PAY-ABS and PR00-GOV candidates live in separate governance register, not invented module tests")
    candidate_ids=set().union(*local.values())
    if set(primary)&candidate_ids:
        fail("R0 canonical IDs must not be confused with additional local candidates")
    unique_total=len(set(active)|retired|candidate_ids|{f"FOUND-{i:02}" for i in range(1,13)})
    if unique_total!=184:
        fail(f"R0 total unique IDs must be 184 (132+12+24+16); got {unique_total}")
    found={f"FOUND-{i:02}" for i in range(1,13)}
    if found!={row["id"] for row in entries["platform"] if row["id"].startswith("FOUND-")}:
        fail("FOUND-01..12 must retain foundation case design coverage")
    roadmap_prs={x["id"] for x in roadmap["r0Prcuts"]}
    covered_prs={x["primaryPr"] for x in active.values()}
    covered_prs.update(x["ownerPr"] for x in extension["cases"])
    if covered_prs!=roadmap_prs or len(covered_prs)!=26:
        fail("all 26 PRs must have at least one scenario or local review candidate")
    decision_list=ledger["decisions"]
    if len(decision_list)!=20 or any(x.get("readiness")!="PENDING" for x in decision_list):
        fail("BR/DEC changed: manual business/legal review required before gate transition")
    for name in ("Platform/Tenancy","Commercial","Cargo","Execution","Tracking","Resilience","121","11","S0","BR/DEC"):
        if name not in report:
            fail("S0 audit report missing "+name)
    return errors

def main():
    errors=validate(load(ALLOC),load(EXT),load(REG),load(ROAD),load(LEDGER),
                    {k:load(p) for k,p in PACKS.items()},
                    (ROOT/REPORT).read_text(encoding="utf-8"))
    if errors:
        for e in errors:print("ERROR:",e,file=sys.stderr)
        return 1
    print("PASS: six S0 design packs, all 121 active R0 cases exactly one primary owner; 11 retired; 26 PRs with design coverage")
    print("PASS: 12 FOUND + 18 SIG + 6 PAY-ABS + 6 cargo + 4 cost + 4 release + 2 governance = 184 unique historical and local IDs")
    print("WARNING: 20 BR/DEC pending, no stakeholder Test Review, no automatic S1 or domain implementation")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
