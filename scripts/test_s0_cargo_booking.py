#!/usr/bin/env python3
"""Mutation tests for S0 Cargo/Compliance/Fleet/Booking design review."""
from __future__ import annotations
import copy, importlib.util, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("cargo_s0",ROOT/"scripts/validate_s0_cargo_booking.py")
assert spec and spec.loader
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class CargoBookingS0ContractTests(unittest.TestCase):
    def setUp(self):
        self.p=v.load(v.PLAN);self.alloc=v.load(v.ALLOC);self.ext=v.load(v.EXT)
        self.ledger=v.load(v.LEDGER)
        self.report=(ROOT/v.REPORT).read_text(encoding="utf-8")
    def check(self):return v.validate(self.p,self.alloc,self.ext,self.ledger,self.report)
    def case(self,cid):return next(c for c in self.p["cases"] if c["id"]==cid)
    def test_draft_consistent_and_unreviewed(self):
        self.assertEqual(self.check(),[])
        self.assertEqual(len(self.p["cases"]),37)
    def test_case_removed(self):
        self.p["cases"].pop(3)
        self.assertTrue(any("27 primary" in x for x in self.check()))
    def test_duplicate_case(self):
        self.p["cases"].append(copy.deepcopy(self.p["cases"][0]))
        self.assertTrue(any("27 primary" in x for x in self.check()))
    def test_canonical_compliance_unknown_cannot_change(self):
        self.case("TDD-SIM-19-G13-02")["canonical"]["then"]="ALLOW"
        self.assertTrue(any("canonical GWT changed" in x for x in self.check()))
    def test_cannot_move_capacity_owner(self):
        self.case("NEG-R0-017")["originalPrimaryPr"]="PR-12"
        self.assertTrue(any("original data owner" in x for x in self.check()))
    def test_affected_pr_links_immutable(self):
        self.case("TDD-R0-E2E-02")["applicablePrs"]=[]
        self.assertTrue(any("cross-PR scope" in x for x in self.check()))
    def test_cannot_remove_br07(self):
        self.case("NEG-R0-017")["proposed"]["pendingDecisionRefs"]=[]
        self.assertTrue(any("BR/DEC blockers" in x for x in self.check()))
    def test_cannot_auto_approve_booking(self):
        self.case("NEG-R0-020")["proposed"]["activation"]="ALLOW"
        self.assertTrue(any("unauthorized positive" in x for x in self.check()))
    def test_cannot_claim_green(self):
        self.case("PR08-CARGO-01")["executionStatus"]="GREEN"
        self.assertTrue(any("false Test Review" in x for x in self.check()))
    def test_cannot_fake_reviewer(self):
        self.case("TDD-SIM-21-G21-01")["reviewerEvidence"]="signed"
        self.assertTrue(any("fabricated" in x for x in self.check()))
    def test_missing_db_oracle(self):
        self.case("NEG-R0-017")["proposed"]["dbOracle"]=""
        self.assertTrue(any("concrete dbOracle" in x for x in self.check()))
    def test_missing_outbox_oracle(self):
        self.case("NEG-R0-020")["proposed"]["eventOracle"]=""
        self.assertTrue(any("concrete eventOracle" in x for x in self.check()))
    def test_missing_ui_oracle(self):
        self.case("TDD-R0-E2E-05")["proposed"]["uiOracle"]=""
        self.assertTrue(any("concrete uiOracle" in x for x in self.check()))
    def test_cannot_unblock_unknown_compliance(self):
        self.p["guardrails"]["unknownComplianceBlocks"]=False
        self.assertTrue(any("unknownComplianceBlocks" in x for x in self.check()))
    def test_cannot_allow_double_capacity(self):
        self.p["guardrails"]["noDoubleExclusiveCapacity"]=False
        self.assertTrue(any("noDoubleExclusiveCapacity" in x for x in self.check()))
    def test_cannot_release_active_custody_on_cancel(self):
        self.p["guardrails"]["cancelDoesNotReleaseActiveCustody"]=False
        self.assertTrue(any("cancelDoesNotReleaseActiveCustody" in x for x in self.check()))
    def test_no_payments(self):
        self.p["guardrails"]["noPayments"]=False
        self.assertTrue(any("noPayments" in x for x in self.check()))
    def test_reviewer_status_not_document_ci(self):
        self.p["reviewStatus"]="APPROVED"
        self.assertTrue(any("cannot claim reviewed" in x for x in self.check()))
    def test_gwt_cargo_amendment_not_rewrite(self):
        self.case("PR08-CARGO-04")["canonical"]["then"]="MUTATE_IN_PLACE"
        self.assertTrue(any("canonical GWT changed" in x for x in self.check()))
    def test_summary_pending_br_not_hide(self):
        self.p["summary"]["pendingDecisions"]=[]
        self.assertTrue(any("pending decision summary" in x for x in self.check()))

if __name__=="__main__":
    unittest.main()
