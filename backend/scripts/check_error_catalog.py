#!/usr/bin/env python3
"""Fail CI when the public RFC9457 error code catalog drifts from Java enum."""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
CATALOG = ROOT / "docs/contracts/api-error-catalog.v1.json"
ENUM = ROOT / "backend/src/main/java/kz/keruenix/platform/errors/ErrorCode.java"

catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
java = ENUM.read_text(encoding="utf-8")
matches = re.findall(r'^\s+([A-Z_]+)\("([A-Z0-9-]+)",\s*HttpStatus\.([A-Z_]+),', java, re.M)
if len(matches) != len(set(x[0] for x in matches)):
    sys.exit("ERROR: duplicate Java enum names")
if len(matches) != len(set(x[1] for x in matches)):
    sys.exit("ERROR: duplicate Java API error codes")
expected = {e["enumName"]: (e["code"], e["httpStatus"]) for e in catalog["errorCodes"]}
if len(expected) != len(catalog["errorCodes"]):
    sys.exit("ERROR: duplicate catalog enum names")
if len({e["code"] for e in catalog["errorCodes"]}) != len(expected):
    sys.exit("ERROR: duplicate machine error codes")

# Numbering convention matches HTTP class; 000 is the explicit framework catch-all.
http_status_names = {
    "BAD_REQUEST": 400, "UNAUTHORIZED": 401, "FORBIDDEN": 403, "NOT_FOUND": 404,
    "METHOD_NOT_ALLOWED": 405, "CONFLICT": 409, "UNSUPPORTED_MEDIA_TYPE": 415,
    "UNPROCESSABLE_ENTITY": 422, "TOO_MANY_REQUESTS": 429,
    "INTERNAL_SERVER_ERROR": 500, "SERVICE_UNAVAILABLE": 503,
}
actual = {}
for name, code, http_constant in matches:
    status = http_status_names.get(http_constant)
    if status is None:
        sys.exit(f"ERROR: unrecognized HttpStatus {http_constant}")
    actual[name] = (code, status)
    embedded = code.split("-")[2]
    if embedded != "000" and int(embedded) != status:
        sys.exit(f"ERROR: encoded HTTP status mismatch: {name}: {code} / {status}")

if expected != actual:
    sys.exit(f"ERROR: Java and JSON error code catalog drift\nJava: {actual}\nCatalog: {expected}")
for e in catalog["errorCodes"]:
    if e["problemType"] != "urn:keruenix:problem:" + e["code"]:
        sys.exit("ERROR: RFC9457 problemType mismatch for " + e["enumName"])
if "RESOURCE_HIDDEN" in expected:
    sys.exit("ERROR: protected resource code would reveal resource existence")

print(f"PASS: {len(actual)} unique error codes and HTTP mappings match the contract.")
