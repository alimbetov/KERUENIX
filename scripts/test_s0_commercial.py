#!/usr/bin/env python3
"""Adversarial tests of Commercial Scenario-First S0 review contracts."""
from __future__ import annotations
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("commercial_s0",ROOT/"scripts/validate_s0_commercial.py")
assert spec and spec.loader
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class CommercialS0Mutations(unittest.TestCase):
    def setUp(self):
        self.d=v.read_json(v.DESIGN)
        self.alloc=v.read_json(v.ALLOC)
        self.ext=v.read_json(v.EXT)
        self.ledger=v.read_json(v.LEDGER)
        self.doc=(ROOT/v.REPORT).read_text(encoding="utf-8")
    def check(self):
        return v.validate(self.d,self.alloc,self.ext,self.ledger,self.doc)
    def case(self,cid):
        return next(x for x in self.d["cases"] if x["id"]==cid)
    def test_original_draft_consistent(self):
        self.assertEqual(self.check(),[])
        self.assertEqual(len(self.d["cases"]),57)
    def test_missing_primary_scenario(self):
        self.d["cases"].pop(0)
        self.assertTrue(any("30 primary" in e for e in self.check()))
    def test_duplicate_signature(self):
        self.d["cases"].append(copy.deepcopy(self.case("SIG-01")))
        self.assertTrue(any("30 primary" in e for e in self.check()))
    def test_changing_canonical_then(self):
        self.case("TDD-SIM-13-G01-01")["canonical"]["then"]="ACCEPTED_WITHOUT_SIGNER"
        self.assertTrue(any("canonical GWT" in e for e in self.check()))
    def test_br01_cannot_be_removed(self):
        self.case("TDD-SIM-13-G01-01")["draft"]["pendingDecisionRefs"]=[]
        self.assertTrue(any("BR/DEC dependency" in e for e in self.check()))
    def test_bypass_business_binding_gate_rejected(self):
        self.case("TDD-SIM-13-G01-01")["draft"]["expectedActivation"]="ALLOW"
        self.assertTrue(any("fail-closed activation" in e for e in self.check()))
    def test_no_fake_signature_acceptance(self):
        self.case("SIG-01")["draft"]["additionalLegalGate"]=None
        self.assertTrue(any("legally gated" in e for e in self.check()))
    def test_sig_profile_cannot_be_approved_through_ci(self):
        self.case("SIG-01")["reviewAuthority"]="fake approver"
        self.assertTrue(any("fabricated" in e for e in self.check()))
    def test_reassign_quote_owner_fails(self):
        self.case("TDD-SIM-10-G08-01")["canonicalPrimaryPr"]="PR-05"
        self.assertTrue(any("canonical owner" in e for e in self.check()))
    def test_cross_pr_link_cannot_be_hidden(self):
        self.case("TDD-R0-E2E-01")["commercialImpactedPrs"]=[]
        self.assertTrue(any("impacted PR links" in e for e in self.check()))
    def test_missing_outbox_oracle(self):
        self.case("NEG-R0-009")["draft"]["sideEffectOracle"]=""
        self.assertTrue(any("concrete sideEffectOracle" in e for e in self.check()))
    def test_missing_ui_oracle(self):
        self.case("NEG-R0-010")["draft"]["httpUiOracle"]=""
        self.assertTrue(any("concrete httpUiOracle" in e for e in self.check()))
    def test_no_payments_invariant_cannot_change(self):
        self.d["rules"]["noPayments"]=False
        self.assertTrue(any("safety rule" in e for e in self.check()))
    def test_carrier_selection_is_not_booking(self):
        self.d["rules"]["carrierSelectionNotBooking"]=False
        self.assertTrue(any("carrierSelectionNotBooking" in e for e in self.check()))
    def test_quote_immutability_must_remain(self):
        self.d["rules"]["quoteImmutable"]=False
        self.assertTrue(any("quoteImmutable" in e for e in self.check()))
    def test_compilation_failure_not_test_pass(self):
        self.case("NEG-R0-013")["execution"]="PASS"
        self.assertTrue(any("executable test claim" in e for e in self.check()))
    def test_test_review_not_allowed_from_docs_ci(self):
        self.d["status"]="TEST_REVIEWED"
        self.assertTrue(any("cannot claim completed" in e for e in self.check()))
    def test_signature_missing_gwt_rejected(self):
        self.case("SIG-18")["canonical"]["when"]=""
        self.assertTrue(any("canonical GWT" in e for e in self.check()))
    def test_summary_missing_pending_decision(self):
        self.d["summary"]["pendingDecisions"]=[]
        self.assertTrue(any("pending decision coverage" in e for e in self.check()))

if __name__=="__main__":
    unittest.main()
