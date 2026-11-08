#!/usr/bin/env python3
"""Mutation checks for canonical E2E Scenario Design S0 proposals."""
from __future__ import annotations
import copy
import importlib.util
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("s0e2e",ROOT/"scripts/validate_s0_e2e.py")
assert spec and spec.loader
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class E2EProposalTests(unittest.TestCase):
    def setUp(self):
        self.p=v.load(v.DRAFT);self.b=v.load(v.BANK);self.a=v.load(v.ALLOCATION)
    def check(self):
        return v.validate(self.p,self.b,self.a)
    def case(self,cid):
        return next(x for x in self.p["cases"] if x["caseId"]==cid)
    def test_current_draft_is_consistent_not_executed(self):
        self.assertEqual(self.check(),[])
    def test_all_ten_original_cases_must_exist(self):
        self.p["cases"].pop()
        self.assertTrue(any("all 10" in x for x in self.check()))
    def test_duplicate_e2e_case_detected(self):
        self.p["cases"].append(copy.deepcopy(self.p["cases"][0]))
        self.assertTrue(any("all 10" in x for x in self.check()))
    def test_canonical_journey_unchanged(self):
        self.case("TDD-R0-E2E-01")["canonicalJourney"]="fake"
        self.assertTrue(any("canonical E2E" in x for x in self.check()))
    def test_canonical_then_unchanged(self):
        self.case("TDD-R0-E2E-04")["canonicalThen"]="DELIVERED"
        self.assertTrue(any("canonical E2E" in x for x in self.check()))
    def test_steps_cannot_be_removed(self):
        self.case("TDD-R0-E2E-04")["proposed"]["whenSteps"]=[]
        self.assertTrue(any("whenSteps" in x for x in self.check()))
    def test_actor_context_required(self):
        self.case("TDD-R0-E2E-09")["proposed"]["actors"]=[]
        self.assertTrue(any("actors" in x for x in self.check()))
    def test_db_oracle_required(self):
        self.case("TDD-R0-E2E-05")["proposed"]["expected"]["db"]=""
        self.assertTrue(any("specific db" in x for x in self.check()))
    def test_outbox_oracle_required(self):
        self.case("TDD-R0-E2E-03")["proposed"]["expected"]["events"]=""
        self.assertTrue(any("specific events" in x for x in self.check()))
    def test_concurrency_negative_case_required(self):
        self.case("TDD-R0-E2E-02")["proposed"]["negativeVariants"]=[]
        self.assertTrue(any("negativeVariants" in x for x in self.check()))
    def test_cannot_forge_stakeholder_review(self):
        self.case("TDD-R0-E2E-04")["stage"]="REVIEWED"
        self.assertTrue(any("false Test Review" in x for x in self.check()))
    def test_cannot_claim_s1_e2e_green(self):
        self.case("TDD-R0-E2E-01")["testExecution"]="PASS"
        self.assertTrue(any("false Test Review" in x for x in self.check()))
    def test_cannot_reenable_payment_e2e(self):
        self.case("TDD-R0-E2E-06")["retired"]=False
        self.assertTrue(any("remain retired" in x for x in self.check()))
    def test_payment_absence_replacements_mandatory(self):
        self.case("TDD-R0-E2E-06")["replacedBy"]=[]
        self.assertTrue(any("replacement incomplete" in x for x in self.check()))
    def test_decision_refs_must_match_allocation(self):
        self.case("TDD-R0-E2E-05")["proposed"]["pendingDecisionRefs"]=[]
        self.assertTrue(any("pending list" in x for x in self.check()))
    def test_cannot_claim_draft_approved(self):
        self.p["status"]="S2_APPROVED"
        self.assertTrue(any("may not claim approval" in x for x in self.check()))

if __name__=="__main__":
    unittest.main()
