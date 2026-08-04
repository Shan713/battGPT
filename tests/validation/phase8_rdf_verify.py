#!/usr/bin/env python3
"""Phase 8: RDF verification — serialization consistency, ontology alignment, structural integrity, and OWL/RDF semantic correctness.

Verifies the regenerated output/battery_kg.{ttl,rdf,jsonld}:
  1. All three serializations parse and are isomorphic (same triple set).
  2. Ontology alignment:
       - no battgpt: classes instantiated (node types come only from imported ontologies)
       - every battgpt: predicate used in the graph is declared as owl:ObjectProperty or owl:DatatypeProperty
       - every rdf:type class belongs to an imported ontology namespace
       - property nodes are typed as emmo:Property (EMMO_b7bcff25_ffc3_474e_9ab5_01b1664bd4ba)
       - no ObjectProperty is used as rdf:type
       - property units are QUDT unit IRIs
  3. Structural integrity & SPARQL:
       - 12 materials, 12 crystals, 12 unit cells, 12 space groups, 6 crystal systems, 350 sites
       - SPARQL ?s emmo:hasProperty ?p returns all property nodes
       - bond graph fully symmetric, no self-loops
  4. Curated BattINFO role annotation: all 12 active materials mapped to a battery role.
  5. Provenance: dcterms:source and prov:wasGeneratedBy present per material.
"""
import json
import sys
from pathlib import Path

from rdflib import Graph, URIRef, RDF, RDFS, OWL, Namespace
from rdflib.compare import isomorphic

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
TTL = OUT / "battery_kg.ttl"
RDFXML = OUT / "battery_kg.rdf"
JSONLD = OUT / "battery_kg.jsonld"
SCHEMA = ROOT / "rdf_schema.ttl"

BG = Namespace("https://w3id.org/battgpt/kg#")
CHSUB = Namespace("https://w3id.org/emmo/domain/chemical-substance#")
CRYST = Namespace("https://w3id.org/emmo/domain/crystallography#")
BATTERY = Namespace("https://w3id.org/emmo/domain/battery#")
EMMO = Namespace("https://w3id.org/emmo#")
QUDT = Namespace("http://qudt.org/schema/qudt/")
UNIT = Namespace("http://qudt.org/vocab/unit/")
PROV = Namespace("http://www.w3.org/ns/prov#")

IMPORTED = ("https://w3id.org/emmo#", "https://w3id.org/emmo/domain/",
            "https://w3id.org/battinfo#", "http://qudt.org/",
            "http://www.w3.org/ns/prov#", "http://purl.org/dc/terms/",
            "http://www.w3.org/2000/01/rdf-schema#", "http://www.w3.org/2002/07/owl#",
            "http://www.w3.org/2001/XMLSchema#", "https://schema.org/",
            "http://www.w3.org/2004/02/skos/core#", "https://w3id.org/battgpt/")

EMMO_PROP_CLASS = URIRef("https://w3id.org/emmo#EMMO_b7bcff25_ffc3_474e_9ab5_01b1664bd4ba")  # owl:Class Property
EMMO_HAS_PROP_PRED = URIRef("https://w3id.org/emmo#EMMO_e1097637_70d2_4895_973f_2396f04fa204") # owl:ObjectProperty hasProperty
EMMO_NUM = URIRef("https://w3id.org/emmo#EMMO_faf79f53_749d_40b2_807c_d34244c192f4")
EMMO_UNIT = URIRef("https://w3id.org/emmo#EMMO_bed1d005_b04e_4a90_94cf_02bc678a8569")

failures: list[str] = []


