#!/usr/bin/env python3
"""CI acceptance manifest validator: no PR qualifies by silently editing status.

Checks structure and evidence references only, not reviewer identity,
legal signature authenticity or business production acceptance.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST="docs/contracts/pr-acceptance-manifest.v1.json"
ROADMAP="docs/contracts/tdd-development-roadmap.v1.json"
BR="docs/contracts/r0-blocker-decisions.v1.json"
DEC="docs/contracts/r0-delivery-contract.v1.json"

def load(path:str)->dict:
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def validate(manifest:dict, road:dict, br:dict, dec:dict)->list[str]:
    errors:list[str]=[]
    if manifest.get("schemaVersion")!="1.0.0" or manifest.get("roadmapVersion")!=road.get("schemaVersion"):
        errors.append("manifest: schema or roadmap version mismatch")
    sem=manifest.get("semantics",{})
    if not (sem.get("noPayments") is True and sem.get("noAutomaticBusinessApproval") is True
            and sem.get("qualificationIsNotDocumentationCI") is True):
        errors.append("manifest: no-payments or non-auto-approval invariants missing")
    source={p["id"]:p for p in road["r0Prcuts"]}
    cuts=manifest.get("acceptanceSlices",[])
    ids=[r.get("id") for r in cuts]
    if len(ids)!=len(set(ids)):errors.append("manifest: duplicate PR identifier")
    if len(ids)!=26 or set(ids)!=set(source):
        errors.append("manifest: must cover exactly 26 roadmap PR cuts")
    br_map={b["decisionId"]:b for b in br["decisions"]}
    dec_map={d["id"]:d for d in dec["decisions"]}
    approved_br={k for k,v in br_map.items() if v["businessApproval"]=="BUSINESS_APPROVED"}
    approved_dec={k for k,v in dec_map.items() if v["status"]=="APPROVED"}
    for row in cuts:
        pid=row.get("id")
        p=source.get(pid)
        if p is None:continue
        for key,expected in [
            ("phase",p["phase"]),
            ("canonicalOwner",p["owner"]),
            ("dependsOnPrs",p["dependsOnPrs"]),
            ("brRefs",p["activationGate"].get("br",[])),
            ("decRefs",[d["id"] for d in dec["decisions"] if d["mustDecideBy"]==pid]),
            ("criticalCaseIds",p["criticalCaseIds"]),
            ("activationGateMode",p["activationGate"]["mode"]),
            ("uiRequired",p["uiAcceptance"]["required"])
        ]:
            if row.get(key)!=expected:
                errors.append(f"{pid}: {key} differs from roadmap/delivery contract")
        status=row.get("qualificationStatus")
        if status not in ("NOT_QUALIFIED","CODE_VERIFIED_DENY_ONLY","QUALIFIED"):
            errors.append(f"{pid}: invalid qualificationStatus")
        ev=row.get("verification",{})
        level=ev.get("level")
        allowed={"NOT_EXECUTED","DOC_CONTRACT_CHECKS_GREEN","PLATFORM_PARTIAL_INTEGRATION_GREEN",
                 "CODE_TESTS_EXECUTED","FULL_ACCEPTANCE_VERIFIED"}
        if level not in allowed:
            errors.append(f"{pid}: invalid verification level")
        if level != "NOT_EXECUTED":
            sha=ev.get("verifiedSha")
            if not isinstance(sha,str) or re.fullmatch(r"[0-9a-f]{40}",sha) is None:
                errors.append(f"{pid}: evidence missing exact 40-hex commit SHA")
            if not ev.get("ciRuns") or not all(isinstance(url,str) and
                    re.fullmatch(r"https://github.com/alimbetov/KERUENIX/actions/runs/[0-9]+",url)
                    for url in ev["ciRuns"]):
                errors.append(f"{pid}: CI runs must link to exact GitHub Actions")
            if not ev.get("testRefs") or not all(isinstance(path,str) and
                    path and (ROOT/path).is_file() for path in ev["testRefs"]):
                errors.append(f"{pid}: verified evidence requires actual test source files")
        if level=="PLATFORM_PARTIAL_INTEGRATION_GREEN":
            if pid!="PR-01" or status!="NOT_QUALIFIED":
                errors.append(f"{pid}: partial foundation evidence cannot qualify a PR")
            for proof in ev.get("partialProof",[]):
                if proof.get("requirementId") not in {f"FOUND-{i:02d}" for i in range(1,13)}:
                    errors.append(f"{pid}: unknown FOUND partial evidence")
                if not proof.get("coverage"):
                    errors.append(f"{pid}: partial proof without scoped coverage")
        if level=="DOC_CONTRACT_CHECKS_GREEN" and (pid!="PR-00" or status!="NOT_QUALIFIED"):
            errors.append(f"{pid}: documentation evidence cannot certify PR qualification")
        acceptance=row.get("acceptance",{})
        keys=("moduleBoundary","securityAuthorization","realDbRls","transactionAndReplay",
              "frontendE2e","performanceAndRecovery","releaseArtifacts")
        if set(acceptance)!=set(keys):
            errors.append(f"{pid}: incomplete acceptance matrix")
        if any(acceptance.get(k) not in ("NOT_VERIFIED","VERIFIED","NOT_APPLICABLE_WITH_REASON")
               for k in keys):
            errors.append(f"{pid}: invalid acceptance matrix state")
        if status=="CODE_VERIFIED_DENY_ONLY":
            if level not in ("CODE_TESTS_EXECUTED","FULL_ACCEPTANCE_VERIFIED"):
                errors.append(f"{pid}: fail-closed code qualification requires verified code tests")
            if row.get("businessApprovalEvidenceRefs"):
                errors.append(f"{pid}: deny-only code cannot claim business signoff")
        if status=="QUALIFIED":
            if level!="FULL_ACCEPTANCE_VERIFIED":
                errors.append(f"{pid}: QUALIFIED requires FULL_ACCEPTANCE_VERIFIED")
            missing={*row.get("brRefs",[])}-approved_br
            missing.update(set(row.get("decRefs",[]))-approved_dec)
            if missing:
                errors.append(f"{pid}: QUALIFIED with pending approvals {sorted(missing)}")
            evidence=row.get("qualificationEvidence",{})
            for f in ("commitSha","ciRunUrl","testReportPath",
                      "reviewerAuthorityRef","approvalEvidenceRef"):
                if not evidence.get(f):
                    errors.append(f"{pid}: QUALIFIED without {f}")
            if row.get("uiRequired") and not evidence.get("frontendE2eRef"):
                errors.append(f"{pid}: QUALIFIED without frontendE2eRef")
            if row.get("acceptance",{}).get("securityAuthorization")!="VERIFIED":
                errors.append(f"{pid}: QUALIFIED requires verified security acceptance")
    return errors

def main()->int:
    errors=validate(load(MANIFEST),load(ROADMAP),load(BR),load(DEC))
    if errors:
        for err in errors:print("ERROR:",err,file=sys.stderr)
        print(f"FAILED: {len(errors)} PR acceptance violations",file=sys.stderr)
        return 1
    print("PASS: 26 PRs mapped to owner/DAG/BR/DEC/tests/UI; no false qualification")
    print("NOTE: acceptance manifest does not verify external signoff authenticity.")
    return 0

if __name__=="__main__":
    sys.exit(main())
