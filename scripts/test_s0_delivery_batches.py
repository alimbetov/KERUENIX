#!/usr/bin/env python3
"""Mutation tests of S0 deliverable plans, never business behavior execution."""
from __future__ import annotations
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("s0del",ROOT/"scripts/validate_s0_delivery_batches.py")
assert spec and spec.loader
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ExecutionS0SafetyTests(unittest.TestCase):
    batch="execution_custody_pod"
    def setUp(self):
        cfg=m.BATCHES[self.batch]
        self.plan=m.load(cfg["file"])
        self.allocation=m.load(m.ALLOC)
        self.ext=m.load(m.EXT)
        self.ledger=m.load(m.LEDGER)
        self.doc=(ROOT/cfg["report"]).read_text(encoding="utf-8")
    def errors(self):
        return m.validate(self.batch,self.plan,self.allocation,self.ext,self.ledger,self.doc)
    def row(self,cid):
        return next(x for x in self.plan["cases"] if x["id"]==cid)
    def test_consistent_unapproved_design(self):
        self.assertEqual(self.errors(),[])
    def test_missing_case(self):
        self.plan["cases"].pop(0)
        self.assertTrue(any("missing/duplicate" in x for x in self.errors()))
    def test_duplicate_case(self):
        self.plan["cases"].append(copy.deepcopy(self.plan["cases"][0]))
        self.assertTrue(any("missing/duplicate" in x for x in self.errors()))
    def test_original_partial_pod_conservation_then_cannot_change(self):
        self.row("TDD-SIM-28-G18-01")["canonical"]["then"]="ALL_DELIVERED"
        self.assertTrue(any("canonical Given/When/Then" in x for x in self.errors()))
    def test_custody_wrong_primary_owner(self):
        self.row("NEG-R0-025")["primaryPr"]="PR-14"
        self.assertTrue(any("original module owner" in x for x in self.errors()))
    def test_cross_role_e2e_remains_pr19_owned(self):
        self.row("TDD-R0-E2E-04")["primaryPr"]="PR-13"
        self.assertTrue(any("original module owner" in x for x in self.errors()))
    def test_hidden_br10_rejected(self):
        self.row("NEG-R0-030")["proposal"]["pendingDecisionRefs"]=[]
        self.assertTrue(any("BR/DEC blockers hidden" in x for x in self.errors()))
    def test_approval_with_pending_br_denied(self):
        self.row("TDD-SIM-24-G15-01")["proposal"]["activation"]="ALLOW"
        self.assertTrue(any("unauthorized positive activation" in x for x in self.errors()))
    def test_missing_db_oracle(self):
        self.row("NEG-R0-026")["proposal"]["dbOracle"]=""
        self.assertTrue(any("missing observable dbOracle" in x for x in self.errors()))
    def test_missing_outbox_oracle(self):
        self.row("TDD-SIM-28-G18-03")["proposal"]["eventOracle"]=""
        self.assertTrue(any("missing observable eventOracle" in x for x in self.errors()))
    def test_missing_ui_oracle(self):
        self.row("TDD-R0-E2E-07")["proposal"]["httpUiOracle"]=""
        self.assertTrue(any("missing observable httpUiOracle" in x for x in self.errors()))
    def test_negative_variants_mandatory(self):
        self.row("TDD-SIM-28-G18-01")["proposal"]["negativeVariants"]=[]
        self.assertTrue(any("negative/failure variants" in x for x in self.errors()))
    def test_actor_steps_mandatory(self):
        self.row("NEG-R0-025")["proposal"]["whenSteps"]=[]
        self.assertTrue(any("missing actionable steps" in x for x in self.errors()))
    def test_claiming_green_is_false(self):
        self.row("NEG-R0-030")["testStatus"]="GREEN"
        self.assertTrue(any("cannot claim Test Review" in x for x in self.errors()))
    def test_fabricated_signoff_rejected(self):
        self.row("NEG-R0-029")["reviewer"]="fake"
        self.assertTrue(any("fabricated reviewer" in x for x in self.errors()))
    def test_partial_not_completed_guard(self):
        self.plan["rules"]["partialPodNotCompleted"]=False
        self.assertTrue(any("partialPodNotCompleted" in x for x in self.errors()))
    def test_no_duplicate_custody_guard(self):
        self.plan["rules"]["custodyOwnerNeverAmbiguous"]=False
        self.assertTrue(any("custodyOwnerNeverAmbiguous" in x for x in self.errors()))
    def test_no_payment_guard(self):
        self.plan["rules"]["noPayments"]=False
        self.assertTrue(any("noPayments" in x for x in self.errors()))
    def test_review_cannot_be_issued_by_ci(self):
        self.plan["status"]="QUALIFIED"
        self.assertTrue(any("cannot bypass S0" in x for x in self.errors()))


