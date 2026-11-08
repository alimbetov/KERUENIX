#!/usr/bin/env python3
"""Mutations ensure unreviewed Platform/Tenancy S0 expectations cannot silently drift."""
from __future__ import annotations
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("platform_tenancy",ROOT/"scripts/validate_s0_platform_tenancy.py")
assert spec and spec.loader
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class PlatformTenancyS0Tests(unittest.TestCase):
    def setUp(self):
        self.plan=v.read_json(v.DESIGN)
        self.alloc=v.read_json(v.ALLOC)
        self.reg=v.read_json(v.REGISTRY)
        self.ledger=v.read_json(v.LEDGER)
        self.report=(ROOT/v.REPORT).read_text(encoding="utf-8")
    def check(self):
        return v.validate(self.plan,self.alloc,self.reg,self.ledger,self.report)
    def case(self,case_id):
        return next(x for x in self.plan["caseContracts"] if x["id"]==case_id)
    def test_baseline_is_consistent_but_not_approved(self):
        self.assertEqual(self.check(),[])
        self.assertEqual(len(self.plan["caseContracts"]),32)
    def test_removing_a_case_is_detected(self):
        self.plan["caseContracts"].pop()
        self.assertTrue(any("12 FOUND + 20" in x for x in self.check()))
    def test_duplicate_case_is_detected(self):
        self.plan["caseContracts"].append(copy.deepcopy(self.plan["caseContracts"][0]))
        self.assertTrue(any("12 FOUND + 20" in x for x in self.check()))
    def test_foundation_owner_cannot_move(self):
        self.case("FOUND-08")["primaryPr"]="PR-03"
        self.assertTrue(any("foundation primary PR" in x for x in self.check()))
    def test_canonical_outcome_immutable(self):
        self.case("NEG-R0-001")["canonical"]["then"]="ALLOW"
        self.assertTrue(any("canonical GWT modified" in x for x in self.check()))
    def test_critical_impacted_pr_cannot_disappear(self):
        self.case("NEG-R0-005")["impactedPrs"]=["PR-03"]
        self.assertTrue(any("impacted PR coverage changed" in x for x in self.check()))
    def test_br03_remains_pending(self):
        self.case("TDD-SIM-05-G03-01")["proposed"]["legalOrBusinessGates"]=[]
        self.assertTrue(any("pending BR/DEC gates changed" in x for x in self.check()))
    def test_signoff_does_not_automatically_activate_positive(self):
        self.case("TDD-SIM-05-G03-01")["proposed"]["activation"]="ALLOW"
        self.assertTrue(any("fail-closed" in x for x in self.check()))
    def test_no_fake_test_green(self):
        self.case("FOUND-02")["evidenceStatus"]="GREEN"
        self.assertTrue(any("tests executed or approved" in x for x in self.check()))
    def test_no_fake_review(self):
        self.case("NEG-R0-040")["reviewerAuthority"]="stakeholder"
        self.assertTrue(any("fabricated reviewer" in x for x in self.check()))
    def test_missing_persistence_oracle_rejected(self):
        self.case("NEG-R0-005")["proposed"]["assertions"]["persistent"]=""
        self.assertTrue(any("concrete persistent" in x for x in self.check()))
    def test_missing_outbox_oracle_rejected(self):
        self.case("NEG-R0-041")["proposed"]["assertions"]["outboxInbox"]=""
        self.assertTrue(any("concrete outboxInbox" in x for x in self.check()))
    def test_missing_ui_observation_rejected(self):
        self.case("TDD-R0-E2E-09")["proposed"]["assertions"]["httpUi"]=""
        self.assertTrue(any("concrete httpUi" in x for x in self.check()))
    def test_customer_account_writer_requires_adr(self):
        self.case("NEG-R0-007")["proposed"]["caveats"]=[]
        self.assertTrue(any("canonical CustomerAccount owner" in x for x in self.check()))
    def test_same_tenant_customer_scope_guard(self):
        self.case("FOUND-08")["proposed"]["caveats"]=[]
        self.assertTrue(any("account scope" in x for x in self.check()))
    def test_old_signed_url_ttl_is_not_misrepresented(self):
        self.case("NEG-R0-006")["proposed"]["caveats"]=[]
        self.assertTrue(any("signed URL" in x for x in self.check()))
    def test_test_first_method_identifier_required(self):
        self.case("FOUND-10")["proposed"]["testMethodCandidate"]=""
        self.assertTrue(any("test method candidate" in x for x in self.check()))
    def test_no_business_review_from_ci(self):
        self.plan["invariants"]["technicalCiCannotApproveBusinessRules"]=False
        self.assertTrue(any("safety invariant" in x for x in self.check()))
    def test_case_source_gwt_must_match_registry(self):
        self.reg["cases"][next(i for i,x in enumerate(self.reg["cases"]) if x["id"]=="FOUND-03")]["then"]="ALLOW"
        self.assertTrue(any("canonical GWT modified" in x for x in self.check()))
    def test_review_report_must_mention_open_adr(self):
        self.report=self.report.replace("DEC-R0-02","DEC-REMOVED")
        self.assertTrue(any("review report incomplete" in x for x in self.check()))

if __name__=="__main__":
    unittest.main()
