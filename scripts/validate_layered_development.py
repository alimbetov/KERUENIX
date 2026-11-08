#!/usr/bin/env python3
"""Cross-check the 10-layer implementation ТЗ against canonical Roadmap, modules and PR gates."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT="docs/contracts/layered-development-plan.v1.json"
ROADMAP="docs/contracts/tdd-development-roadmap.v1.json"
MODULES="docs/contracts/module-boundaries.v1.json"
ACCEPTANCE="docs/contracts/pr-acceptance-manifest.v1.json"
MARKDOWN="docs/43-layer-by-layer-development-tz.md"

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def validate(plan, roadmap, modules, acceptance, markdown):
    errors=[]
    def error(message):errors.append(message)
    source={p["id"]:p for p in roadmap["r0Prcuts"]}
    layer_ids=[x.get("id") for x in plan.get("layers",[])]
    expected=[f"L{i}" for i in range(10)]
    if plan.get("schemaVersion")!="1.0.0" or plan.get("sourceRoadmapVersion")!=roadmap.get("schemaVersion"):
        error("metadata/roadmap: inconsistent version")
    if layer_ids!=expected or len(layer_ids)!=len(set(layer_ids)):
        error("layers: require L0..L9 exactly once in order")
    if plan.get("stack",{}).get("migrationEngine")!="LIQUIBASE_ONLY":
        error("stack: Liquibase must be only migration engine")
    if plan.get("stack",{}).get("deployment")!="modular-monolith-first":
        error("stack: modular monolith baseline changed")
    boundary=plan.get("boundary",{})
    for k in ("paymentProcessing","internalInvoices","accountsReceivableOrPayable",
              "bankGateways","officialTaxInvoiceIssuance"):
        if boundary.get(k) is not False:
            error(f"product boundary: forbidden {k}")
    if boundary.get("commercialCostOnly") is not True or boundary.get("externalAccountingDocumentReference") is not True:
        error("product boundary: missing commercial-cost-only scope")
    policy=plan.get("evidencePolicy",{})
    for k in ("noPromotionFromDocsOnlyCI","noInferredBusinessSignoff",
              "realDbForRlsConcurrency","uiRequiresE2e","securityDenyUntilVerified",
              "releaseRequiresRestoreProof"):
        if policy.get(k) is not True:
            error(f"quality policy: missing {k}")
    for layer in plan.get("layers",[]):
        lid=layer.get("id","?")
        for key in ("owner","goal","scope"):
            if not layer.get(key):error(f"{lid}: missing {key}")
        for key in ("deliverables","tasks","tests","exit","forbidden"):
            if not isinstance(layer.get(key),list) or not layer[key] or not all(
                    isinstance(x,str) and x.strip() for x in layer[key]):
                error(f"{lid}: missing actionable {key}")
        deps=layer.get("dependsOn",[])
        if len(deps)!=len(set(deps)) or any(d not in expected or d==lid for d in deps):
            error(f"{lid}: invalid layer dependency")
    layer_map={x["id"]:x for x in plan.get("layers",[]) if x.get("id") in expected}
    if len(set(layer_ids))==10:
        temp,done=set(),set()
        def visit(lid):
            if lid in temp:
                error("layers: cyclic dependency")
                return
            if lid in done:return
            temp.add(lid)
            for d in layer_map.get(lid,{}).get("dependsOn",[]):
                visit(d)
            temp.remove(lid);done.add(lid)
        for lid in expected:visit(lid)
    rows=plan.get("prExecutionMatrix",[])
    ids=[r.get("id") for r in rows]
    if len(ids)!=26 or set(ids)!=set(source) or len(ids)!=len(set(ids)):
        error("PR matrix: must cover 26 unique canonical PRs")
    for row in rows:
        pid=row.get("id")
        if pid not in source:continue
        p=source[pid]
        for k,canonical in (("phase",p["phase"]),("canonicalOwner",p["owner"]),
                            ("dependsOnPrs",p["dependsOnPrs"]),
                            ("uiRequired",p["uiAcceptance"]["required"]),
                            ("criticalCaseIds",p["criticalCaseIds"]),
                            ("activationGateMode",p["activationGate"]["mode"]),
                            ("blockingBR",p["activationGate"]["br"])):
            if row.get(k)!=canonical:error(f"{pid}: {k} differs from canonical Roadmap")
        refs=row.get("requiredLayers",[])
        if not isinstance(refs,list) or len(refs)!=len(set(refs)) or any(x not in expected for x in refs):
            error(f"{pid}: invalid requiredLayers")
            continue
        for must in ["L0","L9"]:
            if must not in refs:error(f"{pid}: missing mandatory layer {must}")
        if p["uiAcceptance"]["required"] and "L1" not in refs:
            error(f"{pid}: UI required but L1 missing")
        if not p["uiAcceptance"]["required"] and "L1" in refs:
            error(f"{pid}: non-UI PR may not claim L1 completion")
        if pid!="PR-00" and not {"L6","L8"}.issubset(refs):
            error(f"{pid}: missing persistence/security baseline")
        if pid in ("PR-04","PR-05","PR-07","PR-10","PR-12","PR-13","PR-14","PR-17") and not {"L2","L3","L4"}.issubset(refs):
            error(f"{pid}: missing full backend vertical")
        ev=row.get("minimumEvidence",[])
        for must in ["exact-sha-ci-report","accepted-negative-tests","documented-data-owner"]:
            if must not in ev:error(f"{pid}: missing {must} evidence")
        if p["uiAcceptance"]["required"] and "role-based-ui-e2e" not in ev:
            error(f"{pid}: missing UI E2E evidence")
        if row.get("implementationStatus")!="NOT_QUALIFIED":
            error(f"{pid}: proposed layer TZ cannot upgrade qualification")
    for lid,l in layer_map.items():
        expected_prs=[r["id"] for r in rows if lid in r.get("requiredLayers",[])]
        if l.get("prIds")!=expected_prs:
            error(f"{lid}: layer-to-PR coverage differs from PR matrix")
    module_plans=plan.get("moduleReleasePlan",[])
    module_map={x["id"]:x for x in modules["modules"]}
    if len(module_plans)!=len(module_map) or len({x.get("id") for x in module_plans})!=len(module_map):
        error("modules: all 17 canonical module owners required")
    for m in module_plans:
        old=module_map.get(m.get("id"))
        if old is None or old.get("phase")!=m.get("plannedPhase"):
            error(f"modules: phase/ownership mismatch for {m.get('id')}")
        if m.get("implementationQualification")!="NOT_QUALIFIED":
            error(f"modules: unverified module {m.get('id')} promoted")
    if set(boundary.get("requiredR0Modules",[]))!={x["id"] for x in modules["modules"] if x["phase"]=="R0"}:
        error("modules: R0 list inconsistent with module boundaries")
    wave_rows=plan.get("waves",[])
    if [w.get("id") for w in wave_rows]!=[f"W{i}" for i in range(8)]:
        error("waves: require W0..W7")
    visited=set()
    for w in wave_rows:
        for pid in w.get("prs",[]):
            if pid in visited or pid not in source:
                error(f"waves: duplicate/unknown PR {pid}")
            else:
                for dep in source[pid]["dependsOnPrs"]:
                    if dep not in visited:error(f"waves: {pid} before dependency {dep}")
            visited.add(pid)
        if not w.get("exit"):error(f"waves: missing exit gate for {w.get('id')}")
    if visited!=set(source):error("waves: missing canonical PR")
    gates=plan.get("globalGates",[])
    if [g.get("id") for g in gates]!=[f"G{i:02d}" for i in range(1,9)]:
        error("global gates: require G01..G08")
    for g in gates:
        if not g.get("name") or not g.get("evidence"):
            error(f"global gates: missing evidence {g.get('id')}")
    if [x.get("id") for x in acceptance.get("acceptanceSlices",[])]!=ids:
        error("PR matrix: diverges from 26-PR acceptance manifest order")
    if "43 — KERUENIX" not in markdown:
        error("markdown: expected titled specification")
    for lid in expected:
        if f"### {lid} —" not in markdown:
            error(f"markdown: missing layer {lid}")
    for w in wave_rows:
        if f"| {w.get('id')} —" not in markdown:error(f"markdown: missing wave {w.get('id')}")
    for p in source:
        if f"| {p} |" not in markdown:error(f"markdown: missing PR row {p}")
    return errors

def main():
    errors=validate(load(CONTRACT),load(ROADMAP),load(MODULES),
                    load(ACCEPTANCE),(ROOT/MARKDOWN).read_text(encoding="utf-8"))
    if errors:
        for e in errors:print("ERROR:",e,file=sys.stderr)
        return 1
    print("PASS: 10 layers, 26 PR cuts, 17 canonical modules, 8 ordered waves, 8 global safety gates")
    print("NOTE: this validates specification consistency, NOT implementation, CI correctness or legal signoff")
    return 0

if __name__=="__main__":
    sys.exit(main())
