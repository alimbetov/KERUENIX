#!/usr/bin/env python3
"""Negative mutations prevent layer-by-layer ТЗ drift and fake qualification."""
from __future__ import annotations
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("layers",ROOT/"scripts/validate_layered_development.py")
assert spec and spec.loader
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class LayeredDevelopmentContractTests(unittest.TestCase):
    def setUp(self):
        self.plan=v.load(v.CONTRACT)
        self.road=v.load(v.ROADMAP)
        self.modules=v.load(v.MODULES)
        self.manifest=v.load(v.ACCEPTANCE)
        self.markdown=(ROOT/v.MARKDOWN).read_text(encoding="utf-8")

    def errors(self):
        return v.validate(self.plan,self.road,self.modules,self.manifest,self.markdown)

    def pr(self,pid):
        return next(x for x in self.plan["prExecutionMatrix"] if x["id"]==pid)

    def layer(self,lid):
        return next(x for x in self.plan["layers"] if x["id"]==lid)

    def test_current_consistency(self):
        self.assertEqual(self.errors(),[])

    def test_removed_layer(self):
        self.plan["layers"].pop()
        self.assertTrue(any("require L0..L9" in x for x in self.errors()))

    def test_duplicate_pr(self):
        self.plan["prExecutionMatrix"].append(copy.deepcopy(self.pr("PR-01")))
        self.assertTrue(any("26 unique" in x for x in self.errors()))

    def test_missing_ui_requirement(self):
        self.pr("PR-04")["requiredLayers"].remove("L1")
        self.assertTrue(any("PR-04: UI required" in x for x in self.errors()))

    def test_missing_security_scope(self):
        self.pr("PR-12")["requiredLayers"].remove("L8")
        self.assertTrue(any("PR-12: missing persistence/security" in x for x in self.errors()))

    def test_missing_owner(self):
        self.pr("PR-13")["canonicalOwner"]="commercial"
        self.assertTrue(any("PR-13: canonicalOwner" in x for x in self.errors()))

    def test_missing_negative_cases(self):
        self.pr("PR-14")["criticalCaseIds"]=[]
        self.assertTrue(any("PR-14: criticalCaseIds" in x for x in self.errors()))

    def test_dropped_business_blocker(self):
        self.pr("PR-07")["blockingBR"]=[]
        self.assertTrue(any("PR-07: blockingBR" in x for x in self.errors()))

    def test_fake_qualification(self):
        self.pr("PR-01")["implementationStatus"]="QUALIFIED"
        self.assertTrue(any("cannot upgrade qualification" in x for x in self.errors()))

    def test_flyway_reintroduced(self):
        self.plan["stack"]["migrationEngine"]="FLYWAY"
        self.assertTrue(any("Liquibase must be only" in x for x in self.errors()))

    def test_payment_activation(self):
        self.plan["boundary"]["bankGateways"]=True
        self.assertTrue(any("forbidden bankGateways" in x for x in self.errors()))

    def test_future_module_unplanned_activation(self):
        self.plan["moduleReleasePlan"][-1]["plannedPhase"]="R0"
        self.assertTrue(any("phase/ownership mismatch" in x for x in self.errors()))

    def test_future_module_false_green(self):
        self.plan["moduleReleasePlan"][-1]["implementationQualification"]="QUALIFIED"
        self.assertTrue(any("unverified module" in x for x in self.errors()))

    def test_pr_dependency_order_violated(self):
        self.plan["waves"][1]["prs"]=["PR-03","PR-02","PR-03C"]
        self.assertTrue(any("before dependency" in x for x in self.errors()))

    def test_acceptance_manifest_must_correspond(self):
        self.manifest["acceptanceSlices"].reverse()
        self.assertTrue(any("diverges" in x for x in self.errors()))

    def test_deleting_layer_tests_rejected(self):
        self.layer("L6")["tests"]=[]
        self.assertTrue(any("L6: missing actionable tests" in x for x in self.errors()))

    def test_layer_cycle_rejected(self):
        self.layer("L0")["dependsOn"]=["L1"]
        self.assertTrue(any("cyclic dependency" in x for x in self.errors()))

    def test_critical_gate_missing(self):
        self.plan["globalGates"].pop()
        self.assertTrue(any("G01..G08" in x for x in self.errors()))

    def test_readiness_cannot_be_disabled(self):
        self.plan["evidencePolicy"]["noInferredBusinessSignoff"]=False
        self.assertTrue(any("noInferredBusinessSignoff" in x for x in self.errors()))

    def test_markdown_layer_parity(self):
        self.markdown=self.markdown.replace("### L5 —","### Missing —",1)
        self.assertTrue(any("missing layer L5" in x for x in self.errors()))

if __name__=="__main__":
    unittest.main()
