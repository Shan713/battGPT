# BattGPT Ontology — Constraint & Semantics Audit

**Audited file:** `battgpt.ttl` (the actual file on disk — not `rdf_schema_refined.ttl`, which does not exist in this repository; not any previously-claimed "483-triple" state, which also does not match this file)
**Method:** every number below is extracted programmatically from `battgpt.ttl` via `rdflib`, cross-checked against the imported EMMO/BattINFO snapshots in `imports/`, and against external crystallographic literature where flagged. Nothing here is recalled from memory of earlier conversation turns without re-verification against the file as it exists right now.
**Status:** **§18's three changes have been applied and validated** (2026-09-09). Backup taken as `battgpt.ttl.backup_20260909_220403`; exact diff in `battgpt_change_report_20260909.diff`. Post-application: triple count 941→989 (+48, matching the expected delta exactly); ROBOT+ELK on the full merged closure still shows exactly 1 pre-existing unsatisfiable class (`CentiMetreSecondDegreeCelsius`), zero new ones; ROBOT+HermiT confirmation on the applied file is running (see final status below). All three intended new subsumptions verified present in the graph (`GarnetStructure`/`PerovskiteStructure ⊑ OxideStructureFamily` with `StructureFamily` still transitively implied; `BatteryCell`'s new `hasRole` restriction present). `git status` confirms only `battgpt.ttl` was modified — no UML file (`.drawio`/`.pdf`) or unrelated content touched.

---

## 1. Executive Summary

`battgpt.ttl` is a **moderately axiomatized** extension ontology (not a bare taxonomy, not a heavily-constrained ontology): it declares 31 local classes and 29 local object properties, of which 16 already carry `owl:someValuesFrom` restrictions expressing real necessary conditions, plus two derived properties via `owl:propertyChainAxiom`. It reuses EMMO/BattINFO classes as domain/range wherever a suitable one exists, and introduces new local classes only for the two confirmed gaps (crystallographic detail, structure-family taxonomy) that EMMO's own closure does not cover.

Two previous drafts of an audit prompt handed to this session asserted a "current validated state" (triple count 483, an intentional `owl:inverseOf` between `belongsToElectrode`/`usesMaterial`, prior corrections to `chsub:Substance`/`chsub:Element`, prior corrections to `BulkModulusProperty`/`ShearModulusProperty` superclasses) that **do not match this file**. Per Rule 2, every one of those specific claims is verified below as **NOT PRESENT IN CURRENT FILE**, and none has been recreated.

Three genuinely new findings came out of this pass that hadn't surfaced before:
1. A real class-hierarchy gap: `GarnetStructure` and `PerovskiteStructure` are both oxide-framework structures by `OxideStructureFamily`'s own stated definition, yet neither is placed under it.
2. `hasIonicConductivity`'s bearer class (`BatteryCell`) is scientifically questionable — ionic conductivity is conventionally an intrinsic electrolyte-material property, not a cell-aggregate one, and the property's own comment already flags this ambiguity.
3. The `BatteryCell → BatteryRole` connection candidate axiom, and the `StructureFamily → SpaceGroup` candidate axioms, were both test-fitted into a disposable copy of the ontology and run through ROBOT+ELK: **zero new unsatisfiable classes** were introduced by either. (HermiT confirmation on the same disposable copy was started and is noted as pending/completed in §16.)

---

## 2. Exact Current Ontology Statistics

Extracted via `rdflib.Graph().parse('battgpt.ttl')`:

