#!/usr/bin/env python3
"""Mutation checks for full S0 design coverage and honest qualification status."""
from __future__ import annotations
import copy,importlib.util,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("fulls0",ROOT/"scripts/validate_s0_full_coverage.py")
assert spec and spec.loader
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class FullS0CoverageMutationTests(unittest.TestCase):
    def setUp(self):
        self.a=m.load(m.ALLOC);self.ext=m.load(m.EXT);self.reg=m.load(m.REG)
        self.road=m.load(m.ROAD);self.ledger=m.load(m.LEDGER)
        self.packs={k:m.load(path) for k,path in m.PACKS.items()}
        self.doc=(ROOT/m.REPORT).read_text(encoding="utf-8")
    def errors(self):
        return m.validate(self.a,self.ext,self.reg,self.road,self.ledger,self.packs,self.doc)
    def row(self,pack,cid):
        rows=self.packs[pack].get("caseContracts",self.packs[pack].get("cases"))
        return next(x for x in rows if x["id"]==cid)
    def test_all_active_cases_have_exactly_one_primary_draft(self):
        self.assertEqual(self.errors(),[])
    def test_missing_execution_primary_detected(self):
        self.packs["execution"]["cases"]=[x for x in self.packs["execution"]["cases"] if x["id"]!="NEG-R0-025"]
        self.assertTrue(any("197 case appearances" in x for x in self.errors()))
    def test_primary_cannot_be_shifted_to_impacted(self):
        self.row("execution","NEG-R0-025")["batchPrimary"]=False
        self.assertTrue(any("exactly one PRIMARY" in x for x in self.errors()))
    def test_double_primary_e2e_detected(self):
        self.row("execution","TDD-R0-E2E-04")["batchPrimary"]=True
        self.assertTrue(any("exactly one PRIMARY" in x for x in self.errors()))
    def test_commercial_owner_rewrite_detected(self):
        self.row("commercial","NEG-R0-009")["canonicalPrimaryPr"]="PR-11"
        self.assertTrue(any("canonical primary owner" in x for x in self.errors()))
    def test_found_12_coverage_required(self):
        self.packs["platform"]["caseContracts"]=[x for x in self.packs["platform"]["caseContracts"] if x["id"]!="FOUND-12"]
        self.assertTrue(any("FOUND-01..12" in x for x in self.errors()))
    def test_sig_18_coverage_required(self):
        self.packs["commercial"]["cases"]=[x for x in self.packs["commercial"]["cases"] if x["id"]!="SIG-18"]
        self.assertTrue(any("SIGNATURE_CANDIDATE" in x for x in self.errors()))
    def test_cargo_local_coverage_required(self):
        self.packs["cargo"]["cases"]=[x for x in self.packs["cargo"]["cases"] if x["id"]!="PR08-CARGO-06"]
        self.assertTrue(any("CARGO_LOCAL_GAP" in x for x in self.errors()))
    def test_cost_local_coverage_required(self):
        self.packs["downstream"]["cases"]=[x for x in self.packs["downstream"]["cases"] if x["id"]!="PR17-COST-04"]
        self.assertTrue(any("COMMERCIAL_COST_LOCAL_GAP" in x for x in self.errors()))
    def test_release_local_coverage_required(self):
        self.packs["reliability"]["cases"]=[x for x in self.packs["reliability"]["cases"] if x["id"]!="PR20-REL-04"]
        self.assertTrue(any("RELEASE_LOCAL_GAP" in x for x in self.errors()))
    def test_payment_absence_cases_required(self):
        self.ext["cases"]=[x for x in self.ext["cases"] if x["caseId"]!="PAY-ABS-06"]
        self.assertTrue(any("NO_PAYMENT_ABSENCE" in x for x in self.errors()))
    def test_governance_cases_required(self):
        self.ext["cases"]=[x for x in self.ext["cases"] if x["caseId"]!="PR00-GOV-02"]
        self.assertTrue(any("GOVERNANCE_LOCAL_GAP" in x for x in self.errors()))
    def test_cannot_reactivate_payment_e2e(self):
        self.a["cases"][next(i for i,x in enumerate(self.a["cases"]) if x["caseId"]=="TDD-R0-E2E-06")]["retired"]=False
        self.assertTrue(any("121 active + 11 retired" in x for x in self.errors()))
    def test_no_auto_s0_qualification(self):
        self.packs["reliability"]["status"]="QUALIFIED"
        self.assertTrue(any("cannot be auto-qualified" in x for x in self.errors()))
    def test_business_approval_not_faked(self):
        self.ledger["decisions"][0]["readiness"]="APPROVED"
        self.assertTrue(any("manual business/legal review" in x for x in self.errors()))
    def test_twenty_safety_decisions_remain_open(self):
        self.assertEqual(len(self.ledger["decisions"]),20)

if __name__=="__main__":
    unittest.main()
