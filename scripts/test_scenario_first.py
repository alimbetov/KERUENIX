#!/usr/bin/env python3
"""Adversarial mutation checks for 5-stage Scenario-First TDD governance."""
from __future__ import annotations
import copy
import importlib.util
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("scenario",ROOT/"scripts/validate_scenario_first.py")
assert sp is not None and sp.loader is not None
v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)

class ScenarioFirstTests(unittest.TestCase):
    def setUp(self):
        self.p=v.load(v.PLAN);self.b=v.load(v.BASE);self.n=v.load(v.NEG)
        self.r=v.load(v.ROAD);self.f=(ROOT/v.FOUND).read_text(encoding="utf-8")
        self.doc=(ROOT/v.DOC).read_text(encoding="utf-8")
    def check(self):
        return v.validate(self.p,self.b,self.n,self.r,self.f,self.doc)
    def case(self,cid):
        return next(x for x in self.p["cases"] if x["id"]==cid)
    def test_canonical_inventory_is_valid_draft(self):
        self.assertEqual(self.check(),[])
    def test_case_removed(self):
        self.p["cases"].pop(2)
        self.assertTrue(any("inventory must match" in e for e in self.check()))
    def test_duplicate_id(self):
        self.p["cases"].insert(2,copy.deepcopy(self.p["cases"][0]))
        self.assertTrue(any("inventory must match" in e for e in self.check()))
    def test_test_first_cannot_be_skipped(self):
        self.p["fiveStages"].remove("TEST_FIRST")
        self.assertTrue(any("five-stage order" in e for e in self.check()))
    def test_test_review_cannot_be_skipped(self):
        self.p["fiveStages"].remove("TEST_REVIEW")
        self.assertTrue(any("five-stage order" in e for e in self.check()))
    def test_test_first_before_code_must_remain_true(self):
        self.p["mandatoryRules"]["testBeforeNewDomainCode"]=False
        self.assertTrue(any("testBeforeNewDomainCode" in e for e in self.check()))
    def test_false_legal_approval_rejected(self):
        self.case("NEG-R0-001")["reviewerAuthority"]="accepted"
        self.assertTrue(any("fabricated" in e for e in self.check()))
    def test_case_cannot_claim_green_without_real_evidence(self):
        self.case("NEG-R0-001")["executionStatus"]="GREEN"
        self.assertTrue(any("green claim" in e for e in self.check()))
    def test_reactivate_legacy_payment_forbidden(self):
        cid=self.r["testSelection"]["r0OutOfScopeHistory"]["caseIds"][0]
        self.case(cid)["applicability"]="APPLICABLE"
        self.assertTrue(any("payment test reactivated" in e for e in self.check()))
    def test_no_payments_rule_cannot_be_removed(self):
        self.p["mandatoryRules"]["noPayments"]=False
        self.assertTrue(any("noPayments" in e for e in self.check()))
    def test_canonical_oracle_not_silently_rewritten(self):
        self.case("NEG-R0-001")["then"]="ALLOW"
        self.assertTrue(any("oracle changed" in e for e in self.check()))
    def test_critical_case_pr_link_cannot_be_deleted(self):
        self.case("NEG-R0-001")["linkedPrs"]=[]
        self.assertTrue(any("critical PR links" in e for e in self.check()))
    def test_found_not_claimed_fully_qualified(self):
        self.case("FOUND-02")["executionStatus"]="QUALIFIED"
        self.assertTrue(any("foundation evidence" in e for e in self.check()))
    def test_signature_candidate_not_claimed_written(self):
        self.case("SIG-01")["executionStatus"]="GREEN"
        self.assertTrue(any("candidate incorrectly classified" in e for e in self.check()))
    def test_payment_absence_candidate_not_claimed_reviewed(self):
        self.case("PAY-ABS-01")["designStatus"]="REVIEWED"
        self.assertTrue(any("candidate incorrectly classified" in e for e in self.check()))
    def test_registry_cannot_claim_reviewed(self):
        self.p["status"]="S2_TEST_REVIEW_APPROVED"
        self.assertTrue(any("must not claim completion" in e for e in self.check()))

if __name__=="__main__":
    unittest.main()