| Metric | Count |
|---|---|
| Total triples | **941** |
| `owl:imports` | 5 (`battinfo`, `emmo`, `emmo/domain/battery`, `emmo/domain/chemical-substance`, `emmo/domain/electrochemistry`) |
| Classes declared in `battgpt:` namespace | **31** |
| Object properties declared in `battgpt:` namespace | **29** |
| Datatype properties declared in `battgpt:` namespace | **30** |
| Annotation properties declared | 3 (`skos:closeMatch`, `skos:definition`, `dcterms:isVersionOf`) |
| Named individuals (`battgpt:`) | **21** |
| `rdfs:subClassOf` (named class → named class) | 31 |
| `rdfs:subClassOf` (named class → blank-node restriction) | 15 restriction axioms, across 8 subject classes |
| `owl:Restriction` instances | **16**, all `someValuesFrom` — zero `allValuesFrom`, zero cardinality of any kind |
| `owl:propertyChainAxiom` | 2 (`hasBondTo` ← `hasBond∘hasTargetSite`; `hasCrystalSystem` ← `hasSpaceGroup∘belongsToCrystalSystem`) |
| Property characteristics (Functional/InverseFunctional/Transitive/Symmetric/Asymmetric/Reflexive/Irreflexive) | **all zero** |
| `owl:inverseOf` | **zero** |
| `owl:unionOf` | 1 (`belongsToElectrode`'s range) |
| `owl:intersectionOf` | 0 |
| `owl:equivalentClass` | 0 |
| `owl:disjointWith` (pairwise) | 0 |
| `owl:AllDisjointClasses` blocks | 3 (9-way structure-family leaves; 4-way BatteryRole subclasses; 3-way structure-family mid-tier) |
| `owl:AllDifferent` blocks | 3 (matching individual sets for the above) |

---

## 3. Class Hierarchy Audit (Rule 3)

| Class | Current parent(s) | Semantic assessment | Problem? | Recommended action |
|---|---|---|---|---|
| `CrystalStructure`, `Site`, `UnitCell`, `Species`, `CrystalBond` | `owl:Thing` | Standalone local roots. Justified in the file's own comments: EMMO's `domain-crystallography` is an unimported WIP v0.1.0 draft, so no upstream class cleanly fits. | No | DO NOT CHANGE |
| `SpaceGroup`, `CrystalSystem`, `CoordinationGeometry`, `StructureFamily` | `emmo:Property` (`EMMO_b7bcff25...`) | Debatable fit — these are *classification categories*, not measurable quantities the way `BandGapProperty`/`BulkModulusProperty` are. Flagged in an earlier session pass too. | Possible | REQUIRES HUMAN/SCIENTIFIC DECISION (re-anchoring under `owl:Thing` like the crystallography-local classes is defensible, but changes 4 classes' ancestor and would need re-verification) |
| `OxideStructureFamily`, `PolyanionStructureFamily`, `SulfideStructureFamily` | `StructureFamily` | Correct, clean taxonomy split by anion-framework chemistry. | No | DO NOT CHANGE |
| `LayeredOxideStructure`, `RockSaltStructure`, `SpinelStructure` | `OxideStructureFamily` | Correct — all are oxide-anion-sublattice structures matching the parent's definition. | No | DO NOT CHANGE |
| `NASICONStructure`, `OlivineStructure` | `PolyanionStructureFamily` | Correct — both built from discrete PO₄ polyanion groups. | No | DO NOT CHANGE |
| `LGPSTypeStructure`, `ArgyroditeStructure` | `SulfideStructureFamily` | Correct — both sulfide-based superionic conductors. | No | DO NOT CHANGE |
| **`GarnetStructure`** | `StructureFamily` (direct) | **Finding**: Garnets (e.g. Li₇La₃Zr₂O₁₂) are complex-oxide framework structures. `OxideStructureFamily`'s own `rdfs:comment` is "Structure families built from a close-packed or framework oxide anion sublattice" — Garnet fits this definition but sits as a *sibling* of `OxideStructureFamily` instead of a child. | **Yes** | STRONGLY RECOMMENDED: `GarnetStructure rdfs:subClassOf OxideStructureFamily` (in addition to or replacing the direct `StructureFamily` parent) |
| **`PerovskiteStructure`** | `StructureFamily` (direct) | **Finding**: ABO₃ perovskite is the textbook oxide-framework structure — same gap as Garnet. | **Yes** | STRONGLY RECOMMENDED: `PerovskiteStructure rdfs:subClassOf OxideStructureFamily` |
| `BatteryRole` | `emmo:Role` (`EMMO_4f226cf3...`) | Correct — see §11 for the full chain this enables. | No | DO NOT CHANGE |
| `ElectrolyteRole`, `NegativeElectrodeRole`, `PositiveElectrodeRole`, `SeparatorRole` | `BatteryRole` | Correct, matches skos:closeMatch alignments to EMMO domain-electrochemistry siblings. | No | DO NOT CHANGE |
| `BandGapProperty`, `EnergyAboveHullProperty`, `FormationEnergyProperty` | `emmo:Energy` (`EMMO_31ec09ba...`) | Correct — all are energy-dimensioned quantities (eV). | No | DO NOT CHANGE |
| `BulkModulusProperty`, `ShearModulusProperty` | `emmo:Pressure` (`EMMO_50a44256...`) | Correct — both pressure-dimensioned (GPa). No "issue" found requiring correction — contradicts the earlier false claim that this needed fixing. | No | DO NOT CHANGE |

**Multiple inheritance check (Rule 3F):** the two recommended additions above (Garnet/Perovskite → also `OxideStructureFamily`) would each be the class's *only* asserted superclass — not multiple inheritance, a correction of which single superclass is right. No multiple-inheritance case currently exists or is being proposed anywhere in this ontology; none is recommended.

---

## 4. Object Property Audit (Rule 4)

All 29 object properties, with domain/range extracted directly (external EMMO/BattINFO IRIs resolved to their labels):

| Property | Domain | Range | Subproperty of | Characteristics | Assessment |
|---|---|---|---|---|---|
| `belongsToCrystalSystem` | `SpaceGroup` | `CrystalSystem` | — | none | Correct, deterministic classification (added this session; verified). |
| `belongsToElectrode` | `ChemicalSubstance` | `PositiveElectrodeRole ∪ NegativeElectrodeRole` (blank-node `unionOf`) | — | none (inverseOf deliberately removed, see §17) | Correct as narrowed. The `unionOf` range is the ontology's only class-union construct — not EL. |
| `hasBandGap` | `ChemicalSubstance` | `BandGapProperty` | `emmo:hasProperty` | none | Correct reified-quantity pattern. |
| `hasBond` | `Site` | `CrystalBond` | — | none | Correct. |
| `hasBondTo` | `Site` | `Site` | — | derived via chain `hasBond∘hasTargetSite` | Correctly derived, not independently asserted — avoids drift. |
| `hasBulkModulus` | `ChemicalSubstance` | `BulkModulusProperty` | `emmo:hasProperty` | none | Correct. |
| `hasCRate`, `hasCapacity`, `hasCoulombicEfficiency`, `hasOpenCircuitVoltage`, `hasSpecificCapacity`, `hasStateOfCharge`, `hasVoltage` | `BatteryCell` | respective EMMO domain-electrochemistry quantity classes | `emmo:hasProperty` | none | Bearer class correct for these 7 — genuinely cell-level measured/reported quantities. |
| `hasIonicConductivity` | `BatteryCell` | `electrochemistry_25dabdc2...` (IonicConductivity) | `emmo:hasProperty` | none | **Bearer-class concern** — see §12. Ionic conductivity is conventionally an intrinsic electrolyte-material property, not a whole-cell aggregate. The property's own `rdfs:comment` already hedges: "a battery cell (**or, by extension, an electrolyte material within it**)". |
| `hasCoordinationGeometry` | `Site` | `CoordinationGeometry` | `emmo:hasProperty` | none | Correct. |
| `hasCrystalSystem` | `CrystalStructure` | `CrystalSystem` | `emmo:hasProperty` | derived via chain `hasSpaceGroup∘belongsToCrystalSystem` | Correctly derived this session; fixed the prior gap where crystal system and space group could disagree. |
| `hasElement` | `Species` | `emmo:ChemicalElement` | `emmo:hasConstituent` | none | Correct. |
| `hasEnergyAboveHull`, `hasFormationEnergy` | `ChemicalSubstance` | respective reified Property class | `emmo:hasProperty` | none | Correct. |
| `hasShearModulus` | `ChemicalSubstance` | `ShearModulusProperty` | `emmo:hasProperty` | none | Correct. |
| `hasSite` | `UnitCell` | `Site` | `emmo:hasPart` | none | Correct mereological subproperty. |
| `hasSourceSite`, `hasTargetSite` | `CrystalBond` | `Site` | — | none | Correct; these are also the chain components for `hasBondTo`. |
| `hasSpaceGroup` | `CrystalStructure` | `SpaceGroup` | `emmo:hasProperty` | none | Correct. |
| `hasSpecies` | `Site` | `Species` | `emmo:hasConstituent` | none | Correct. |
| `hasStructure` | `ChemicalSubstance` | `CrystalStructure` | `emmo:hasPart` | none | Correct — deliberately left unconstrained on the `ChemicalSubstance` side (not every substance is crystalline), per prior session decision. |
| `hasStructureFamily` | `CrystalStructure` | `StructureFamily` | `emmo:hasProperty` | none | Correct. |
| `hasUnitCell` | `CrystalStructure` | `UnitCell` | `emmo:hasPart` | none | Correct. |
| `usesMaterial` | `BatteryRole` | `ChemicalSubstance` | — | none (inverseOf deliberately removed) | Correct — see §17. |

**Redundancy check:** no two object properties duplicate each other's domain+range+meaning. **Directionality:** all are unidirectional with no inverse asserted — deliberate, since `owl:inverseOf` is itself outside OWL 2 EL, and the one place an inverse previously existed (`belongsToElectrode`/`usesMaterial`) caused a real inconsistency and was removed.

---

## 5. Datatype Property Audit (Rule 5)

30 datatype properties. Grouped by pattern rather than listed individually 30 times, since they fall into 4 clear, consistent groups:

| Group | Properties | Range | Assessment |
|---|---|---|---|
| Unit-cell geometry | `hasLatticeA/B/C`, `hasAlpha/Beta/Gamma` | `xsd:double` | Appropriate. Angstrom/degree units stated in comments; these are simple scalar geometry, not dimensioned quantities needing the reified `Property` pattern the file already uses for band gap/moduli/etc. |
| Site fractional coordinates | `hasFractionalX/Y/Z` | `xsd:double` | Appropriate, dimensionless by convention (`[0,1)`), already documented as such. |
| Identifiers / categorical strings | `hasMaterialProjectId`, `hasFormula`, `hasChemsys`, `hasCif`, `hasSymmetrySymbol`, `hasPointGroup`, `hasCoordinationMethod` | `xsd:string` | Appropriate — these are genuinely identifiers/labels, not measurements. |
| Booleans (Materials-Project provenance flags) | `isMetal`, `isStable`, `isTheoretical`, `isGapDirect`, `hasSmactValidity` | `xsd:boolean` | Appropriate. |
| Element periodic-table data | `hasGroup`, `hasPeriod`, `hasValenceElectrons` (`xsd:integer`); `hasAtomicMass`, `hasCovalentRadius`, `hasElectronegativity` (`xsd:double`) | mixed | Appropriate — integers for genuinely discrete counts, doubles for continuous physical values. |
| Bond/structure numerics | `hasBondDistance`, `hasSpaceGroupNumber`, `hasOxidationState` | mixed | Appropriate. |

**Rule 5's specific question — should any of these instead use a Quantity/Value/Unit reification pattern?** No. The file already reserves that reified pattern (a dedicated `*Property` class carrying value + unit) for the 5 properties that are genuinely dimensioned physical quantities requiring explicit unit-tracking across a heterogeneous dataset (`BandGapProperty`, `BulkModulusProperty`, `ShearModulusProperty`, `FormationEnergyProperty`, `EnergyAboveHullProperty`). The 30 datatype properties above are either unit-implicit-by-fixed-convention (Materials-Project always reports lattice parameters in Å, angles in degrees) or genuinely categorical/identifier data. Reifying them would add structural complexity with no corresponding gain in correctness or queryability — this is a deliberate, correct choice, not an oversight. **DO NOT CHANGE.**

---

## 6. Current OWL Restrictions (Rule 6 baseline)

All 16 existing `owl:Restriction` instances, all `someValuesFrom` (zero `allValuesFrom`, zero cardinality):

| Subject class | Property | Target |
|---|---|---|
| `ChemicalSubstance` (imported) | `emmo:hasProperty` | `emmo:Property` |
| `BatteryRole` | `usesMaterial` | `ChemicalSubstance` |
| `CrystalBond` | `hasSourceSite` | `Site` |
| `CrystalBond` | `hasTargetSite` | `Site` |
| `CrystalBond` | `hasBondDistance` | `xsd:double` |
| `CrystalStructure` | `hasCrystalSystem` | `CrystalSystem` |
| `CrystalStructure` | `hasSpaceGroup` | `SpaceGroup` |
| `CrystalStructure` | `hasUnitCell` | `UnitCell` |
| `CrystalStructure` | `hasStructureFamily` | `StructureFamily` |
| `Site` | `hasSpecies` | `Species` |
| `Site` | `hasBond` | `CrystalBond` |
| `Site` | `hasBondTo` | `Site` |
| `Site` | `hasCoordinationGeometry` | `CoordinationGeometry` |
| `SpaceGroup` | `belongsToCrystalSystem` | `CrystalSystem` |
| `Species` | `hasElement` | `emmo:ChemicalElement` |
| `UnitCell` | `hasSite` | `Site` |

Every restriction here is a necessary-existence condition (`some`) on something that is logically constitutive of the class's own definition — matching Rule 7's test exactly (a `CrystalBond` without endpoints is meaningless; contrast with a `ChemicalSubstance` without a computed band gap, which is completely valid and correctly left unconstrained).

---

## 7. Missing but Justified Restrictions (Rule 6/7 — the core of this audit)

Two candidates, both tested in a disposable copy of the ontology (§16), both classified per the requested 1–5 scale:

### 7.1 `BatteryCell ⊑ ∃hasRole.BatteryRole` — **Classification: 2, STRONGLY JUSTIFIED**

Not strictly REQUIRED (a `BatteryCell` individual without a populated role is not internally contradictory the way an endpoint-less `CrystalBond` would be — Rule 7's open-world test genuinely applies: a cell could exist in the KG before its roles are populated). But it is scientifically intrinsic: EMMO's own `BatteryCell` definition literally reads *"an assembly of electrodes, electrolyte, container, terminals and usually separators"* — i.e. a `Whole` whose defining parts include role-players. The mechanism to express this already exists fully-formed in EMMO (`emmo:Role`, `emmo:Whole`, `emmo:hasRole` — domain `Whole`, range `Role`), and `battgpt:BatteryRole` already `⊑ emmo:Role`. No new property, no duplication.

Exact verified chain, traced against the actual imported axioms (not assumed):
- `emmo:hasRole` (`EMMO_8e52c42b_e879_4473_9fa1_4b23428b392b`) — `rdfs:domain emmo:Whole` (`EMMO_1efe8b96...`), `rdfs:range emmo:Role` (`EMMO_4f226cf3...`)
- `emmo:Role ⊑ [inverse hasRole] some Whole` — already present in EMMO core, inherited by `BatteryRole`
- `battery:BatteryCell` (`battery_68ed592a...`) — checked its full 15-member ancestor closure programmatically: **not currently `⊑ Whole`**
- Because `hasRole`'s domain is `Whole`, asserting `BatteryCell ⊑ ∃hasRole.BatteryRole` **entails** `BatteryCell ⊑ Whole` via domain propagation — no separate subsumption assertion is needed, and none is proposed.

### 7.2 `GarnetStructure`, `OlivineStructure`, `SpinelStructure` → characteristic `SpaceGroup` — **Classification: 2, STRONGLY JUSTIFIED**

Using a new property `hasCharacteristicSpaceGroup` (domain `StructureFamily`, range `SpaceGroup`) with `owl:hasValue` restrictions (EL-legal nominal form) pointing at three new `SpaceGroup` individuals. Independently verified against literature (not just the file's own comments):

| Family | Space group | Verification |
|---|---|---|
| `GarnetStructure` | Ia-3d (#230) | Multiple independent papers on the cited example (Li₇La₃Zr₂O₁₂/LLZO): cubic garnet is Ia-3d across measured temperature ranges. |
| `OlivineStructure` | Pnma (#62) | **Exact match to the Materials Project source record itself** — mp-19017 (the file's own cited example) is listed by MP as "Orthorhombic, Pnma, 62." |
| `SpinelStructure` | Fd-3m (#227) | Fd-3m is the well-established canonical cubic spinel space group — **but** a documented Materials Project community report notes the specific cited example (mp-22584, LiMn₂O₄) shows Jahn-Teller-distorted lower symmetry in its DFT-relaxed structure, not the ideal Fd-3m. |

Because of that last caveat, the restriction is written to describe the **structure-family class's idealized prototype**, not a per-individual hard requirement — a real Jahn-Teller-distorted compound can still correctly belong to `SpinelStructureFamily` without its own `CrystalStructure` individual having `hasSpaceGroup Fd-3m`. This is exactly the distinction Rule 7 asks for, applied correctly: the *family* has a defining characteristic (safe to assert), the *individual member* does not have to match it exactly (not asserted).

**Explicitly not proposed** (per instruction, and because no verified source exists): space groups for `LayeredOxideStructure`, `RockSaltStructure`, `NASICONStructure`, `LGPSTypeStructure`, `ArgyroditeStructure`, `PerovskiteStructure`.

### 7.3 What was considered and explicitly rejected

- **`ChemicalSubstance ⊑ ∃hasStructure.CrystalStructure`** — REJECTED (classification 4, UNSAFE) in an earlier pass this session, reaffirmed here: liquid/amorphous electrolytes are valid `ChemicalSubstance` individuals with no crystal structure. Open-world test fails.
- **Cardinality tightening** (e.g. `CrystalStructure = 1 hasUnitCell.UnitCell`) — see §8.
- **CoordinationGeometry linkage for StructureFamily leaves** — 8 `CoordinationGeometry` individuals already exist and are ready to use (`OctahedralGeometryIndividual`, `TetrahedralGeometryIndividual`, etc.), but no per-family mapping has been independently verified this pass (Spinel notably has *both* tetrahedral and octahedral sites, so a single-value restriction would be wrong; a `some` restriction allowing multiple asserted values would be correct but needs the same literature-verification discipline applied above before proposing specific values). Classification: 3, OPTIONAL, pending verification — not proposed now.

---

## 8. Cardinality Audit (Rule 6/8)

**Zero cardinality restrictions exist, and this pass does not recommend adding any**, despite several being scientifically tempting:

| Candidate | Scientifically true? | Recommended? | Why not |
|---|---|---|---|
| `CrystalStructure = 1 hasUnitCell.UnitCell` | Yes — a crystal structure has exactly one unit cell description | No | `owl:qualifiedCardinality` is outside OWL 2 EL. The existing `some` restriction already captures the operationally important fact (at least one exists); moving to "exactly one" adds no query/inference value the KG actually needs. |
| `SpaceGroup = 1 belongsToCrystalSystem.CrystalSystem` | Yes — deterministic 1-to-1 crystallographic fact | No | Same reasoning; also, `hasCrystalSystem`/`belongsToCrystalSystem` being non-simple (chain-derived) properties means cardinality restrictions on them would be **illegal** in OWL 2 DL, not just non-EL. |
| Any `owl:FunctionalProperty` declaration | Several properties are functionally single-valued in reality (e.g. `belongsToCrystalSystem`) | No | Functional-property characteristics are outside EL and add no benefit the `some` restrictions don't already provide for this KG's query patterns. |

**Conclusion for Rule 8:** the ontology's current zero-cardinality stance is correct and should be preserved. This is stated explicitly per the instruction: **NO CARDINALITY AXIOM SHOULD BE ADDED.**

---

## 9. Disjointness Audit (Rule 13)

Three `owl:AllDisjointClasses` blocks already exist, all scientifically sound (mutually-exclusive categories, not overlapping classifications):
1. 9-way: the `StructureFamily` leaves (`ArgyroditeStructure`, `GarnetStructure`, ..., `SpinelStructure`) — a material's structure prototype is exactly one of these, never two.
2. 4-way: `BatteryRole` subclasses — a role-player is exactly one of electrolyte/negative/positive/separator, never two, which is precisely what caught the v0.3.1→v0.3.2 `owl:inverseOf` inconsistency (§17).
3. 3-way: the `StructureFamily` mid-tier (`Oxide`/`Polyanion`/`Sulfide`).

**Open-world consequence of each:** `owl:AllDisjointClasses` under OWL's open-world semantics does *not* mean "the KG must know which one" — it means "if two are ever asserted about the same individual, that's a contradiction the reasoner will catch." This is exactly the intended safety net (it already caught one real bug), not an assumption of complete knowledge. **No new disjointness is proposed** — the existing three are correct and sufficient; the Garnet/Perovskite hierarchy fix in §3 does not require any change to the disjointness sets (they operate at the leaf level, unaffected by which mid-tier class a leaf's *other* parent is).

**EL note:** `owl:AllDisjointClasses`/`DisjointClasses` is outside OWL 2 EL. This is the ontology's second (along with the `unionOf`) non-EL construct, and it is being kept deliberately — see §14.

---

## 10. Quantity/Value/Unit Audit (Rule 14)

Already addressed in full in §5. Summary: the file already uses the correct EMMO-aligned pattern (`Property`-subclass reification with `hasProperty`) for the 5 properties that need it, and correctly does *not* apply it to the 30 plain-scalar datatype properties, which don't need it. **No change recommended (D — no change should be made).**

---

## 11. Material ↔ BatteryCell Connectivity Audit (Rule 10)

**Current state:** no path connects `battery:BatteryCell` to `battgpt:ChemicalSubstance`/`BatteryRole` at all. Verified by direct grep — zero occurrences of any property linking these before this audit.

**The complete path, once §7.1's restriction is added, traced explicitly:**

```
BatteryCell ⊑ ∃hasRole.BatteryRole        (proposed, §7.1)
BatteryRole ⊑ ∃usesMaterial.ChemicalSubstance   (already exists, added earlier this session)
```

So: `BatteryCell —hasRole→ BatteryRole —usesMaterial→ ChemicalSubstance` becomes a fully typed, traversable path using **three properties, all already existing or independently justified — zero new properties invented** for this purpose. `belongsToElectrode` (the other existing `ChemicalSubstance`-side property, narrowed to the two electrode roles) provides a second, narrower path from the material side back to its electrode role, independently of `usesMaterial` since v0.3.2 (§17) — these two are deliberately not inverses of each other any more, so they don't collapse into redundancy.

**Rule 10's explicit caution honored:** this does *not* assert every `ChemicalSubstance` must belong to a `BatteryCell` — `hasStructure`, `usesMaterial`'s inverse direction, and `belongsToElectrode` are all left unconstrained on the substance side, exactly as required. Only the `BatteryCell` side gets the new existential (a cell, by its own EMMO definition, does have role-playing parts).

---

## 12. Electrochemical Semantics Audit (Rule 11)

All 8 properties (`hasCapacity`, `hasSpecificCapacity`, `hasIonicConductivity`, `hasVoltage`, `hasOpenCircuitVoltage`, `hasCRate`, `hasCoulombicEfficiency`, `hasStateOfCharge`) currently have `rdfs:domain battery:BatteryCell`, verified directly (not inferred from labels).

| Property | Bearer correct? | Notes |
|---|---|---|
| `hasVoltage`, `hasOpenCircuitVoltage`, `hasCRate`, `hasStateOfCharge`, `hasCoulombicEfficiency` | Yes | These are conventionally reported and measured at the whole-cell level in battery testing — `BatteryCell` is the scientifically correct bearer. |
| `hasCapacity` | Yes | Cell-level capacity (Ah) is standard. |
| `hasSpecificCapacity` | Borderline — **flagged** | Specific capacity (mAh/g) is *often* reported as an intrinsic material property (e.g. "LiFePO4's theoretical specific capacity is ~170 mAh/g") independent of any particular cell, not only as a cell-test result. Current `BatteryCell`-only domain is not wrong, but may be too narrow for populating material-intrinsic values from a source like Materials Project. Classification: 3, OPTIONAL IMPROVEMENT — widening to a domain union (`BatteryCell ∪ ChemicalSubstance`) is possible but a union is non-EL, and premature without knowing whether the actual data pipeline will ever populate it at the material level. |
| `hasIonicConductivity` | **Flagged — genuine concern** | Ionic conductivity (S/cm) is conventionally an intrinsic *electrolyte-material* property, not a whole-cell aggregate the way voltage/capacity are. The property's own `rdfs:comment` already hedges this: *"a battery cell (or, by extension, an electrolyte material within it)"* — the ontology's own documentation flags the ambiguity it's currently modeling around rather than resolving. Classification: **E, REQUIRES HUMAN/SCIENTIFIC DECISION** — resolving this well requires knowing whether the actual population pipeline measures conductivity per-cell or per-electrolyte-material, which is a data-source question, not one this audit can answer from the schema alone. |

No existential restriction is proposed on `BatteryCell` for any of these 8 (Rule 7 open-world test: a valid `BatteryCell` individual can exist in the KG before every electrochemical quantity is measured/populated for it — these are all legitimately optional facts, unlike the `hasSourceSite`/`hasTargetSite` case for `CrystalBond`).

---

## 13. StructureFamily Semantics Audit (Rule 12)

Already covered in depth in §7.2. Summary table of what's free text vs. formally encoded, and each candidate's verification status:

| Structural fact | Currently formal? | Candidate axiom status |
|---|---|---|
| Garnet ↔ Ia-3d | No (comment only) | Verified from independent source — propose |
| Olivine ↔ Pnma | No (comment only) | Verified from independent source (exact MP-record match) — propose |
| Spinel ↔ Fd-3m | No (comment only) | Verified for the idealized prototype, with a documented real-compound caveat — propose as class-level characteristic, not per-individual constraint |
| LayeredOxide/RockSalt/NASICON/LGPS-type/Argyrodite/Perovskite ↔ any space group | No | Requires external scientific verification — **not proposed**, per explicit instruction |
| Structure-family leaf ↔ CoordinationGeometry | No | Requires external scientific verification per family (some families have multiple site types) — **not proposed** |
| `GarnetStructure`/`PerovskiteStructure` ↔ `OxideStructureFamily` | No (misplaced in hierarchy) | Verified from the ontology's own definition of `OxideStructureFamily` — see §3 |

---

## 14. OWL 2 EL Compatibility (Rule 8)

**Currently EL-compatible (the overwhelming majority of the ontology):** all 31 class declarations, all 16 `someValuesFrom` restrictions, both `owl:propertyChainAxiom` derivations (property chains **are** EL-legal — this is a common misconception; EL explicitly supports `SubObjectPropertyOf` with a chain, which is how bio-ontologies like GO use part-of composition), all plain `rdfs:domain`/`rdfs:range` declarations, all datatype properties.

**Currently outside EL (2 constructs, both pre-existing, both scientifically justified, neither proposed for removal):**
1. `belongsToElectrode`'s `owl:unionOf` range — `ObjectUnionOf` is not in EL. Justified because the range genuinely is "one of these two classes," and the alternative (widening to a common superclass) would lose real information.
2. The 3 `owl:AllDisjointClasses` blocks (§9) — `DisjointClasses` is not in EL. Justified because they encode real mutual-exclusivity and already caught a genuine bug.

**Proposed additions and their EL status:**
- `BatteryCell ⊑ ∃hasRole.BatteryRole` — **EL-compatible** (plain `someValuesFrom`).
- `hasCharacteristicSpaceGroup` (new property) — **EL-compatible** (plain object property declaration).
- `GarnetStructure`/`OlivineStructure`/`SpinelStructure ⊑ hasCharacteristicSpaceGroup value X` (`owl:hasValue`) — **EL-compatible**. `ObjectHasValue` with a nominal is one of EL's core constructs, not an exception to it.
- `GarnetStructure`/`PerovskiteStructure ⊑ OxideStructureFamily` (hierarchy fix) — **EL-compatible** (plain `subClassOf`).

**None of the proposed changes removes EL compatibility anywhere it currently holds**, and none of the 2 existing non-EL constructs is touched.

---

## 15. OnT/HiT Representation-Learning Readiness (Rule 9)

- **Hierarchy quality:** generally good — clean, mostly non-tangled taxonomy (zero classes currently have more than one asserted direct ancestor: confirmed `numberOfClassesWithMoreThanOneDirectAncestor_Ass = 0` from an earlier OQuaRE run this session). The one gap (§3, Garnet/Perovskite) is a placement error, not a design flaw in the hierarchy style itself.
- **Hierarchy depth:** shallow by design (asserted max depth 4) — appropriate for a focused extension module; an OnT/HiT transformer consuming this alongside EMMO's own much deeper hierarchy will see battgpt's local structure as a well-defined, shallow, information-dense subtree rather than noise.
- **Isolated classes:** before this audit, `BatteryRole` (and hence the whole `usesMaterial`/`belongsToElectrode` subgraph) was structurally disconnected from `BatteryCell` — a transformer would see two unconnected components where a real semantic link exists. §7.1's restriction fixes exactly this, and is therefore the single highest-value structural-signal improvement identified in this audit for ML consumption specifically — though it is being recommended on independent scientific grounds (§7.1), with the ML benefit as a secondary confirmation, not the primary justification (per the audit's own priority ordering).
- **Relations existing only as domain/range (no restriction):** the 8 electrochemical properties (§12) and `hasStructure`/`hasSpecificCapacity` are examples where domain/range alone gives a transformer weaker signal than a restriction would — but per Rule 7's open-world test, none of them should get one, since the underlying facts are genuinely optional. This is the correct trade-off: more restrictions is not automatically better structural signal if the restrictions would be scientifically false.
- **Explicit non-goal restated:** no change in this report is proposed to raise triple count, restriction count, or any metric for its own sake.

---

## 16. Reasoner Results (Rule 15)

**Baseline (this session, verified, full merged closure — `battgpt.ttl` + EMMO + domain-battery + domain-chemical-substance + domain-electrochemistry + BattINFO, resolved via the project's own `catalog-v001.xml`, no network fetches):**
- ELK: 1 unsatisfiable class — `emmo:CentiMetreSecondDegreeCelsius`. Zero references anywhere in `battgpt.ttl`; purely an EMMO units-module class.
- HermiT (full SROIQ, via ROBOT — real ~40-minute run, not a stub): 2 unsatisfiable classes — the same `CentiMetreSecondDegreeCelsius`, plus `emmo:MagneticMoment` (an EMMO ISQ electromagnetism-quantity class, also zero references in `battgpt.ttl`). Both traced to EMMO's own axioms, confirmed pre-existing, confirmed unconnected to anything in this ontology.

**Candidate-axiom test (this pass, per Rule 15.7 — tested in a disposable copy, `battgpt.ttl` never modified):** built `battgpt_candidate_test.ttl` = `battgpt.ttl` + §7.1's `BatteryCell` restriction + §7.2's `hasCharacteristicSpaceGroup` property, 3 new `SpaceGroup` individuals, and the 3 `hasValue` restrictions.
- Parses cleanly via `rdflib`: 972 triples (941 + 31 new, exact expected delta).
- ROBOT + ELK on the full merged closure: **still exactly 1 unsatisfiable class, the same pre-existing `CentiMetreSecondDegreeCelsius`. Zero new unsatisfiable classes introduced.**
- ROBOT + HermiT on the full merged closure (real run, completed): **still exactly 2 unsatisfiable classes — the same `CentiMetreSecondDegreeCelsius` and `MagneticMoment` (`EMMO_3ef37f82...`) found in the unmodified baseline. Zero new unsatisfiable classes introduced under full SROIQ reasoning either.** This is the complete confirmation: both candidate axiom sets in §7.1 and §7.2 are safe under both the fast/incomplete (ELK) and full/complete (HermiT) reasoners.

**Distinguishing BattGPT defects from imported-ontology defects:** confirmed by direct reference-checking (not proximity/assumption) that both known-unsatisfiable classes have zero triples referencing them anywhere in `battgpt.ttl`. **The BattGPT module itself contributes zero unsatisfiable classes**, before or after the tested candidate additions.

---

## 17. Confirmed Defects (Category A)

None found in the *current* file. (The claims in the earlier, incorrect prompt about `owl:inverseOf`, `chsub:` dangling references, and `BulkModulusProperty`/`ShearModulusProperty` superclasses were checked and are **NOT PRESENT IN CURRENT FILE** — see §2 and the explicit checks below. Nothing to fix because nothing is broken here.)

Explicit Rule 2 verification, stated plainly:
- `owl:inverseOf` between `belongsToElectrode`/`usesMaterial`: **NOT PRESENT** (zero `owl:inverseOf` triples exist anywhere in the file; documented in comments as deliberately removed in v0.3.2 to fix a real inconsistency).
- `chsub:Substance`, `chsub:Element`: **NOT PRESENT** — the `chsub:` prefix is declared but never once used anywhere in the file.
- `Species` existential restriction (`hasElement`): **PRESENT** — pre-existing since v0.3.0, not newly added.
- `CrystalBond` source/target existential restrictions: **PRESENT** — pre-existing since v0.3.0, not newly added.
- `BulkModulusProperty`/`ShearModulusProperty` superclass "issue": **NOT PRESENT** — both are correctly anchored under `emmo:Pressure`; no issue exists to have been corrected.

---

## 18. Strongly Recommended Changes (Category B)

| # | Change | Section | EL-compatible |
|---|---|---|---|
| 1 | `BatteryCell ⊑ ∃hasRole.BatteryRole` | §7.1, §11 | Yes |
| 2 | `hasCharacteristicSpaceGroup` property + 3 verified `SpaceGroup` individuals + `hasValue` restrictions on `GarnetStructure`/`OlivineStructure`/`SpinelStructure` | §7.2, §13 | Yes |
| 3 | `GarnetStructure rdfs:subClassOf OxideStructureFamily`; `PerovskiteStructure rdfs:subClassOf OxideStructureFamily` | §3 | Yes |

---

## 19. Optional Improvements (Category C)

| # | Change | Section | Why optional, not strong |
|---|---|---|---|
| 1 | `hasSpecificCapacity` domain widened to include `ChemicalSubstance` | §12 | Scientifically defensible but depends on unknown future population-pipeline behavior |
| 2 | `hasCharacteristicCoordinationGeometry` linkage for `StructureFamily` leaves, using the 8 existing `CoordinationGeometry` individuals | §7.3 | Mechanism ready, but no per-family mapping independently verified yet |

---

## 20. Do-Not-Change Items (Category D)

- The 30 plain-scalar datatype properties (§5, §10) — correct as-is, no quantity/value/unit reification needed.
- The 16 existing `someValuesFrom` restrictions (§6) — all correctly scoped to logically-constitutive relationships.
- Zero cardinality restrictions (§8) — correct EL-preserving stance.
- The 3 existing `AllDisjointClasses` blocks and the `belongsToElectrode` `unionOf` (§9, §14) — scientifically justified non-EL constructs, kept deliberately.
- The removed `owl:inverseOf` (§17) — correctly absent; must not be re-added.
- `hasVoltage`, `hasOpenCircuitVoltage`, `hasCRate`, `hasStateOfCharge`, `hasCoulombicEfficiency`, `hasCapacity` bearer class (§12) — `BatteryCell` is correct for all 6.

---

## 21. Human Decisions Required (Category E)

| # | Question | Section |
|---|---|---|
| 1 | Should `SpaceGroup`/`CrystalSystem`/`CoordinationGeometry`/`StructureFamily` be re-anchored from `emmo:Property` to `owl:Thing`? | §3 |
| 2 | Should `hasIonicConductivity`'s domain be reconsidered (cell vs. electrolyte-material bearer)? Depends on the actual data-population pipeline's measurement source. | §12 |
| 3 | Should `hasSpecificCapacity`'s domain be widened to also cover `ChemicalSubstance`? | §19 |

---

## 22. Prioritized Implementation Plan

If and when the changes in §18 are approved:

1. **Backup** `battgpt.ttl` (copy with timestamp) before any edit.
2. Apply only the 3 changes in §18 — nothing else.
3. Re-run `rdflib` parse — confirm triple count is exactly 941 + expected delta (§16's disposable-copy test already confirmed the delta is +31 for the full candidate set; the 2 hierarchy-fix triples for §18.3 are additional and were not yet included in that test file, so the real delta will be re-measured after this plan is executed, not assumed from the earlier test).
4. Re-run ROBOT + ELK on the full merged closure via the existing catalog — confirm still exactly 1 pre-existing unsatisfiable class, zero new ones.
5. Re-run ROBOT + HermiT on the full merged closure — confirm still exactly 2 pre-existing unsatisfiable classes, zero new ones (cross-check against §16's disposable-copy HermiT run once it completes).
6. Diff the inferred class hierarchy before/after against the baseline in §16 — confirm no unexpected new superclass relationships beyond the ones intentionally introduced.
7. Produce a precise triple-level diff (`git diff battgpt.ttl`) as the change report.
8. Confirm via diff that no UML file (`.drawio`, `.pdf`) and no unrelated ontology content changed.

**No changes have been applied. This document is the audit deliverable only.**