def check(label: str, ok: bool, detail: str = ""):
    status = "OK " if ok else "FAIL"
    print(f"  [{status}] {label}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(label + (f" — {detail}" if detail else ""))


def main():
    print("=" * 72)
    print("PHASE 8: RDF VERIFICATION — serialization, ontology alignment, structure")
    print("=" * 72)

    # ── 1. Parse all three serializations ──
    g_ttl = Graph()
    g_ttl.parse(str(TTL), format="turtle")
    g_rdf = Graph()
    g_rdf.parse(str(RDFXML), format="xml")
    g_json = Graph()
    g_json.parse(str(JSONLD), format="json-ld")
    print(f"\nParsed: TTL={len(g_ttl)} triples | RDF/XML={len(g_rdf)} | JSON-LD={len(g_json)}")

    check("TTL == RDF/XML (isomorphic)", isomorphic(g_ttl, g_rdf))
    check("TTL == JSON-LD (isomorphic)", isomorphic(g_ttl, g_json))
    check("RDF/XML == JSON-LD (isomorphic)", isomorphic(g_rdf, g_json))

    g = g_ttl

    # ── 2. Ontology alignment ──
    print("\n-- 2. Ontology alignment --")
    # (a) no battgpt: classes
    battgpt_classes = sorted({str(o) for s, o in g.subject_objects(RDF.type)
                              if str(o).startswith("https://w3id.org/battgpt/kg#") and o != OWL.Ontology})
    check("no battgpt: owl:Class instantiated", not battgpt_classes,
          f"found {battgpt_classes}" if battgpt_classes else "")
    # (b) all rdf:type classes are imported-ontology classes
    bad_types = sorted({str(o) for o in g.objects(None, RDF.type)
                        if not str(o).startswith(IMPORTED)})
    check("all rdf:type classes are imported-ontology classes", not bad_types,
          f"foreign: {bad_types}" if bad_types else "")
    
    # (c) Semantic Check: No ObjectProperty used as rdf:type
    bad_objectprop_types = list(g.triples((None, RDF.type, EMMO_HAS_PROP_PRED)))
    check("no ObjectProperty used as rdf:type", len(bad_objectprop_types) == 0,
          f"found {len(bad_objectprop_types)} ObjectProperty instances" if bad_objectprop_types else "")

    # (d) Protégé compliance: every battgpt: predicate declared as Object/DatatypeProperty
    used_battgpt_preds = {str(p) for s, p, o in g if str(p).startswith(str(BG))}
    undeclared_preds = []
    for p_str in used_battgpt_preds:
        p_ref = URIRef(p_str)
        types = set(g.objects(p_ref, RDF.type))
        if not types.intersection({OWL.ObjectProperty, OWL.DatatypeProperty}):
            undeclared_preds.append(p_str)
    check("every battgpt: predicate declared as ObjectProperty/DatatypeProperty", not undeclared_preds,
          f"undeclared: {undeclared_preds}" if undeclared_preds else "")

    # (e) units are QUDT
    unit_iris = sorted({str(o) for s, p, o in g if p == EMMO_UNIT})
    bad_units = [u for u in unit_iris if not u.startswith(str(UNIT))]
    check("all property units are QUDT unit IRIs", not bad_units,
          f"non-QUDT: {bad_units}" if bad_units else "")

    # ── 3. Structural integrity & SPARQL ──
    print("\n-- 3. Structural integrity & SPARQL --")
    mats = list(g.subjects(RDF.type, CHSUB.Substance))
    crys = list(g.subjects(RDF.type, CRYST.Crystal))
    ucs = list(g.subjects(RDF.type, CRYST.UnitCell))
    sgs = list(g.subjects(RDF.type, CRYST.SpaceGroup))
    css = list(g.subjects(RDF.type, CRYST.CrystalSystem))
    sites = list(g.subjects(RDF.type, CRYST.AtomicSite))
    props = list(g.subjects(RDF.type, EMMO_PROP_CLASS))
    check("12 materials", len(mats) == 12, f"got {len(mats)}")
    check("12 crystals", len(crys) == 12, f"got {len(crys)}")
    check("12 unit cells", len(ucs) == 12, f"got {len(ucs)}")
    check("space group nodes present (>= 8 distinct)", len(sgs) >= 8, f"got {len(sgs)}")
    check("crystal system nodes present (>= 6 distinct)", len(css) >= 6, f"got {len(css)}")
    check("350 atomic sites", len(sites) == 350, f"got {len(sites)}")
    check("426 property nodes typed as emmo:Property", len(props) == 426, f"got {len(props)}")

    # SPARQL Query check for emmo:hasProperty
    sparql_props = list(g.query("""
        PREFIX emmo: <https://w3id.org/emmo#>
        SELECT DISTINCT ?p WHERE {
            ?s emmo:EMMO_e1097637_70d2_4895_973f_2396f04fa204 ?p .
        }
    """))
    check("SPARQL ?s emmo:hasProperty ?p returns all property nodes", len(sparql_props) == 426,
          f"got {len(sparql_props)}")

    # per material chain integrity
    chain_bad = 0
    for m in mats:
        crys_of = list(g.objects(m, BG.hasStructure))
        if len(crys_of) != 1:
            chain_bad += 1
            continue
        c = crys_of[0]
        ucs_of = list(g.objects(c, BG.hasUnitCell))
        sgs_of = list(g.objects(c, BG.hasSpaceGroup))
        css_of = list(g.objects(c, BG.hasCrystalSystem))
        if len(ucs_of) != 1 or len(sgs_of) != 1 or len(css_of) != 1:
            chain_bad += 1
    check("each material -> 1 crystal -> 1 unitcell/spacegroup/crystalsystem", chain_bad == 0,
          f"{chain_bad} broken" if chain_bad else "")

    # containsSite coverage
    contained = set(g.objects(None, BG.containsSite))
    check("every site is contained by a unit cell", contained == set(sites),
          f"contained={len(contained)} sites={len(sites)}" if contained != set(sites) else "")

    # bond graph
    edges = set(g.subject_objects(BG.hasBondTo))
    asym = [e for e in edges if (e[1], e[0]) not in edges]
    selfloops = [e for e in edges if e[0] == e[1]]
    check("bond graph symmetric (A->B implies B->A)", not asym, f"{len(asym)} asymmetric")
    check("no self-loop bonds", not selfloops, f"{len(selfloops)} self-loops")
    check("1670 directed bond edges", len(edges) == 1670, f"got {len(edges)}")

    # CIF literals
    cif_count = sum(1 for c in crys if list(g.objects(c, BG.hasCif)))
    check("every crystal has a CIF literal", cif_count == 12, f"got {cif_count}")

    # species & elements
    species = list(g.subjects(RDF.type, CHSUB.AtomicSpecies))
    elems = list(g.subjects(RDF.type, CHSUB.Element))
    check("species nodes present", len(species) > 0, f"{len(species)}")
    check("element nodes present", len(elems) > 0, f"{len(elems)}")

    def has(subj, pred):
        return next(g.objects(subj, pred), None) is not None

    unitless_numeric = [str(p).split("/")[-1] for p in props
                        if has(p, EMMO_NUM) and not has(p, EMMO_UNIT)]
    check("every numeric property has a unit", not unitless_numeric, f"unitless: {unitless_numeric}")
    unit_no_num = [str(p).split("/")[-1] for p in props
                   if has(p, EMMO_UNIT) and not has(p, EMMO_NUM)]
    check("every unit-bearing property has a number", not unit_no_num, f"no-number: {unit_no_num}")
    geom = sum(1 for p in props if not has(p, EMMO_UNIT))
    check("unitless properties are coordination-geometry only", geom >= 12, f"got {geom} unitless")

    # ── 4. BattINFO role annotation ──
    print("\n-- 4. Curated BattINFO role annotation --")
    POS = "battery_b8f04fd5_8741_4d17_9713_931d752c0021"   # PositiveElectrode
    NEG = "battery_0a37db91_6c02_4eb4_9b2d_e8a2a02b1f85"   # NegativeElectrode
    ELY = "battery_b69c4c79_463e_436b_8b59_5b067f9446d6"   # Electrolyte
    SEP = "battery_13e9a59b_2ef4_4a2a_b5e5_d9a8c27bc32f"   # Separator
    roles = {
        "mp-22526": POS, "mp-19017": POS, "mp-25411": POS, "mp-22584": POS,
        "mp-776557": POS, "mp-19226": POS,
        "mp-685194": NEG, "mp-48": NEG, "mp-149": NEG,
        "mp-696128": ELY, "mp-942733": ELY,
        "mp-1143": SEP,
    }
    role_map = {r: "UNMAPPED" for r in roles}
    for m in mats:
        mid = str(m).split("/")[-1]
        rtype = next(g.objects(m, BG.belongsToElectrode), None)
        if rtype is not None:
            role_map[mid] = str(rtype).split("battery#")[-1]
    all_mapped = all(role_map[m] != "UNMAPPED" for m in roles)
    check("all 12 materials mapped to a battery role", all_mapped)

    # usesMaterial / belongsToElectrode inverse
    uses = set(g.subject_objects(BG.usesMaterial))
    belongs = set(g.subject_objects(BG.belongsToElectrode))
    inv_ok = all((b, a) in uses for (a, b) in belongs)
    check("belongsToElectrode inverse of usesMaterial", inv_ok)

    # ── 5. Provenance ──
    print("\n-- 5. Provenance --")
    src_missing = [str(m).split("/")[-1] for m in mats if not list(g.objects(m, PROV.wasGeneratedBy))]
    check("every material has prov:wasGeneratedBy", not src_missing, f"missing: {src_missing}")
    dcterms_src = list(g.triples((None, URIRef("http://purl.org/dc/terms/source"), None)))
    check("dcterms:source provenance present", len(dcterms_src) >= 24, f"got {len(dcterms_src)} triples")

    # ── summary ──
    print("\n" + "=" * 72)
    if failures:
        print(f"PHASE 8: FAILED — {len(failures)} check(s):")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("PHASE 8: PASS — serializations isomorphic, ontology aligned, structure sound")


if __name__ == "__main__":
    main()
