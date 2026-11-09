#!/usr/bin/env python3
"""Adversarial mutations of the S0 132-case allocation matrix."""
from __future__ import annotations
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("allocation",ROOT/"scripts/validate_s0_scenario_allocation.py")
assert spec and spec.loader
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class ScenarioAllocationMutationTests(unittest.TestCase):
    def setUp(self):
        self.matrix=v.load(v.MATRIX)
        self.bank=v.load(v.BANK)
        self.negative=v.load(v.NEGATIVE)
        self.roadmap=v.load(v.ROADMAP)
        self.ledger=v.load(v.LEDGER)

    def check(self):
        return v.validate(self.matrix,self.bank,self.negative,self.roadmap,self.ledger)

    def case(self,cid):
        return next(x for x in self.matrix["cases"] if x["caseId"]==cid)

    def pr(self,pid):
        return next(x for x in self.matrix["prMatrix"] if x["prId"]==pid)

    def test_initial_allocation_is_conservative_not_approved(self):
        self.assertEqual(self.check(),[])
        self.assertEqual(sum(not x["retired"] for x in self.matrix["cases"]),121)

    def test_missing_case_detected(self):
        self.matrix["cases"].pop(3)
        self.assertTrue(any("132 canonical" in x for x in self.check()))

    def test_duplicate_case_detected(self):
        self.matrix["cases"].append(copy.deepcopy(self.matrix["cases"][0]))
        self.assertTrue(any("132 canonical" in x for x in self.check()))

    def test_wrong_group_detected(self):
        self.case("NEG-R0-001")["group"]="E2E"
        self.assertTrue(any("group differs" in x for x in self.check()))

    def test_payment_positive_reintroduced_detected(self):
        self.case("NEG-R0-033")["retired"]=False
        self.assertTrue(any("payment/out-of-scope" in x for x in self.check()))

    def test_retired_case_can_never_have_primary_owner(self):
        self.case("TDD-R0-E2E-06")["primaryPr"]="PR-17"
        self.assertTrue(any("retired payment case" in x for x in self.check()))

    def test_owner_mismatch_detected(self):
        self.case("NEG-R0-001")["primaryOwner"]="finance"
        self.assertTrue(any("primary owner" in x for x in self.check()))

    def test_unknown_primary_pr_detected(self):
        self.case("NEG-R0-001")["primaryPr"]="PR-99"
        self.assertTrue(any("lacks canonical primary" in x for x in self.check()))

    def test_original_critical_anchor_cannot_be_erased(self):
        self.case("NEG-R0-017")["originalRoadmapCriticalPrs"]=[]
        self.assertTrue(any("critical case anchors altered" in x for x in self.check()))

    def test_critical_pr_not_removed_from_affected_prs(self):
        self.case("NEG-R0-017")["impactedPrs"]=["PR-10"]
        self.assertTrue(any("critical anchor" in x for x in self.check()))

    def test_case_cannot_claim_test_review_completed(self):
        self.case("NEG-R0-001")["reviewStatus"]="APPROVED"
        self.assertTrue(any("cannot fabricate reviewer" in x for x in self.check()))

    def test_case_cannot_claim_green_or_approved_oracle(self):
        self.case("NEG-R0-001")["expected"]["oracleStatus"]="APPROVED"
        self.assertTrue(any("proposal incorrectly promoted" in x for x in self.check()))

    def test_original_gwt_cannot_be_silently_changed(self):
        self.case("NEG-R0-001")["expected"]["canonicalThen"]="ALLOW"
        self.assertTrue(any("canonical GWT oracle changed" in x for x in self.check()))

    def test_oracle_missing_is_rejected(self):
        self.case("NEG-R0-017")["expected"]["dbOracle"]=""
        self.assertTrue(any("dbOracle missing" in x for x in self.check()))

    def test_decision_dependency_cannot_be_dropped(self):
        x=self.case("TDD-SIM-13-G01-01")
        x["businessDecisionRefs"]=[]
        self.assertTrue(any("canonical BR dependency removed" in e for e in self.check()))

    def test_pending_blocker_cannot_be_hidden(self):
        self.case("TDD-SIM-13-G01-01")["blockingPendingDecisionRefs"]=[]
        self.assertTrue(any("missing pending decision blocker" in e for e in self.check()))

    def test_missing_gwt_cannot_be_pretended_complete(self):
        self.case("TDD-R0-E2E-01")["gwtMissing"]=[]
        self.assertTrue(any("missing-GWT status" in e for e in self.check()))

    def test_pr_owner_cannot_be_rewritten(self):
        self.pr("PR-08")["canonicalOwner"]="tenancy"
        self.assertTrue(any("roadmap owner/phase drift" in e for e in self.check()))

    def test_no_primary_case_gap_must_remain_visible(self):
        self.pr("PR-08")["gaps"]=[]
        self.assertTrue(any("unmapped primary gap hidden" in e for e in self.check()))

    def test_doc_pr_cannot_claim_cases_not_present(self):
        self.pr("PR-00")["impactedCaseIds"]=["NEG-R0-001"]
        self.assertTrue(any("impacted scenario coverage" in e for e in self.check()))

    def test_summary_cannot_fake_full_gwt(self):
        self.matrix["counts"]["missingGwt"]=0
        self.assertTrue(any("gap counts" in e for e in self.check()))

    def test_no_payments_scope_must_not_change(self):
        self.matrix["scope"]="PAYMENTS_IN_R1"
        self.assertTrue(any("NO PAYMENTS" in e for e in self.check()))

    def test_no_human_signoff_claimed_from_documentation(self):
        self.matrix["decisionReadiness"]["noHumanSignoffFabricated"]=False
        self.assertTrue(any("signoff" in e for e in self.check()))

    def test_review_stage_remains_open(self):
        self.matrix["status"]="S0_APPROVED"
        self.assertTrue(any("cannot assert review approval" in e for e in self.check()))

if __name__=="__main__":
    unittest.main()
