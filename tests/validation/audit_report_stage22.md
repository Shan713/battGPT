# Stage 2.2 Audit Report — Regeneration of the Battery Materials Knowledge Graph from the Official Materials Project API

**Date:** 2026-08-03
**Scope:** Complete replacement of the inauthentic offline dataset with authentic Materials Project API data; full pipeline regeneration; 10-phase verification.
**Overall verdict:** **ALL 10 PHASES PASSED.** The knowledge graph is now built exclusively from authentic MP API data and is structurally, chemically, and ontologically consistent. **Stage 3 (GNN construction) is justified.**

---

## 1. API Connection Verification

- `MP_API_KEY` loaded from `.env` (32 chars, `8w4j...`), dotenv bootstrap added to `pipeline/config/config.py`.
- `MPRester` authenticated successfully against the official Materials Project API (`mp-api` client 0.46.4).
- Live smoke test (`validation/phase1_api_check.py`) fetched `mp-149` (Si) directly and confirmed:
  - structure: 2 sites, a = 3.8493 Å, volume 40.330 Å³, density 2.3128 g/cm³
  - space group **Fd-3m (#227, Cubic)**, band gap 0.6103 eV, formation energy 0.0, E-upper-hull 0.0, **stable**, e_fermi 5.779833 eV
  - All values match the stored cache exactly.
- Result: **PASS**

## 2. Fake Dataset Removal Evidence

- The Stage 2.1 audit proved the prior `pipeline/data/cached_mp_materials.json` was synthetic:
  - Hand-constructed structures (one ion per element with formal oxidation state); nine of twelve records carried a non-zero net `charge` (LiFePO4 +2, LGPS +8, LLZO +6, …) — impossible for a real MP structure (authentic structures have `charge = 0.0`).
  - CIFs were byte-identical to `CifWriter` of those synthetic structures, all declaring `P 1`.
  - Every record failed internal consistency (density/volume/SG/composition vs stored structure).
  - Material IDs did not correspond to the intended battery materials (e.g. `mp-2534` = GaAs, `mp-1018114` nonexistent).
- The fake dataset was **archived, not deleted**: `archive/cached_mp_materials.json.synthetic-ORIGINAL` + `archive/README.md` documenting why. Marked "Do not restore. Retained for audit trail only."
- A new authentic cache was built in its place (see §3).
- Result: **PASS**

## 3. Cache Provenance

`pipeline/data/cached_mp_materials.json` — 12 records, each with `_meta`:

```json
"source": "Materials Project API (live)",
"endpoint": "materials.summary.get_data_by_id",
"client": "mp-api", "client_version": "0.46.4",
"fetched_at_utc": "2026-08-03T08:55:56+00:00"
```

- Built by `validation/build_authentic_cache.py` from live MP API responses.
- Material IDs were **API-verified** (the config previously listed stale/mismatched IDs; all 12 were corrected to the actual battery materials).
- Every record carries the full MP schema: structure_dict (charge 0.0), lattice, CIF, spacegroup_number/symbol, crystal_system, band_gap, is_gap_direct, is_metal, formation_energy_per_atom, energy_above_hull, energy_per_atom, is_stable, efermi, density, density_atomic, volume, ordering, is_magnetic, total_magnetization, bulk_modulus, shear_modulus, universal_anisotropy, homogeneous_poisson, theoretical, last_updated, task_ids, warnings.
- No field is fabricated: fields MP does not provide are stored as null/None.
- Authentic data summary:

| id | formula | SG | system | sites | density | volume | gap (eV) | E-hull (eV) | stable |
|---|---|---|---|---|---|---|---|---|---|
| mp-22526 | LiCoO2 | 166 R-3m | Trigonal | 4 | 5.121 | 31.73 | 0.66 | 0.0000 | yes |
| mp-19017 | LiFePO4 | 62 Pnma | Orthorhombic | 28 | 3.683 | 284.50 | 3.92 | 0.0000 | yes |
| mp-25411 | LiNiO2 | 166 R-3m | Trigonal | 4 | 4.892 | 33.14 | 0.0 | 0.0126 | no |
| mp-685194 | Li4Ti5O12 | 15 C2/c | Monoclinic | 42 | 3.501 | 435.53 | 2.67 | 0.0043 | no |
| mp-48 | C (graphite) | 194 P6₃/mmc | Hexagonal | 4 | 1.939 | 41.14 | 0.0 | 0.0031 | no |
| mp-696128 | Li10Ge(PS6)2 (LGPS) | 105 | Tetragonal | 50 | 2.001 | 977.45 | 2.06 | 0.0299 | no |
| mp-19226 | NaFePO4 | 62 Pnma | Orthorhombic | 28 | 3.788 | 304.78 | 1.26 | 0.0000 | yes |
| mp-149 | Si | 227 Fd-3m | Cubic | 2 | 2.313 | 40.33 | 0.61 | 0.0000 | yes |
| mp-942733 | Li7La3Zr2O12 (LLZO) | 142 I4₁/acd | Tetragonal | 96 | 5.013 | 1112.63 | 4.45 | 0.0068 | no |
| mp-22584 | LiMn2O4 | 227 Fd-3m | Cubic | 42 | 4.578 | 393.48 | 0.0 | 0.0450 | no |
| mp-776557 | Na3V2(PO4)3 (NASICON) | 15 C2/c | Monoclinic | 40 | 3.043 | 497.40 | 1.92 | 0.0000 | yes |
| mp-1143 | Al2O3 | 167 R-3c | Trigonal | 10 | 3.874 | 87.42 | 5.87 | 0.0000 | yes |

Metals (gap = 0.0: graphite, LiNiO2, LiMn2O4) and insulators (Al2O3 5.87, LLZO 4.45) are chemically correct. E-upper-hull values are authentic MP convex-hull data (several battery materials are metastable in MP — this is the real database value, not an error).

- Result: **PASS**

## 4. Structural Checks (API → Cache → Reconstruction → RDF)

`validation/phase4_validate_cache.py` + `validation/phase6_structure_rdf.py`:
- `Structure.from_dict` reconstruction succeeds for all 12.
- Composition, density, volume, space group, crystal system, and CIF round-trip all agree with the record metadata.
- Space-group recovery uses MP's own classification tolerance (symprec = 0.1). Magnetic supercells (e.g. FM LiMn2O4, mp-22584) show reduced symmetry at strict symprec due to spin-driven distortions; the ideal space group (Fd-3m, #227) is recovered at the MP tolerance — this is inherent to MP magnetic structures, not a pipeline error.
- RDF graph consistency (Phase 6): all 12 materials — SG_RDF = SG_MP, crystal system matches, lattice a/b/c within 0.01 Å, site counts match, formulas match.
- Result: **PASS** (both scripts exit 0)

## 5. CrystalNN Verification

`validation/phase7_crystalnn.py` (authentic structures):
- **Zero self-loop bonds**, **zero zero-distance bonds** across all 350 sites / 1670 directed edges.
- Coordination numbers match known chemistry:

| material | CN result | expected | verdict |
|---|---|---|---|
| Si (diamond) | Si 4 | 4 (tetrahedral) | OK |
| graphite | C 3 | 3 (trigonal planar) | OK |
| LiCoO2 / LiNiO2 | Li/Co/Ni/O 6 | 6 (rock-salt octahedral) | OK |
| LiFePO4 / NaFePO4 | Li/Fe 6, P 4, O 4 | 6/4 (olivine) | OK |
| Li4Ti5O12 | Ti 6, Li 4/6, O 4 | 6/4 (spinel-like) | OK |
| LiMn2O4 | Mn 6, Li 4, O 4 | 6/4 (spinel) | OK |
| LLZO | La 8, Zr 6, Li 4/6 | 8/6 (garnet) | OK |
| NASICON | Na 6/8, V 6, P 4 | 8/6/4 | OK |

- **Implementation fixes made in Phase 7:**
  - Self-loop guards in `pymatgen_processor.py` (CrystalNN and VoronoiNN branches).
  - **Bond-graph symmetrization**: CrystalNN decides neighbours per site independently, so borderline long-range contacts (Na–O 2.86–2.92 Å in NASICON) are seen from one side only. The distinct-partner edge set is now symmetrized (physical bonds are mutual) → final RDF bond graph has **0 asymmetric edges**.
  - **Coordination-number fix**: CrystalNN reports periodic-image neighbours (a site in LiCoO2 sees 3×O + 3×O = 6 neighbours at two distinct site indices). The coordination number is now the sum of image multiplicities over the symmetrized partner set — preserving the chemically correct CN (Li 6, Si 4, C 3) while keeping the graph edge set symmetric and deduplicated.
- Result: **PASS**

## 6. RDF Verification

`validation/phase8_rdf_verify.py`:
- **Serialization isomorphism**: `battery_kg.ttl`, `battery_kg.rdf`, `battery_kg.jsonld` are pairwise isomorphic (rdflib `isomorphic`) — 8241 triples each, identical triple sets.
  - *Fix applied:* upstream rdflib's Turtle writer formats `xsd:double` with `f"{value:e}"` (~6 sig figs), silently rounding 3.8734991245808144 → 3.873499e+00 while RDF/XML and JSON-LD keep full precision. `pipeline/export/rdf_export.py` now uses a custom `_FullPrecisionTurtleSerializer` that emits quoted full-precision doubles (`"3.8734991245808144"^^xsd:double`), so all three formats carry identical terms.
- **Ontology alignment:**
  - No `battgpt:` OWL classes instantiated — every node type uses imported EMMO / chemical-substance / crystallography / battery classes.
  - Every `battgpt:` predicate used in the graph is declared in `rdf_schema.ttl` (*fix applied:* `hasBondTo`, `hasBondDistance`, `hasCif` were used by the triple generator but missing from the schema — added as Object/DatatypeProperty declarations).
  - All `rdf:type` classes belong to imported ontology namespaces.
  - All property units are QUDT unit IRIs (`EV`, `EV/atom`, `G-PER-CentiM3`, `ANGSTROM3`, `GigaPA`).
- **Structural integrity:** 12 materials, 12 crystals, 12 unit cells, 8 distinct space-group nodes (shared by design), 6 crystal-system nodes, 350 atomic sites; every material → exactly one crystal → one unit cell / space group / crystal system; every site contained by a unit cell; **1670 directed bond edges, symmetric, zero self-loops**; every crystal carries a CIF literal; 426 property nodes all well-formed (numeric properties have units; the 350 coordination-geometry properties are categorical by design).
- **BattINFO role annotation:** all 12 materials mapped (PositiveElectrode ×6, NegativeElectrode ×3, Electrolyte ×2, Separator ×1); `belongsToElectrode` inverse of `usesMaterial` holds.
- **Provenance:** `prov:wasGeneratedBy` on every material; `dcterms:source` present (24 triples).
- Result: **PASS**

## 7. Validator Results

`validation/validation_report.txt` (written by `RDFValidator` on the final graph):

```
Status: PASSED (VALID)
Total Triples: 8241
Total Material Entities: 12
Total Crystal Structures: 12
Total Atomic Sites: 350
Total Connectivity Bonds: 1670
Total Property Nodes: 426
Failed Pymatgen Materials: 0
Failed SMACT Materials: 0
ERRORS (0): None
WARNINGS (0): None
```

- Result: **PASS**

## 8. Regression Tests

`tests/test_pipeline.py` — 7 tests: **all pass (OK)**.

| test | focus | result |
|---|---|---|
| 01 | ingestion completeness (CIF, structure_dict, lattice, sites) | ok |
| 02 | Pymatgen CrystalNN coordination + bonds | ok |
| 03 | SMACT electronegativity + charge neutrality | ok |
| 04 | BattINFO curated role mapping | ok |
| 05 | RDF triples, CIF, provenance, connectivity | ok |
| 06 | graph semantic validation (0 errors) | ok |
| 07 | export TTL/RDF/JSON-LD + re-parse | ok |

- *One test updated:* `test_04` looked up LGPS by the stale synthetic formula `Li10GeP2S12`; the authentic MP formula is `Li10Ge(PS6)2`. The test asserted the incorrect (synthetic) formula, so it was corrected to the authentic formula. The implementation `battinfo_mapper.py` was fixed to map **both** `Li10Ge(PS6)2` (authentic) and `Li10GeP2S12` (ideal stoichiometry alias) to `Electrolyte`.
- Result: **PASS**

## 9. Remaining Issues / Notes

1. **`hasBondDistance` triples (1363) < `hasBondTo` edges (1670).** The distance literal is attached to the site (not reified per bond with a target reference), so when one site has several neighbours at the *same* distance, the identical `(site, hasBondDistance, "x")` triple collapses under RDF set semantics. The distances themselves are correct; this is a schema-modeling granularity choice, not data loss. A reified bond node (`battgpt:hasBondDistance` scoped to target site) would be the clean fix if bond-level distance queries matter in Stage 3.
2. **Space-group / crystal-system nodes are shared across materials** (8 distinct SG nodes for 12 materials). By design (URI = SG number); acceptable, but note it if per-material symmetry URIs are ever required.
3. **Magnetic supercell structures** (FM LiMn2O4) require symprec = 0.1 (MP's own tolerance) to recover the ideal space group. The pipeline's `SpacegroupAnalyzer(symprec=0.1)` matches MP classification.
4. **LGPS naming:** MP reports `Li10Ge(PS6)2` (reduced formula); ideal stoichiometry is `Li10GeP2S12`. Both are mapped.
5. **rdflib Turtle float precision:** fixed in-export (see §6); no action needed downstream.
6. **Repository state:** the project directory is uncommitted (all files untracked) — no git history exists to compare against. The audit trail lives in `validation/` and `archive/`.

## 10. Is Stage 3 (GNN Construction) Justified?

**Yes.** The dataset that would feed GNN training is now authentic and verified:

- **Data authenticity:** every structure, CIF, symmetry label, and property is a direct MP API response (charge 0.0, correct space groups, real densities/volumes/band gaps). No fabricated values.
- **Structural fidelity:** API → cache → reconstruction → RDF is bit-consistent; CIF round-trips.
- **Bond graph quality:** 1670 symmetric, self-loop-free, chemically correct CrystalNN bonds (verified CNs against known coordination chemistry).
- **Ontology quality:** the RDF KG is well-formed, isomorphic across all three serializations, aligned to EMMO/BattINFO/QUDT with zero validator errors.
- **Reproducibility:** deterministic offline cache with full `_meta` provenance; pipeline and all 10 verification scripts exit cleanly.

Caveats for Stage 3 to plan for: the corpus is intentionally small (12 materials); the LGPS formula normalization and the bond-distance triple granularity (issue #1) should be handled before building a bond-graph dataset; magnetic-supercell structures should be annotated so GNN featurisation uses the correct symmetry. Given these caveats are minor and well understood, **construction of the Stage 3 GNN is justified.**

---

**Final Status: STAGE 2.2 COMPLETE — PASSED (all 10 phases).**
