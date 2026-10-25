import argparse
import ast
import importlib
import importlib.util
import inspect
import json
from pathlib import Path

import funcprops as fp
from funcprops.verification import _certificate_verifiers

root = Path(fp.__file__).parent
modules = {}
classes = {}
functions = {}
aliases = {}
packages = {}
for path in root.rglob("*.py"):
    parts = path.relative_to(root).with_suffix("").parts
    module = "funcprops" + (
        "." + ".".join(parts[:-1]) if parts[-1] == "__init__" else "." + ".".join(parts)
    )
    tree = ast.parse(path.read_text())
    modules[module] = tree
    imports = {}
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    packages[module] = package
    for n in tree.body:
        if isinstance(n, ast.ImportFrom):
            base = (
                importlib.util.resolve_name("." * n.level + (n.module or ""), package)
                if n.level
                else n.module
            )
            for a in n.names:
                imports[a.asname or a.name] = base + "." + a.name
        if isinstance(n, ast.ClassDef):
            names = {
                a.name
                for a in n.body
                if isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            if (
                "verify" in names
                or "certified" in names
                or "Certificate" in n.name
                or n.name.endswith("Proof")
            ):
                classes[module + "." + n.name] = {
                    "type": module + "." + n.name,
                    "has_verify": "verify" in names,
                    "line": n.lineno,
                    "constructor_sites": [],
                }
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions[module + "." + n.name] = (module, n)
    aliases[module] = imports
registered = {c.__module__ + "." + c.__name__ for c, _ in _certificate_verifiers()}
for c, _ in _certificate_verifiers():
    name = c.__module__ + "." + c.__name__
    classes.setdefault(
        name,
        {
            "type": name,
            "has_verify": hasattr(c, "verify"),
            "line": None,
            "constructor_sites": [],
        },
    )
graph = {}
for name, (module, node) in functions.items():
    calls = set()
    local_imports = {}
    package = packages[module]
    for imported in ast.walk(node):
        if isinstance(imported, ast.ImportFrom):
            base = (
                importlib.util.resolve_name(
                    "." * imported.level + (imported.module or ""), package
                )
                if imported.level
                else imported.module
            )
            for alias in imported.names:
                local_imports[alias.asname or alias.name] = base + "." + alias.name
    for call in ast.walk(node):
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
            target = local_imports.get(
                call.func.id,
                aliases[module].get(call.func.id, module + "." + call.func.id),
            )
            calls.add(target)
            if target in classes:
                classes[target]["constructor_sites"].append(name)
    graph[name] = calls
for name, c in classes.items():
    module_name, _, class_name = name.rpartition(".")
    record_type = getattr(importlib.import_module(module_name), class_name)
    c["has_verify"] = callable(getattr(record_type, "verify", None))
    c["replay_supported"] = name in registered
    c["contract"] = (
        "witness-kernel"
        if name.startswith(
            (
                "funcprops.extrema_bounds.",
                "funcprops.algebraic_coefficients.",
                "funcprops.parameter_geometry.",
                "funcprops.branch_gluing.",
                "funcprops.metric_proofs.",
                "funcprops.real_analysis.regularity_extensions.LipschitzResult",
                "funcprops.seam_regularity.",
                "funcprops.entire_cancellation.",
                "funcprops.real_analysis.variation.VariationResult",
                "funcprops.branch_atlas.",
                "funcprops.implicit_orders.",
                "funcprops.coverage_contract.",
                "funcprops.enclosures.",
                "funcprops.adaptive_roots.",
                "funcprops.complex_clusters.",
                "funcprops.analytic_contours.",
                "funcprops.complex_isolation.",
                "funcprops.complex_newton.",
                "funcprops.complex_multiplicity.",
                "funcprops.complex_cofinal.",
                "funcprops.quotient_isolation.",
                "funcprops.quotient_cofinal.",
                "funcprops.quotient_refinement.",
                "funcprops.shared_zeros.",
                "funcprops.property_contract.",
                "funcprops.infinite_contract.",
                "funcprops.parameter_contract.",
            )
        )
        else "factory-certificate"
    )
    c["replay_mode"] = (
        "theorem-premise-check"
        if c["contract"] == "witness-kernel" and c["replay_supported"]
        else "declared-backend-replay"
        if c["replay_supported"]
        else "unsupported-unified-replay"
    )
    if name.startswith("funcprops.algebraic_complex."):
        c["contract"] = "backend-adapter"
        c["replay_mode"] = (
            "algroots-exact-backend-replay"
            if c["replay_supported"]
            else "unsupported-unified-replay"
        )
    if name == "funcprops.transcendental.complex_roots.ComplexRootIsolationResult":
        c["contract"] = "route-dependent"
        c["replay_mode"] = "bound-native-or-algroots-replay"
    c["exported_names"] = sorted(
        k
        for k in fp.__all__
        if getattr(fp, k).__class__ is type
        and getattr(fp, k).__module__ + "." + getattr(fp, k).__name__ == name
    )


def reaches(name, seen):
    if name in classes:
        return {name}
    if name in seen:
        return set()
    seen.add(name)
    out = set()
    for target in graph.get(name, ()):
        out.update(reaches(target, seen))
    return out


apis = []
for name in sorted(n for n in vars(fp) if not n.startswith("_")):
    obj = getattr(fp, name)
    if inspect.isfunction(obj):
        f = inspect.unwrap(obj)
        target = f.__module__ + "." + f.__name__
        reachable = reaches(target, set())
        if reachable:
            apis.append(
                {
                    "api": name,
                    "implementation": target,
                    "possible_record_types": sorted(reachable),
                }
            )
manifest = {
    "inventory_version": 1,
    "description": "Approximate static call graph of exported functions reaching proof-record constructors. Ordinary/unknown returns remain possible. Factory-based replay is distinct from independent witness checking. SymPy and arithmetic backends remain trusted.",
    "records": sorted(classes.values(), key=lambda c: c["type"]),
    "public_entrypoints": apis,
}
parser = argparse.ArgumentParser(description="Generate the proof contract inventory")
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
text = json.dumps(manifest, indent=2) + "\n"
path = root / "data/proof_api_manifest.json"
if args.check:
    if path.read_text() != text:
        raise SystemExit("stale proof inventory; run tools/update_proof_inventory.py")
else:
    path.write_text(text)
print(
    json.dumps(
        {
            "records": len(classes),
            "registered_replay_types": len(registered),
            "public_entrypoints": len(apis),
        }
    )
)
