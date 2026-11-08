#!/usr/bin/env python3
"""PR-00 decision and workshop readiness contract. Standard library only.

A green result proves structural consistency, not authenticity of approvals.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = "docs/contracts/r0-decision-readiness.v1.json"
BR_PATH = "docs/contracts/r0-blocker-decisions.v1.json"
DEC_PATH = "docs/contracts/r0-delivery-contract.v1.json"
ROAD_PATH = "docs/contracts/tdd-development-roadmap.v1.json"
APPROVAL_FIELDS = ("approvalEvidenceRef", "approverAuthorityRef", "approvedVersion",
                   "approvedAtUtc", "independentVerificationEvidenceRef")


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def is_reference(value: object) -> bool:
    if not isinstance(value, str) or not value or len(value) > 512:
        return False
    lowered = value.lower()
    if any(t in lowered for t in ("placeholder", "example", "todo", "pending",
                                    "fake", "test://", "sample")):
        return False
    return bool(re.match(r"^(restricted|evidence|audit|artifact)://[^/\s]+/[^\s]+$", value))


def is_utc(value: object) -> bool:
    if not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate(ledger: dict, br: dict, dec: dict, roadmap: dict) -> list[str]:
    errors: list[str] = []
    if ledger.get("schemaVersion") != "1.0.0":
        errors.append("ledger: unsupported schemaVersion")
    if ledger.get("semantics", {}).get("productBoundary") != "NO_PAYMENTS":
        errors.append("ledger: NO_PAYMENTS boundary missing")
    if ledger.get("semantics", {}).get("approvalRecordsCannotSelfAuthorize") is not True:
        errors.append("ledger: evidence records cannot self-authorize")
    br_map = {x["decisionId"]: x for x in br["decisions"]}
    dec_map = {x["id"]: x for x in dec["decisions"]}
    pr_ids = {x["id"] for x in roadmap["r0Prcuts"]}
    gates = {key: sorted(x["id"] for x in roadmap["r0Prcuts"]
                         if key in x.get("activationGate", {}).get("br", []))
             for key in br_map}
    wanted_workshops = {
        "W1": ({"BR-01", "BR-02", "BR-03", "BR-05"},
               {"DEC-R0-01", "DEC-R0-02", "DEC-R0-03"}),
        "W2": ({"BR-06", "BR-07", "BR-08"}, {"DEC-R0-06"}),
        "W3": ({"BR-09", "BR-10"}, {"DEC-R0-05", "DEC-R0-08"}),
        "W4": ({"BR-11", "BR-12"}, {"DEC-R0-04", "DEC-R0-07"}),
        "W5": ({"BR-04"}, set()),
    }
    workshops = ledger.get("workshops", [])
    if len({w.get("id") for w in workshops}) != len(workshops):
        errors.append("workshop: duplicate ID")
    if {w.get("id") for w in workshops} != set(wanted_workshops):
        errors.append("workshop: must contain exactly W1..W5")
    workshop_map = {w.get("id"): w for w in workshops}
    for wid, (wanted_br, wanted_dec) in wanted_workshops.items():
        workshop = workshop_map.get(wid, {})
        if set(workshop.get("brIds", [])) != wanted_br or set(
                workshop.get("decIds", [])) != wanted_dec:
            errors.append(f"{wid}: decision mapping differs from workshop plan")
        if not workshop.get("requiredParticipantRoles"):
            errors.append(f"{wid}: missing mandatory participant roles")
        status = workshop.get("status")
        if status not in ("NOT_CONDUCTED", "CONDUCTED_PENDING_SIGNOFF",
                          "SIGNED_OFF_WITH_EVIDENCE"):
            errors.append(f"{wid}: unknown workshop status")
        if status != "NOT_CONDUCTED":
            for field in ("heldAtUtc", "meetingEvidenceRef",
                          "participantAuthorityEvidenceRef", "facilitatorAuthorityRef"):
                value = workshop.get(field)
                if field == "heldAtUtc":
                    if not is_utc(value):
                        errors.append(f"{wid}: meeting requires valid UTC date")
                elif not is_reference(value):
                    errors.append(f"{wid}: meeting requires {field}")
        if status == "SIGNED_OFF_WITH_EVIDENCE" and not is_reference(
                workshop.get("signoffRecordRef")):
            errors.append(f"{wid}: signed workshop missing signoffRecordRef")

    decisions = ledger.get("decisions", [])
    ids = [x.get("decisionId") for x in decisions]
    if len(ids) != len(set(ids)):
        errors.append("ledger: duplicate decisionId")
    if set(ids) != set(br_map) | set(dec_map) or len(ids) != 20:
        errors.append("ledger: expected exactly all 12 BR and 8 DEC decisions")
    for record in decisions:
        rid = record.get("decisionId")
        kind = record.get("kind")
        source = br_map.get(rid) if kind == "BR" else dec_map.get(rid) if kind == "DEC" else None
        if source is None:
            errors.append(f"{rid}: unknown decision kind/source")
            continue
        wanted_source_path = BR_PATH if kind == "BR" else DEC_PATH
        if record.get("sourceContract") != wanted_source_path:
            errors.append(f"{rid}: source path drift")
        source_state = source["businessApproval"] if kind == "BR" else source["status"]
        if record.get("sourceStatus") != source_state:
            errors.append(f"{rid}: source status drift")
        w_id = record.get("workshopId")
        workshop = workshop_map.get(w_id, {})
        if rid not in workshop.get("brIds" if kind == "BR" else "decIds", []):
            errors.append(f"{rid}: workshop reference mismatch")
        target_gates = gates[rid] if kind == "BR" else [source["mustDecideBy"]]
        if sorted(record.get("activationGatePrIds", [])) != sorted(target_gates):
            errors.append(f"{rid}: activation PR gate drift")
        if any(g not in pr_ids for g in target_gates):
            errors.append(f"{rid}: unknown PR gate")
        state = record.get("readiness")
        if state not in ("PENDING", "APPROVED_WITH_VERIFIED_EVIDENCE",
                         "REJECTED_SAFE_DENY", "DEFERRED_SAFE_DENY"):
            errors.append(f"{rid}: invalid readiness status")
            continue
        authorized = source_state == ("BUSINESS_APPROVED" if kind == "BR" else "APPROVED")
        if state == "APPROVED_WITH_VERIFIED_EVIDENCE":
            if not authorized:
                errors.append(f"{rid}: readiness approval without authoritative source approval")
            if record.get("evidenceVerification") != "EXTERNALLY_VERIFIED":
                errors.append(f"{rid}: approval requires independent verification")
            for field in APPROVAL_FIELDS:
                value = record.get(field)
                valid = is_utc(value) if field == "approvedAtUtc" else (
                    isinstance(value, str) and bool(re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", value))
                    if field == "approvedVersion" else is_reference(value))
                if not valid:
                    errors.append(f"{rid}: approved without valid {field}")
            if record.get("requiredLegalReview") and not is_reference(
                    record.get("applicableLegalProfileRef")):
                errors.append(f"{rid}: legal profile approval missing")
            if kind == "BR" and workshop.get("status") != "SIGNED_OFF_WITH_EVIDENCE":
                errors.append(f"{rid}: BR approval requires evidenced workshop signoff")
            for field in ("approvalEvidenceRef", "approverAuthorityRef",
                          "approvedVersion", "approvedAtUtc"):
                if source.get(field) != record.get(field):
                    errors.append(f"{rid}: approved evidence differs from authoritative decision")
            if kind == "BR" and record.get("requiredLegalReview") and source.get("legalApproval") != "APPROVED":
                errors.append(f"{rid}: legally material BR requires legal signoff")
        elif state == "PENDING":
            if authorized:
                errors.append(f"{rid}: authoritative approval not reflected in evidence ledger")
            if record.get("evidenceVerification") != "NOT_VERIFIED":
                errors.append(f"{rid}: pending decision falsely marked verified")
        else:
            if source_state not in ("REJECTED", "DEFERRED_SAFE_DENY"):
                errors.append(f"{rid}: disposition differs from authoritative status")
            if not record.get("dispositionRationale"):
                errors.append(f"{rid}: safe denial requires rationale")
    return errors


def main() -> int:
    errors = validate(load(LEDGER_PATH), load(BR_PATH), load(DEC_PATH), load(ROAD_PATH))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAILED: {len(errors)} decision-readiness problems", file=sys.stderr)
        return 1
    print("PASS: 12 BR + 8 DEC, 5 workshops, PR activation gates and evidence controls")
    print("NOTE: decision-ledger validation does not verify external signatures or approve business actions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
