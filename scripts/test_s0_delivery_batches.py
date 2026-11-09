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


class ResilienceReleaseS0SafetyTests(unittest.TestCase):
    batch="resilience_release"
    def setUp(self):
        cfg=m.BATCHES[self.batch]
        self.plan=m.load(cfg["file"]);self.alloc=m.load(m.ALLOC);self.ext=m.load(m.EXT)
        self.ledger=m.load(m.LEDGER);self.doc=(ROOT/cfg["report"]).read_text(encoding="utf-8")
    def errors(self):
        return m.validate(self.batch,self.plan,self.alloc,self.ext,self.ledger,self.doc)
    def row(self,cid):
        return next(x for x in self.plan["cases"] if x["id"]==cid)
    def test_design_baseline_not_qualified(self):
        self.assertEqual(self.errors(),[])
        self.assertEqual(len(self.plan["cases"]),29)
    def test_loss_of_release_case_detected(self):
        self.plan["cases"].pop()
        self.assertTrue(any("missing/duplicate case" in x for x in self.errors()))
    def test_replay_and_crash_must_be_defined(self):
        self.plan["rules"]["outboxInboxIdempotent"]=False
        self.assertTrue(any("outboxInboxIdempotent" in x for x in self.errors()))
    def test_suspension_never_general_auth(self):
        self.plan["rules"]["suspensionSafetyScopeNotGeneralAuth"]=False
        self.assertTrue(any("suspensionSafetyScopeNotGeneralAuth" in x for x in self.errors()))
    def test_suspension_no_new_booking(self):
        self.plan["rules"]["noBookingDuringSuspension"]=False
        self.assertTrue(any("noBookingDuringSuspension" in x for x in self.errors()))
    def test_custody_durability_essential(self):
        self.plan["rules"]["noLostCustodyOnCrash"]=False
        self.assertTrue(any("noLostCustodyOnCrash" in x for x in self.errors()))
    def test_restore_drill_required(self):
        self.plan["rules"]["restoreDrillRequired"]=False
        self.assertTrue(any("restoreDrillRequired" in x for x in self.errors()))
    def test_release_requires_exact_sha(self):
        self.plan["rules"]["exactShaReleaseEvidence"]=False
        self.assertTrue(any("exactShaReleaseEvidence" in x for x in self.errors()))
    def test_pilot_must_include_two_tenants(self):
        self.plan["rules"]["twoTenantPilotRequired"]=False
        self.assertTrue(any("twoTenantPilotRequired" in x for x in self.errors()))
    def test_cannot_return_payment_scope(self):
        self.plan["rules"]["noPayments"]=False
        self.assertTrue(any("noPayments" in x for x in self.errors()))
    def test_br04_cannot_be_removed(self):
        self.row("TDD-SIM-41-G05-01")["proposal"]["pendingDecisionRefs"]=[]
        self.assertTrue(any("BR/DEC blockers hidden" in x for x in self.errors()))
    def test_pending_binding_cannot_auto_allow(self):
        self.row("TDD-SIM-41-G05-01")["proposal"]["activation"]="ALLOW"
        self.assertTrue(any("unauthorized positive" in x for x in self.errors()))
    def test_immutable_e2e_custody_then(self):
        self.row("TDD-R0-E2E-04")["canonical"]["then"]="ALL_DELIVERED_AFTER_8"
        self.assertTrue(any("canonical Given/When/Then" in x for x in self.errors()))
    def test_release_cannot_fake_signoff(self):
        self.row("PR20-REL-04")["reviewer"]="fake"
        self.assertTrue(any("fabricated reviewer" in x for x in self.errors()))
    def test_release_case_owner(self):
        self.row("PR20-REL-01")["primaryPr"]="PR-18"
        self.assertTrue(any("original module owner" in x for x in self.errors()))
    def test_role_e2e_remains_pr19_owned(self):
        self.row("TDD-R0-E2E-07")["primaryPr"]="PR-18"
        self.assertTrue(any("original module owner" in x for x in self.errors()))
    def test_no_production_qualified_claim(self):
        self.plan["status"]="QUALIFIED"
        self.assertTrue(any("cannot bypass S0" in x for x in self.errors()))

if __name__=="__main__":
    unittest.main()
