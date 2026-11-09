#!/usr/bin/env python3
"""Adversarial mutations of the PR acceptance manifest gate."""
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "pr_acceptance",ROOT/"scripts/validate_pr_acceptance.py")
assert spec is not None and spec.loader is not None
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class PrAcceptanceManifestMutationTests(unittest.TestCase):
    def setUp(self):
        self.man=module.load(module.MANIFEST)
        self.road=module.load(module.ROADMAP)
        self.br=module.load(module.BR)
        self.dec=module.load(module.DEC)

    def audit(self):
        return module.validate(self.man,self.road,self.br,self.dec)

    def row(self,pid):
        return next(x for x in self.man["acceptanceSlices"] if x["id"]==pid)

    def test_current_manifest_passes_as_not_qualified(self):
        self.assertEqual(self.audit(),[])
        self.assertTrue(all(x["qualificationStatus"]=="NOT_QUALIFIED"
                            for x in self.man["acceptanceSlices"]))

    def test_missing_pr_cannot_be_hidden(self):
        self.man["acceptanceSlices"]=[x for x in self.man["acceptanceSlices"]
                                      if x["id"]!="PR-14"]
        self.assertTrue(any("exactly 26" in e for e in self.audit()))

    def test_duplicate_pr_is_rejected(self):
        self.man["acceptanceSlices"].append(copy.deepcopy(self.row("PR-01")))
        self.assertTrue(any("duplicate PR" in e for e in self.audit()))

    def test_wrong_canonical_owner_is_rejected(self):
        self.row("PR-07")["canonicalOwner"]="tenancy"
        self.assertTrue(any("PR-07: canonicalOwner" in e for e in self.audit()))

    def test_wrong_pr_dependency_is_rejected(self):
        self.row("PR-12")["dependsOnPrs"]=[]
        self.assertTrue(any("PR-12: dependsOnPrs" in e for e in self.audit()))

    def test_critical_case_cannot_be_dropped(self):
        self.row("PR-12")["criticalCaseIds"]=[]
        self.assertTrue(any("PR-12: criticalCaseIds" in e for e in self.audit()))

    def test_business_gate_cannot_be_dropped(self):
        self.row("PR-07")["brRefs"]=[]
        self.assertTrue(any("PR-07: brRefs" in e for e in self.audit()))

    def test_ui_requirement_cannot_be_hidden(self):
        self.row("PR-19")["uiRequired"]=False
        self.assertTrue(any("PR-19: uiRequired" in e for e in self.audit()))

    def test_pr01_partial_green_cannot_be_qualified(self):
        self.row("PR-01")["qualificationStatus"]="QUALIFIED"
        self.assertTrue(any("PR-01: QUALIFIED requires" in e for e in self.audit()))

    def test_pr00_document_ci_cannot_be_qualified(self):
        self.row("PR-00")["qualificationStatus"]="QUALIFIED"
        self.assertTrue(any("documentation evidence" in e for e in self.audit()))

    def test_fabricated_qualified_pr_with_no_real_signoff_fails(self):
        p=self.row("PR-07")
        p["qualificationStatus"]="QUALIFIED"
        p["verification"]["level"]="FULL_ACCEPTANCE_VERIFIED"
        self.assertTrue(any("PR-07: QUALIFIED with pending approvals" in e
                            for e in self.audit()))

    def test_missing_ci_evidence_fails(self):
        self.row("PR-01")["verification"]["ciRuns"]=[]
        self.assertTrue(any("PR-01: CI runs" in e for e in self.audit()))

    def test_wrong_sha_is_rejected(self):
        self.row("PR-01")["verification"]["verifiedSha"]="HEAD"
        self.assertTrue(any("exact 40-hex" in e for e in self.audit()))

    def test_forged_verified_test_path_is_rejected(self):
        self.row("PR-01")["verification"]["testRefs"]=["tests/imaginary-file.py"]
        self.assertTrue(any("actual test source files" in e for e in self.audit()))

    def test_payment_product_scope_change_is_rejected(self):
        self.man["semantics"]["noPayments"]=False
        self.assertTrue(any("no-payments" in e for e in self.audit()))

if __name__=="__main__":
    unittest.main()
