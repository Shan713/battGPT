# BattGPT Semantic Enrichment Audit — StructureFamily / BatteryRole / Material↔BatteryCell

**Status: audit + proposal only. `battgpt.ttl` has NOT been modified by this pass.**
Baseline audited: `battgpt.ttl` as it stands after the previously-applied changes (989 triples: `hasRole` bridge, `hasCharacteristicSpaceGroup` for Garnet/Olivine/Spinel, Garnet/Perovskite reparented under `OxideStructureFamily`).

---

## Phase 1 — Audit of current state

**A. Classes checked, confirmed present/absent by direct grep (not assumed):**

| Concept named in the task | Exists in `battgpt.ttl`? |
|---|---|
| `StructureFamily`, `CrystalStructure`, `SpaceGroup`, `CoordinationGeometry`, `Site`, `Species` | Yes, all present (local classes) |
| `BatteryRole`, `PositiveElectrodeRole`, `NegativeElectrodeRole`, `ElectrolyteRole`, `SeparatorRole` | Yes, all present (exactly 4 `BatteryRole` subclasses — confirmed by grep, no 5th) |
| **`ActiveMaterialRole`** | **No — does not exist.** Not a class in this ontology. |
| `BatteryCell` | Yes, but as the *imported* EMMO/BattINFO class (`battery:battery_68ed592a...`), not a local battgpt class |
| `Battery` | Only as an imported EMMO class (`battery:Battery`, superclass of `BatteryCell` in the import — unrelated to this task) |
| `ChemicalSubstance` | Yes, imported EMMO class, used throughout as the material-bearer range |
| `Material` (EMMO's own, distinct from `ChemicalSubstance`) | Exists in EMMO but deliberately *not* used — documented reasoning already in `usesMaterial`'s comment |
| `Substance` | Exists in EMMO as the shared ancestor of `ChemicalSubstance`/`Material`/`Mixture` — not used directly |
| `Electrode` | Only as an imported EMMO class (`electrochemistry_0f007072...`, labeled "Electrode") — no local `battgpt:Electrode` |
| `Electrolyte`, `Separator` | **No dedicated classes of either name in EMMO or battgpt.** `hasElectrolyte`'s range is generic `emmo:Substance`; `hasSeparator`'s range is generic `emmo:PhysicalObject`. Neither is a specific "Electrolyte" or "Separator" class. |

**B. Object properties involving these concepts** (already fully enumerated in the previous audit pass, `battgpt_ontology_constraint_and_semantics_audit.md` §4 — re-verified unchanged here): `usesMaterial` (`BatteryRole→ChemicalSubstance`), `belongsToElectrode` (`ChemicalSubstance→PositiveElectrodeRole∪NegativeElectrodeRole`), `hasStructure`, `hasStructureFamily`, `hasSpaceGroup`, `hasCrystalSystem`, `belongsToCrystalSystem`, `hasCharacteristicSpaceGroup`, plus the newly-applied `emmo:hasRole` restriction on `BatteryCell`.

**C. Restriction/characteristic inventory** — unchanged from the previous audit's exact counts (16 `someValuesFrom` + 3 `hasValue` restrictions now present after the applied changes; zero cardinality, zero `allValuesFrom`, zero property characteristics, zero `owl:inverseOf`, one `unionOf`, three `AllDisjointClasses` blocks). Not re-derived here in full — see the prior report for the complete table.

**D. Relations currently only in comments, not formalized:**
- `hasIonicConductivity`'s comment hedges "a battery cell (or, by extension, an electrolyte material within it)" — an *acknowledged* ambiguity, not a hidden formal claim. Flagged already in the prior audit; not re-litigated here.
- No other comment-only relationship was found this pass that both (a) states a specific, checkable claim and (b) isn't already covered by an existing axiom. Per the task's own instruction, a relation mentioned in a comment is **not** automatically a candidate for formalization — none of the remaining comment text (e.g. "used by fast Li-ion-conducting solid electrolytes" on `GarnetStructure`) states a checkable structural fact distinct from what's already formalized.

---

## Phase 2 — StructureFamily semantic enrichment

### 2.1 `hasCharacteristicSpaceGroup` — already applied for Garnet/Olivine/Spinel

No further space-group mappings are proposed. Per the previous audit, `LayeredOxideStructure`, `RockSaltStructure`, `NASICONStructure`, `LGPSTypeStructure`, `ArgyroditeStructure` have no space group verified from any source in or out of this ontology — **not proposed, per explicit instruction not to guess.**

### 2.2 `hasCharacteristicCoordinationGeometry` — new candidate property

8 `CoordinationGeometry` individuals already exist (`OctahedralGeometryIndividual`, `TetrahedralGeometryIndividual`, `CuboctahedralGeometryIndividual`, etc.) but **zero** `StructureFamily`-level mapping exists — only `Site`-level (`hasCoordinationGeometry`, domain `Site`).

Verified this pass (via literature, one live search) and via well-established crystallography (textbook-level, not independently re-searched this pass — flagged accordingly):

| Family | Site(s) and geometry | Verification | Single or multiple? |
|---|---|---|---|
| `PerovskiteStructure` | A-site: cuboctahedral (12-fold); B-site: octahedral (6-fold) | **Verified via live search this pass** — matches exactly | Multiple (2 distinct sites) — `some`, not functional |
| `SpinelStructure` | A-site (8a): tetrahedral; B-site (16d): octahedral | Well-established (textbook AB₂O₄ spinel structure) — not independently re-searched this pass | Multiple — `some` |
| `OlivineStructure` | M1/M2 sites: octahedral; P site: tetrahedral | Well-established (textbook olivine/LiFePO₄ structure) — not independently re-searched this pass | Multiple — `some` |
| `LayeredOxideStructure`, `RockSaltStructure` | Both cation sublattices: octahedral | Well-established — not independently re-searched this pass | Both sites share the *same* geometry type here, so a single `some octahedral` assertion happens to be non-misleading, but still written as `some` (not `=1`), since it's still two distinct sites |
| `GarnetStructure` | La-site: 8-fold **dodecahedral** (not in the existing 8-individual vocabulary); Zr-site: octahedral; Li-sites: mixed tetrahedral/octahedral/distorted 4-fold | Per the LLZO literature already checked for the space-group verification | **Not proposed** — the dominant A-site geometry (dodecahedral) has no existing `CoordinationGeometry` individual, and the Li-sites are too heterogeneous to safely characterize with one relation |
| `NASICONStructure`, `LGPSTypeStructure`, `ArgyroditeStructure` | Not independently verified this pass | — | **Not proposed** |

**Recommendation for this whole group: Category B (ADD AFTER HUMAN VERIFICATION)**, not "definitely add" — even the well-established textbook cases weren't run through the same live-search verification discipline as the space-group facts were, and `GarnetStructure`'s case surfaces a real vocabulary gap (no dodecahedral `CoordinationGeometry` individual exists) that shouldn't be silently worked around by omission without flagging it. All restrictions, if added, would be `someValuesFrom` (never `allValuesFrom`, never cardinality) — every family here has ≥2 crystallographically distinct sites, so a single/exact/universal claim would be scientifically wrong.

### 2.3 `hasSiteType` — investigated, not proposed

No existing `SiteType` concept exists, and none is needed: `Site`'s existing relations (`hasSpecies`, `hasCoordinationGeometry`) already express everything a "type" label would add, at the instance level. Inventing a class-level `StructureFamily→Site` relation would either (a) duplicate `hasCoordinationGeometry` under a different name, or (b) conflate a class-level generalization with instance-level `Site` data. **Not recommended (D).**

### 2.4 `StructureFamily → CrystalStructure` — already adequately expressed

The existing `hasStructureFamily` (domain `CrystalStructure`, range `StructureFamily`) already expresses this relationship correctly, with the `CrystalStructure ⊑ ∃hasStructureFamily.StructureFamily` restriction already in place. No additional relation needed — adding one would duplicate the subclass/instantiation semantics already present. **Not recommended (D).**

### 2.5 `SpaceGroup` datatype properties

`hasSpaceGroupNumber`/`hasSymmetrySymbol` already exist and are now populated on the 3 new individuals (`Ia3dIndividual`=230, `PnmaIndividual`=62, `Fd3mIndividual`=227) from the previous applied change. No further action needed here.

---

## Phase 3 — BatteryRole semantic enrichment

### 3.1 `BatteryCell → BatteryRole` — already resolved

Already applied via `emmo:hasRole` in the previous pass (not `hasComponentRole`/`hasBatteryRole` — those would have duplicated an existing, better-fitting EMMO property). **No further action.**

### 3.2 `BatteryRole → physical bearer` — already fully expressed, no new property needed

`usesMaterial` (`BatteryRole→ChemicalSubstance`) **is** the role-to-bearer relation the task is asking about. Inventing `isRoleOf`/`roleBearer` now would be a direct duplicate — violates Critical Rule #3. **Not recommended (D — already satisfied).**

### 3.3 / 3.4 `PositiveElectrodeRole`/`NegativeElectrodeRole → Electrode`

**Not recommended.** EMMO's `Electrode` class (`electrochemistry_0f007072...`) is a physical-component category, not a role category — connecting `PositiveElectrodeRole` to it (via subsumption or equivalence) would collapse exactly the role/bearer distinction Critical Rule #9 requires preserving. The ontology already has the correct, looser bridge: `skos:closeMatch` from each role class to EMMO domain-electrochemistry's *polarity-based* classes (`NegativeElectrode`/`PositiveElectrode`), deliberately **not** the *current-direction-based* `Anode`/`Cathode` classes — this was verified in an earlier session pass specifically to preserve correct rechargeable-battery semantics (Critical Rule #10). No change needed; this is already correct.

### 3.5 `ElectrolyteRole → Electrolyte`

**Not recommended.** No dedicated `Electrolyte` class exists anywhere in the imports (§Phase 1.A) — `hasElectrolyte`'s range is generic `emmo:Substance`. Connecting to that generic class would add no real information beyond what `usesMaterial`'s existing `ChemicalSubstance` range already provides (`ChemicalSubstance ⊑ Substance` transitively). `BatteryCell → ElectrolyteRole → usesMaterial → ChemicalSubstance` is already fully expressible via the applied Model B (§Phase 4).

### 3.6 `SeparatorRole → Separator`

**Not recommended**, same reasoning — no dedicated `Separator` class exists; `hasSeparator`'s range is generic `emmo:PhysicalObject`, which adds nothing over the existing `ChemicalSubstance`-typed path.

### 3.7 `ActiveMaterialRole`

**Recommend: DO NOT CREATE.** "Active material" is, in the existing model, simply "the `ChemicalSubstance` that a `PositiveElectrodeRole`/`NegativeElectrodeRole` individual `usesMaterial`" — there is no additional concept here that isn't already expressible. Creating a 5th `BatteryRole` subclass would either (a) duplicate the existing electrode roles under a new name, or (b) require deciding whether "active material" is a role *distinct from* "positive/negative electrode role," which isn't scientifically justified — the active material *is* the material playing the electrode role, not a separate role. This directly matches EMMO's own `hasActiveMaterial` property, whose domain is "an electrode or other functional component" and range is `Substance` — i.e. EMMO itself doesn't model "active material" as a role either, it's a direct component→substance relation, which `usesMaterial` already mirrors at the role level.

---

## Phase 4 — Material ↔ BatteryCell integration

### 4.1 Existing relations audit

Confirmed by direct grep before any of this session's changes: **zero** properties connected `BatteryCell` to any material/role concept. After the previously-applied change: exactly one, `emmo:hasRole` (via the restriction on `BatteryCell`).

### 4.2 Model comparison

| Model | Description | Verdict |
|---|---|---|
| **A** — `BatteryCell —hasMaterial→ ChemicalSubstance` (direct) | Skips the role layer entirely | **Rejected.** Loses which functional role (positive/negative/electrolyte/separator) a material serves in that specific cell — the entire reason `BatteryRole` exists. Would be a regression against the ontology's own documented design intent. |
| **B** — `BatteryCell —hasRole→ BatteryRole —usesMaterial→ ChemicalSubstance` | Functional-role mediation | **Already applied** (previous session pass). Preserves cell/role/material distinction; reuses EMMO's `Role`/`Whole`/`hasRole` mechanism with zero new properties. |
| **C** — `BatteryCell —hasComponent→ Electrode/Electrolyte/Separator —usesMaterial→ ChemicalSubstance` | Physical-component mediation, using EMMO's own `hasComponent`/`hasElectrode`/`hasElectrolyte`/`hasSeparator` | **Valid, EMMO-native alternative — but a different modeling dimension** (physical decomposition, not functional role), and not needed to satisfy this task's objective, which Model B already does. Flagged as future/optional work, not proposed now — adding it would be scope creep, and per Phase 4's own framing ("do NOT add redundant edges merely for connectivity"), stacking Model C on top of an already-sufficient Model B is exactly the redundancy to avoid unless a genuine use case for the physical-component dimension specifically emerges. |

**Recommendation: keep Model B as the sole material↔cell path. Do not add Model A or C.**

### 4.3 Cardinality analysis — the core of Phase 6, addressed here in full

| Relation | Existence (min 1) justified? | Exactly-1 justified? | Reasoning |
|---|---|---|---|
| `BatteryCell → PositiveElectrodeRole` | **Yes** — a functioning cell requires a positive electrode by definition | **No** | Blended/composite cathodes (e.g. NMC+LMO physical mixtures) are common in real battery engineering — a cell can have more than one `PositiveElectrodeRole`-typed material. |
| `BatteryCell → NegativeElectrodeRole` | **Yes** | **No** | Same reasoning — composite anodes (e.g. graphite+silicon blends) are common. |
| `BatteryCell → ElectrolyteRole` | **Yes** — no ionic transport, no functioning cell | **No** | Dual-salt electrolytes, composite polymer-ceramic electrolytes, and liquid+SEI systems mean more than one electrolyte-role material can coexist. |
| `BatteryCell → SeparatorRole` | **No** — genuinely optional | N/A | All-solid-state cells can use the solid electrolyte itself as the physical separator, with no distinct separator component. `BatteryCell`'s own EMMO definition already hedges this: *"...and **usually** separators"* — not "always." This is textual evidence directly against making this required. |
| `BatteryCell → ActiveMaterialRole` | N/A | N/A | Class doesn't exist and isn't being created (§3.7). |

**Conclusion: existence (`some`) restrictions are justified for `PositiveElectrodeRole`, `NegativeElectrodeRole`, and `ElectrolyteRole` specifically (not just generic `BatteryRole`, which is already covered) — see Phase 8's proposal table. None should be `SeparatorRole`-specific, and none should use `owl:qualifiedCardinality` anywhere in this group; every one of them has a real, identified counter-example to "exactly one."**

### 4.4 Material-specific role restrictions (`PositiveElectrodeRole→Electrode` etc.)

Already addressed in §3.3–3.6: **none recommended**, for the same role/bearer-conflation reason in each case.

---

## Phase 5 — Systematic restriction search (categories 1–8)

| Class | Candidate | Category | Verdict |
|---|---|---|---|
| `CrystalBond` | `∃hasSourceSite.Site`, `∃hasTargetSite.Site` | 1 (Required existence) | **Already present.** Confirmed correct, no change. |
| `CrystalBond` | exactly-1 source / exactly-1 target | 4 (Exact cardinality) | Scientifically true (a directed bond has exactly one source and one target) but adds no operational value over the existing `some` restriction and costs EL-compatibility for no real gain — **Category C, optional, not recommended to add.** |
| `Species` | `∃hasElement.ChemicalElement` | 1 | Already present, correct. |
| `Site` | `∃hasSpecies.Species` | 1 | Already present, correct. |
| `Site` | exactly-1 `hasSpecies` | 4 | **Not recommended.** Mixed/partial-occupancy sites (e.g. Ni/Mn/Co sharing one site in NMC cathodes) are common in real battery materials — forcing exactly-1 would exclude valid data. This is a textbook case of Rule 7's open-world test correctly blocking a tempting-looking constraint. |
| `CrystalStructure` | `∃hasSpaceGroup`, `∃hasUnitCell`, `∃hasCrystalSystem`, `∃hasStructureFamily` | 1 | Already present, correct. |
| `StructureFamily` (leaves) | `hasValue` space group (Garnet/Olivine/Spinel) | 2 (Optional but scientifically characteristic) | Already applied. |
| `BatteryCell` | `∃hasRole.BatteryRole` | 2/1 (arguably required — see §4.3) | Already applied at the generic `BatteryRole` level. |
| `BatteryCell` | `∃hasRole.PositiveElectrodeRole`, `∃hasRole.NegativeElectrodeRole`, `∃hasRole.ElectrolyteRole` | 1 (Required existence, per §4.3) | **New candidate — proposed in Phase 8.** |
| `BatteryCell` | `∃hasRole.SeparatorRole` | 2 (Optional) | **Not proposed as required** — see §4.3. |
| `Electrode`, `Electrolyte`, `Separator` | any restriction | — | No local classes exist for these; nothing to restrict (§Phase 1.A). |
| `ChemicalSubstance` | `∃hasStructure.CrystalStructure` | 1 vs. 4 (UNSAFE if required) | **Not recommended** — already rejected in the prior audit pass; reaffirmed: liquid/amorphous electrolytes are valid substances without a crystal structure. |
| Category 6 (Disjointness) | — | — | Existing 3 `AllDisjointClasses` blocks remain correct and sufficient; no new disjointness identified as needed. |
| Category 7/8 (domain/range, subproperty) | — | — | Already audited in full in the prior report; unchanged. |

---

## Phase 6 — Cardinality requirement (explicit answers to all 11 pairs asked)

1. `BatteryCell → PositiveElectrodeRole`: existence yes, exactly-1 no, multiple allowed yes, zero legitimate no (for a cell modeled in this KG's scope). EL-compatible as `some`.
2. `BatteryCell → NegativeElectrodeRole`: same as #1.
3. `BatteryCell → ElectrolyteRole`: same as #1.
4. `BatteryCell → SeparatorRole`: existence **no** (zero is legitimate — all-solid-state cells), so no restriction proposed.
5. `BatteryCell → ActiveMaterialRole`: not applicable — class not created.
6. `StructureFamily → SpaceGroup`: existence yes for 3 verified families only (already applied via `hasValue`, which permits but doesn't force exclusivity); exactly-1 not applicable (hasValue is not a maxCardinality assertion). EL-compatible.
7. `CrystalStructure → SpaceGroup`: already `some`, correct, unchanged.
8/9. `CrystalBond → source/target Site`: already `some`, correct; exact-1 analyzed and not recommended (§Phase 5).
10. `Site → Species`: already `some`, correct; exact-1 explicitly rejected (mixed occupancy).
11. `ChemicalSubstance → Structure`: no restriction, correct, unchanged.

None of these were forced to cardinality 1 automatically — each was evaluated against a real counter-example before being accepted or rejected, per the task's explicit instruction.

---

## Phase 8 — Final proposal table

| # | Proposed change | Scientific justification | OWL axiom | OWL 2 EL? | Risk | Recommendation |
|---|---|---|---|---|---|---|
| 1 | `BatteryCell ⊑ ∃hasRole.PositiveElectrodeRole` | Every functioning cell modeled in this KG's scope has a positive electrode | `battery:BatteryCell rdfs:subClassOf [ owl:onProperty emmo:hasRole ; owl:someValuesFrom battgpt:PositiveElectrodeRole ]` | Yes | Low | **A — DEFINITELY ADD** |
| 2 | `BatteryCell ⊑ ∃hasRole.NegativeElectrodeRole` | Same reasoning | Same pattern | Yes | Low | **A — DEFINITELY ADD** |
| 3 | `BatteryCell ⊑ ∃hasRole.ElectrolyteRole` | Same reasoning | Same pattern | Yes | Low | **A — DEFINITELY ADD** |
| 4 | `BatteryCell ⊑ ∃hasRole.SeparatorRole` | **Not** universally true (separator-free all-solid-state cells exist) | — | — | High (would exclude valid data) | **D — DO NOT ADD** |
| 5 | `ActiveMaterialRole` new class | Would duplicate existing `PositiveElectrodeRole`/`NegativeElectrodeRole` + `usesMaterial` semantics | — | — | Medium (duplication) | **D — DO NOT ADD** |
| 6 | `isRoleOf`/`roleBearer` new property | Already fully expressed by existing `usesMaterial` | — | — | Medium (duplication) | **D — DO NOT ADD** |
| 7 | `PositiveElectrodeRole`/`NegativeElectrodeRole`/`ElectrolyteRole`/`SeparatorRole → Electrode/Electrolyte/Separator` | Would conflate role category with physical-component category; no dedicated Electrolyte/Separator class exists to target anyway | — | — | Medium (category error) | **D — DO NOT ADD** |
| 8 | `hasCharacteristicCoordinationGeometry` for Perovskite/Spinel/Olivine/LayeredOxide/RockSalt | Scientifically well-established, one live-verified this pass (Perovskite); others textbook-level but not independently re-searched | `StructureFamily rdfs:subClassOf [ owl:onProperty hasCharacteristicCoordinationGeometry ; owl:someValuesFrom CoordinationGeometry ]`, per-family, always `some` | Yes | Low-medium (verification rigor not yet equal to the space-group work) | **B — ADD AFTER HUMAN VERIFICATION** |
| 9 | `hasCharacteristicCoordinationGeometry` for Garnet | A-site geometry (dodecahedral) has no corresponding individual in the existing 8-member vocabulary | — | — | Medium (would need a new `CoordinationGeometry` individual first) | **E — REQUIRES HUMAN/SCIENTIFIC DECISION** (does the vocabulary need a 9th geometry individual?) |
| 10 | `CrystalBond`/`Site` exact-cardinality tightening | Scientifically true in the narrow case, but excludes valid mixed-occupancy data (`Site`) or adds no value over `some` (`CrystalBond`) | — | — | High for `Site`, low-but-pointless for `CrystalBond` | **D — DO NOT ADD** |
| 11 | Model C (`hasComponent`-based physical decomposition) | Valid EMMO-native alternative, but a different modeling dimension not needed to meet this task's objective | — | — | Low (but scope creep) | **C — OPTIONAL / future work** |

**Only items #1–3 are proposed for actual application. Everything else in this table is either already correctly absent, already correctly present, or requires further verification/decision before any Turtle is written.**
