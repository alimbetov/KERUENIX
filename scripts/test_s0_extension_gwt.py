#!/usr/bin/env python3
"""Mutation tests: missing signature/absence or invented approval must fail S0."""
from __future__ import annotations
import copy
import importlib.util
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("extension",ROOT/"scripts/validate_s0_extension_gwt.py")
assert sp and sp.loader
v=importlib.util.module_from_spec(sp)
sp.loader.exec_module(v)

class ExtensionGwtTests(unittest.TestCase):
    def setUp(self):
        self.p=v.load(v.PLAN);self.r=v.load(v.REGISTRY);self.road=v.load(v.ROAD)
    def check(self):
        return v.validate(self.p,self.r,self.road)
    def case(self,cid):
        return next(x for x in self.p["cases"] if x["caseId"]==cid)
    def test_consistent_unapproved_s0_draft(self):
        self.assertEqual(self.check(),[])
    def test_missing_signature_case(self):
        self.p["cases"].pop(0)
        self.assertTrue(any("18 SIG" in x for x in self.check()))
    def test_duplicate_payment_absence(self):
        self.p["cases"].insert(19,copy.deepcopy(self.p["cases"][18]))
        self.assertTrue(any("18 SIG" in x for x in self.check()))
    def test_preexisting_candidate_must_exist_in_registry(self):
        self.r["cases"]=[x for x in self.r["cases"] if x["id"]!="SIG-01"]
        self.assertTrue(any("candidate vs new local" in x for x in self.check()))
    def test_missing_cargo_oracle(self):
        self.case("PR08-CARGO-01")["dbOracle"]=""
        self.assertTrue(any("missing concrete dbOracle" in x for x in self.check()))
    def test_false_green_rejected(self):
        self.case("SIG-18")["testExecution"]="GREEN"
        self.assertTrue(any("cannot fake test completion" in x for x in self.check()))
    def test_forged_review_evidence_rejected(self):
        self.case("PR17-COST-01")["reviewerEvidence"]="approved"
        self.assertTrue(any("stakeholder review" in x for x in self.check()))
    def test_allowing_payment_scope_rejected(self):
        self.p["scope"]="PAYMENTS"
        self.assertTrue(any("no-payments" in x for x in self.check()))
    def test_unsafe_signature_auto_approval_rejected(self):
        self.case("SIG-01")["legalDependency"]=None
        self.assertTrue(any("legally gated" in x for x in self.check()))
    def test_payment_absence_relabel_detected(self):
        self.case("PAY-ABS-03")["kind"]="PAYMENT_IMPLEMENTATION"
        self.assertTrue(any("must never activate" in x for x in self.check()))
    def test_cargo_pr_owner_mismatch_rejected(self):
        self.case("PR08-CARGO-04")["ownerPr"]="PR-12"
        self.assertTrue(any("cargo ownership drift" in x for x in self.check()))
    def test_releasing_without_review_rejected(self):
        self.p["status"]="QUALIFIED"
        self.assertTrue(any("may not claim review approval" in x for x in self.check()))

if __name__=="__main__":
    unittest.main()
