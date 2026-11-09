#!/usr/bin/env python3
"""Mutation tests: PR-00 approvals never self-authorize by JSON status."""
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "decision_readiness", ROOT / "scripts/validate_decision_readiness.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DecisionReadinessMutationTests(unittest.TestCase):
    def setUp(self):
        self.ledger = module.load(module.LEDGER_PATH)
        self.br = module.load(module.BR_PATH)
        self.dec = module.load(module.DEC_PATH)
        self.road = module.load(module.ROAD_PATH)

    def audit(self):
        return module.validate(self.ledger, self.br, self.dec, self.road)

    def row(self, rid):
        return next(x for x in self.ledger["decisions"] if x["decisionId"] == rid)

    def test_original_pending_registry_passes(self):
        self.assertEqual(self.audit(), [])
        self.assertTrue(all(d["readiness"] == "PENDING"
                            for d in self.ledger["decisions"]))

    def test_missing_br_cannot_pass(self):
        self.ledger["decisions"] = [d for d in self.ledger["decisions"]
                                    if d["decisionId"] != "BR-01"]
        self.assertTrue(any("expected exactly" in x for x in self.audit()))

    def test_duplicate_dec_cannot_pass(self):
        self.ledger["decisions"].append(copy.deepcopy(self.row("DEC-R0-08")))
        self.assertTrue(any("duplicate decisionId" in x for x in self.audit()))

    def test_workshop_mapping_change_is_rejected(self):
        w = next(x for x in self.ledger["workshops"] if x["id"] == "W4")
        w["brIds"].remove("BR-12")
        self.assertTrue(any("W4: decision mapping" in x for x in self.audit()))

    def test_made_up_business_approval_is_rejected(self):
        self.row("BR-01")["readiness"] = "APPROVED_WITH_VERIFIED_EVIDENCE"
        self.assertTrue(any("without authoritative source approval" in x for x in self.audit()))

    def test_made_up_dec_approval_is_rejected(self):
        self.row("DEC-R0-07")["readiness"] = "APPROVED_WITH_VERIFIED_EVIDENCE"
        self.assertTrue(any("without authoritative source approval" in x for x in self.audit()))

    def test_br_source_change_without_ledger_update_is_rejected(self):
        next(x for x in self.br["decisions"] if x["decisionId"] == "BR-01")[
            "businessApproval"] = "BUSINESS_APPROVED"
        self.assertTrue(any("BR-01: source status drift" in x for x in self.audit()))

    def test_pending_dec_with_fake_verification_is_rejected(self):
        self.row("DEC-R0-04")["evidenceVerification"] = "EXTERNALLY_VERIFIED"
        self.assertTrue(any("falsely marked verified" in x for x in self.audit()))

    def test_changed_pr_gate_is_rejected(self):
        self.row("DEC-R0-03")["activationGatePrIds"] = ["PR-01"]
        self.assertTrue(any("DEC-R0-03: activation PR gate drift" in x for x in self.audit()))

    def test_approval_requires_real_evidence_and_workshop(self):
        record = self.row("BR-01")
        record["sourceStatus"] = "BUSINESS_APPROVED"
        next(x for x in self.br["decisions"] if x["decisionId"] == "BR-01")[
            "businessApproval"] = "BUSINESS_APPROVED"
        record["readiness"] = "APPROVED_WITH_VERIFIED_EVIDENCE"
        record["evidenceVerification"] = "EXTERNALLY_VERIFIED"
        self.assertTrue(any("approved without valid approvalEvidenceRef" in x
                            for x in self.audit()))
        self.assertTrue(any("requires evidenced workshop signoff" in x
                            for x in self.audit()))

    def test_unverified_evidence_reference_placeholders_rejected(self):
        self.assertFalse(module.is_reference("restricted://placeholder/test"))
        self.assertFalse(module.is_reference("test://fake/approval"))
        self.assertTrue(module.is_reference("restricted://approvals/BR-01"))

    def test_utc_validation_rejects_malformed_date(self):
        self.assertFalse(module.is_utc("2026-11-08"))
        self.assertTrue(module.is_utc("2026-11-08T09:00:00Z"))


if __name__ == "__main__":
    unittest.main()
