#!/usr/bin/env python3
"""Mutation tests for the roadmap validator; not Java or business qualification."""
from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "roadmap_validator", ROOT / "scripts/validate_tdd_roadmap.py"
)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


class RoadmapValidatorMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.roadmap = load("docs/contracts/tdd-development-roadmap.v1.json")
        base = load("docs/contracts/r0-tdd-scenarios.v1.json")
        neg = load("docs/contracts/r0-negative-scenarios.v1.json")
        access = load("docs/contracts/access-policy-matrix.v2.json")
        cls.case_ids = {
            item["id"] for item in (
                base["blockerCases"] + base["r0SafetyCases"]
                + base["crossRoleCases"] + neg["cases"]
            )
        }
        cls.permissions = {p["id"]: p["permission"] for p in access["entries"]}
        cls.br_ids = set(cls.roadmap["blockedUntilSignoff"])
        cls.markdown = (ROOT / "docs/33-tdd-development-roadmap-v1.md").read_text(
            encoding="utf-8"
        )

    def check_risk(self, road: dict) -> list[str]:
        return module.audit_v16_pr_contract(
            road, self.case_ids, self.permissions, self.br_ids
        )

    def test_current_contract_has_no_v16_risk_errors(self) -> None:
        self.assertEqual([], self.check_risk(self.roadmap))

    def test_unknown_critical_case_fails(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-04")[
            "criticalCaseIds"
        ].append("NEG-R0-999")
        self.assertTrue(any("unknown critical case" in p for p in self.check_risk(road)))

    def test_rfq_submit_cannot_be_silently_enabled(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-05")[
            "activationGate"
        ]["mode"] = "POLICY_SCOPED"
        self.assertTrue(any("PR-05 submit" in p for p in self.check_risk(road)))

    def test_required_ui_cannot_be_skipped(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-13")[
            "uiAcceptance"
        ]["required"] = False
        self.assertTrue(any("PR-13: missing mandatory role-UI" in p
                            for p in self.check_risk(road)))

    def test_customer_owner_cannot_silently_swap(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(d for d in road["domainOwnershipDecisions"]
             if d["resource"] == "CustomerAccount")["canonicalWriter"] = "tenancy"
        self.assertTrue(any("CustomerAccount owner/grant split" in p
                            for p in self.check_risk(road)))

    def test_payment_mechanisms_cannot_be_silently_enabled(self) -> None:
        road = copy.deepcopy(self.roadmap)
        road["financeBoundaryGate"]["paymentMechanismsEnabled"] = True
        self.assertTrue(any("Payment mechanisms must remain EXCLUDED" in p
                            for p in self.check_risk(road)))

    def test_current_markdown_pr_dag_matches_machine(self) -> None:
        self.assertEqual([], module.audit_v16_markdown_pr_table(
            self.roadmap, self.markdown
        ))

    def test_commercial_account_onboarding_requires_role_ui(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-03C")[
            "uiAcceptance"
        ]["required"] = False
        self.assertTrue(any("PR-03C" in p for p in self.check_risk(road)))

    def test_removed_bank_pr_cannot_be_restored_as_dependency(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-19")[
            "dependsOnPrs"
        ].append("PR-17S")
        self.assertTrue(any("Removed PR-17S" in p for p in self.check_risk(road)))

    def test_suffixed_commercial_account_pr_dependency_is_checked(self) -> None:
        q = chr(96)
        original = f"| {q}PR-03{q} | {q}RD-02{q} | {q}tenancy{q} | {q}PR-03C{q} |"
        changed = self.markdown.replace(
            original,
            f"| {q}PR-03{q} | {q}RD-02{q} | {q}tenancy{q} | {q}PR-02{q} |",
            1
        )
        self.assertNotEqual(changed, self.markdown)
        self.assertTrue(any("PR-03: Markdown prerequisites differ" in p
                            for p in module.audit_v16_markdown_pr_table(
                                self.roadmap, changed
                            )))

    def test_fleet_registry_cannot_claim_confirmed_capacity(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-10V")[
            "outcome"
        ] = "Registry and full Booking CONFIRMED"
        self.assertTrue(any("PR-10V Fleet registry" in p for p in self.check_risk(road)))

    def test_cancel_command_must_have_br11(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-12C")[
            "activationGate"
        ]["br"] = []
        self.assertTrue(any("PR-12C cancellation" in p for p in self.check_risk(road)))

    def test_private_review_cannot_become_public_reputation(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-16R")[
            "outcome"
        ] = "Public marketplace rating"
        self.assertTrue(any("PR-16R must remain" in p for p in self.check_risk(road)))

    def test_e2e_must_qualify_cancellation_and_review(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-19")[
            "dependsOnPrs"
        ].remove("PR-12C")
        self.assertTrue(any("PR-19 R0 E2E" in p for p in self.check_risk(road)))

    def test_advance_invoice_cannot_be_blocked_by_blanket_pod_dependency(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-17")[
            "dependsOnPrs"
        ].append("PR-16")
        self.assertTrue(any("PR-17 must not depend on bank/payment/official invoice" in p for p in self.check_risk(road)))

    def test_decision_approval_requires_real_reviewer_evidence(self) -> None:
        doc = module.load("docs/contracts/r0-delivery-contract.v1.json")
        decision = next(d for d in doc["decisions"] if d["id"] == "DEC-R0-01")
        decision["status"] = "APPROVED"
        self.assertTrue(any("DEC-R0-01: APPROVED without" in error
                            for error in module.audit_v16_delivery_approvals(doc)))

    def test_decision_approval_with_evidence_can_be_recorded(self) -> None:
        doc = module.load("docs/contracts/r0-delivery-contract.v1.json")
        decision = next(d for d in doc["decisions"] if d["id"] == "DEC-R0-01")
        decision.update(status="APPROVED", approvalEvidenceRef="restricted://adr/1",
                        approverAuthorityRef="role:approved-decision-owner",
                        approvedVersion="1", approvedAtUtc="2026-11-08T09:00:00Z")
        self.assertFalse(module.audit_v16_delivery_approvals(doc))

    def test_eds_signing_must_gate_quote_acceptance(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-07")[
            "dependsOnPrs"
        ].remove("PR-06S")
        self.assertTrue(any("Signed Quote must depend" in p
                            for p in self.check_risk(road)))

    def test_eds_signer_has_no_integration_shortcut(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-06S")[
            "outcome"
        ] = "Sign arbitrary document without verification"
        self.assertTrue(any("Signed Quote must depend" in p
                            for p in self.check_risk(road)))

    def test_cost_reporting_must_not_implement_payments(self) -> None:
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-17")[
            "testGate"
        ] = "Payment settlement success"
        self.assertTrue(any("PR-17 must be commercial margin report" in p
                            for p in self.check_risk(road)))

    def current_scope(self, road=None, access=None, sign=None, cases=None, negatives=None):
        return module.audit_v16_current_product_scope(
            road or self.roadmap,
            access or load("docs/contracts/access-policy-matrix.v2.json"),
            sign or load("docs/contracts/r0-scope-eds-signing.v1.json"),
            cases or load("docs/contracts/r0-tdd-scenarios.v1.json"),
            negatives or load("docs/contracts/r0-negative-scenarios.v1.json")
        )

    def test_no_payments_and_eds_current_scope_passes(self):
        self.assertEqual(self.current_scope(), [])

    def test_payment_permission_reactivation_is_rejected(self):
        access = load("docs/contracts/access-policy-matrix.v2.json")
        next(x for x in access["entries"] if x["id"] == "FIN-03")["decision"] = "DENY_UNLESS_ALL_GUARDS_PASS"
        self.assertTrue(any("FIN-03 payment permission" in x for x in self.current_scope(access=access)))

    def test_bank_legacy_case_cannot_become_r0_gate(self):
        cases = load("docs/contracts/r0-tdd-scenarios.v1.json")
        next(x for x in cases["crossRoleCases"] if x["id"] == "TDD-R0-E2E-06")["r0Applicability"] = "APPLICABLE_APPROVED"
        self.assertTrue(any("Payment test TDD-R0-E2E-06" in x for x in self.current_scope(cases=cases)))

    def test_carrier_commitment_cannot_bypass_verified_signing(self):
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["r0Prcuts"] if p["id"] == "PR-11")["dependsOnPrs"].remove("PR-06S")
        self.assertTrue(any("PR-11 binding carrier" in x for x in self.current_scope(road=road)))

    def test_cost_phase_must_not_wait_for_full_delivery(self):
        road = copy.deepcopy(self.roadmap)
        next(p for p in road["phases"] if p["id"] == "RD-09")["dependsOn"].append("RD-08")
        self.assertTrue(any("RD-09 commercial costing" in x for x in self.current_scope(road=road)))

    def test_signature_legal_ux_and_authority_extensions_are_required(self):
        signed = load("docs/contracts/r0-scope-eds-signing.v1.json")
        signed["signing"]["tests"].remove("SIG-15")
        self.assertTrue(any("SIG-01..18" in x for x in self.current_scope(sign=signed)))

    def test_wrong_markdown_pr_prerequisite_fails(self) -> None:
        q = chr(96)
        changed = self.markdown.replace(
            f"| {q}PR-05{q} | {q}RD-03{q} | {q}commercial{q} | {q}PR-04{q} |",
            f"| {q}PR-05{q} | {q}RD-03{q} | {q}commercial{q} | {q}PR-01{q} |",
            1,
        )
        self.assertNotEqual(changed, self.markdown)
        self.assertTrue(any("PR-05: Markdown prerequisites differ" in p
                            for p in module.audit_v16_markdown_pr_table(
                                self.roadmap, changed
                            )))


if __name__ == "__main__":
    unittest.main()