class DownstreamS0SafetyTests(unittest.TestCase):
    batch="tracking_documents_cost"
    def setUp(self):
        cfg=m.BATCHES[self.batch]
        self.plan=m.load(cfg["file"]);self.alloc=m.load(m.ALLOC);self.ext=m.load(m.EXT)
        self.ledger=m.load(m.LEDGER);self.doc=(ROOT/cfg["report"]).read_text(encoding="utf-8")
    def errors(self):
        return m.validate(self.batch,self.plan,self.alloc,self.ext,self.ledger,self.doc)
    def row(self,id):
        return next(x for x in self.plan["cases"] if x["id"]==id)
    def test_design_is_not_approved(self):
        self.assertEqual(self.errors(),[])
        self.assertEqual(len(self.plan["cases"]),17)
    def test_stale_booking_must_not_confirm(self):
        self.row("NEG-R0-044")["canonical"]["then"]="CONFIRMED"
        self.assertTrue(any("canonical Given/When/Then" in x for x in self.errors()))
    def test_tracking_cannot_lose_tenant_scope(self):
        self.plan["rules"]["tenantAccountTrackingScope"]=False
        self.assertTrue(any("tenantAccountTrackingScope" in x for x in self.errors()))
    def test_signed_url_ttl_must_remain_explicit(self):
        self.plan["rules"]["signedUrlTtlExplicit"]=False
        self.assertTrue(any("signedUrlTtlExplicit" in x for x in self.errors()))
    def test_private_review_requires_verified_completion(self):
        self.plan["rules"]["reviewOnlyAfterVerifiedComplete"]=False
        self.assertTrue(any("reviewOnlyAfterVerifiedComplete" in x for x in self.errors()))
    def test_cost_cannot_become_payment(self):
        self.plan["rules"]["noPayments"]=False
        self.assertTrue(any("noPayments" in x for x in self.errors()))
    def test_immutable_pod_original_protected(self):
        self.plan["rules"]["originalProofImmutable"]=False
        self.assertTrue(any("originalProofImmutable" in x for x in self.errors()))
    def test_cost_case_original_owner_cannot_change(self):
        self.row("PR17-COST-01")["primaryPr"]="PR-16"
        self.assertTrue(any("original module owner" in x for x in self.errors()))
    def test_original_e2e_ownership_stays_pr19(self):
        self.row("TDD-R0-E2E-04")["primaryPr"]="PR-16"
        self.assertTrue(any("original module owner" in x for x in self.errors()))
    def test_pending_review_not_approved(self):
        self.row("NEG-R0-048")["status"]="QUALIFIED"
        self.assertTrue(any("cannot claim Test Review" in x for x in self.errors()))
    def test_no_fake_evidence(self):
        self.row("PR17-COST-03")["evidence"]="passed"
        self.assertTrue(any("fabricated reviewer" in x for x in self.errors()))
    def test_failure_and_replay_variants_required(self):
        self.row("NEG-R0-032")["proposal"]["negativeVariants"]=[]
        self.assertTrue(any("negative/failure variants" in x for x in self.errors()))

if __name__=="__main__":
    unittest.main()
