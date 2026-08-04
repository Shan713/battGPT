# Master RDF Schema Specification - Battery Materials Knowledge Graph

This document serves as the master RDF Schema specification for the Battery Materials Knowledge Graph. It integrates foundational ontologies (**BattINFO**, **EMMO Core**, **EMMO Chemical Substance**, **EMMO Electrochemistry**, **EMMO Crystallography**) with external material science engines (**Materials Project**, **Pymatgen**, **SMACT**) and defines a lightweight predicate namespace (`battgpt:`) to support graph neural network (GNN) embeddings and downstream injection into **CrystalLLM**.

---

## 1. BattINFO Repository Exploration & Architectural Context

### 1.1 Repo Findings Summary
An inspection of the BattINFO repository (`/Users/shantharam/FYP/battGPT/battinfo/battinfo`) reveals the following semantic foundation:

1. **Import Manifest & Dependency Pinnings (`battinfo.ttl`)**:
   - `battinfo:` is an application/profile ontology (`owl:Ontology`) acting as an import manifest and pinning upstream EMMO modules.
   - Pinned EMMO imports:
     - `owl:imports <https://w3id.org/emmo/domain/battery/0.19.0/battery>`
     - `owl:imports <https://w3id.org/emmo/domain/electrochemistry/0.34.0/electrochemistry>`
     - Transitive EMMO imports: `domain-chemical-substance`, `domain-crystallography`, `emmo-core`.

2. **Namespaces & Vocabularies**:
   - **Hash Namespace**: `https://w3id.org/battinfo#` for the application ontology.
   - **Slash Namespace**: `https://w3id.org/battinfo/` for record-layer vocabulary terms and placeholders (e.g. `battinfo:capacityThresholdExhaustion`, `battinfo:cycleLifeCRate`, `battinfo:operatingTemperatureMax`).
   - SKOS Concept Scheme: `<https://w3id.org/battinfo/ConformanceStatus>` with concepts (`Conformant`, `PartialConformance`, `NonConformant`, `ConformanceUnknown`).

3. **Context Files & JSON-LD Generation**:
   - Context files located at `src/battinfo/data/context/records.context.json` mapping JSON keys to EMMO IRIs.
   - `src/battinfo/jsonld.py` provides `record_to_jsonld()`, mapping canonical record schema types (`cell-spec`, `cell-instance`, `test`, `dataset`) into JSON-LD graphs via curated mapping tables (`property_map.curated.json`, `unit_map.curated.json`, `entity_type_map.json`).

4. **Reusable Classes**:
   - EMMO Core: `EMMO_4207e895_8bfe_4b08_8e2d_dd53af54e10b` (`Material`), `EMMO_e1097637_70d2_4895_973f_2396f04fa204` (`hasProperty`), `EMMO_8ef3cd6d_ae58_4a8d_9fc0_ad8f49015cd0` (`hasNumericalPart`), `EMMO_bed1d005_b04e_4a90_94cf_02bc678a8569` (`hasMeasurementUnit`), `EMMO_faf79f53_749d_40b2_807c_d34244c192f4` (`hasNumberValue`).
   - EMMO Battery: `BatteryCell`, `BatteryCellSpecification`, `PositiveElectrode`, `NegativeElectrode`, `Electrolyte`, `Separator`, `BatteryTest`.

---

## 2. Knowledge Graph Architecture & GNN Integration Strategy

```
  [ EMMO / BattINFO Ontologies ]       [ External Computational Tools ]
    (Core, Chem, Elchem, Cryst)          (Materials Project, Pymatgen, SMACT)
                 │                                        │
                 └───────────────────┬────────────────────┘
                                     ▼
                      [ Semantic Graph Schema Layer ]
                      (Node Types & battgpt: Predicates)
                                     │
                                     ▼
                   [ Heterogeneous RDF Knowledge Graph ]
                                     │
                                     ▼
                 [ PyTorch Geometric / Hetero-GNN Encoder ]
                                     │
                                     ▼
                 [ Graph Embeddings -> CrystalLLM Injection ]
```

The primary objective of this RDF schema is to define a multi-relational, heterogeneous graph structure. Every entity node (Material, Crystal, UnitCell, AtomicSite, Element, Electrode, Property) has a strict semantic class from EMMO or BattINFO. Relations and scalar attributes use either EMMO properties or `battgpt:` predicates.

---

## 3. Node Specifications

The Knowledge Graph consists of 14 primary Node Types:

### 3.1 Material
- **Ontology Class**: `chsub:Substance` / `emmo:EMMO_4207e895_8bfe_4b08_8e2d_dd53af54e10b`
- **Description**: Bulk material, solid-state compound, active material, or electrolyte phase.
- **Outgoing Edges**: `battgpt:hasStructure` → `Crystal`, `emmo:hasProperty` → `Property`, `battgpt:belongsToElectrode` → `Electrode`.
- **Datatype Properties**: `battgpt:hasFormula`, `battgpt:hasMaterialProjectId`, `battgpt:isStable`.

### 3.2 Crystal
- **Ontology Class**: `cryst:Crystal` / `emmo:EMMO_e046edb4_...`
- **Description**: Periodic 3D crystal structure representation.
- **Outgoing Edges**: `battgpt:hasUnitCell` → `UnitCell`, `battgpt:hasSpaceGroup` → `SpaceGroup`, `battgpt:hasCrystalSystem` → `CrystalSystem`, `battgpt:hasBandGap` → `Property`, `battgpt:hasFormationEnergy` → `Property`, `battgpt:hasEnergyAboveHull` → `Property`.
- **Datatype Properties**: `battgpt:hasMaterialProjectId`.

### 3.3 UnitCell
- **Ontology Class**: `cryst:UnitCell`
- **Description**: Geometric unit cell containing lattice vectors, cell volume, and atomic site positions.
- **Outgoing Edges**: `battgpt:containsSite` → `AtomicSite`.
- **Datatype Properties**: `battgpt:hasLatticea`, `battgpt:hasLatticeb`, `battgpt:hasLatticec`, `battgpt:hasAlpha`, `battgpt:hasBeta`, `battgpt:hasGamma`.

### 3.4 AtomicSite
- **Ontology Class**: `cryst:AtomicSite`
- **Description**: Specific crystallographic coordinate site occupied by one or more atomic species.
- **Outgoing Edges**: `battgpt:containsSpecies` → `AtomicSpecies`, `battgpt:hasCoordinationGeometry` → `Property`.
- **Datatype Properties**: `battgpt:hasFractionalX`, `battgpt:hasFractionalY`, `battgpt:hasFractionalZ`.

### 3.5 AtomicSpecies
- **Ontology Class**: `chsub:AtomicSpecies`
- **Description**: Chemical element in a specific oxidation state or ionic state occupying a site.
- **Outgoing Edges**: `battgpt:hasElement` → `Element`.
- **Datatype Properties**: `battgpt:hasOxidationState`.

### 3.6 Element
- **Ontology Class**: `chsub:Element`
- **Description**: Fundamental chemical element from the periodic table.
- **Datatype Properties**: `battgpt:hasAtomicNumber`, `battgpt:hasSymbol`, `battgpt:hasElectronegativity`.

### 3.7 SpaceGroup
- **Ontology Class**: `cryst:SpaceGroup`
- **Description**: Crystallographic space group symmetry definition.
- **Datatype Properties**: `battgpt:hasSymmetrySymbol`, `battgpt:hasSpaceGroupNumber`.

### 3.8 CrystalSystem
- **Ontology Class**: `cryst:CrystalSystem`
- **Description**: Crystal system classification (Cubic, Hexagonal, Monoclinic, etc.).
- **Datatype Properties**: `rdfs:label`.

### 3.9 BatteryCell
- **Ontology Class**: `battery:battery_68ed592a_7924_45d0_a108_94d6275d57f0`
- **Description**: Complete battery cell device.
- **Outgoing Edges**: `battery:hasPositiveElectrode` → `PositiveElectrode`, `battery:hasNegativeElectrode` → `NegativeElectrode`, `battery:hasElectrolyte` → `Electrolyte`, `emmo:hasProperty` → `Property`.

### 3.10 Electrode (PositiveElectrode / NegativeElectrode)
- **Ontology Class**: `battery:battery_179f82fb_...` (`PositiveElectrode`: `battery_b8f04fd5_...`, `NegativeElectrode`: `battery_0a37db91_...`)
- **Description**: Battery electrode component.
- **Outgoing Edges**: `battgpt:usesMaterial` → `Material`, `emmo:hasProperty` → `Property`.

### 3.11 Electrolyte
- **Ontology Class**: `battery:battery_b69c4c79_...`
- **Description**: Battery electrolyte phase.
- **Outgoing Edges**: `battgpt:usesMaterial` → `Material`.

### 3.12 Property / PhysicalQuantity
- **Ontology Class**: `emmo:EMMO_e1097637_70d2_4895_973f_2396f04fa204` / `emmo:EMMO_a4b99a9a_3950_4fee_a1e3_b9e59d9c22d1`
- **Description**: Quantified physical, electronic, thermodynamic, or electrochemical property.
- **Outgoing Edges**: `emmo:hasMeasurementUnit` → `MeasurementUnit`.
- **Datatype Properties**: `emmo:hasNumberValue` (`xsd:double`).

### 3.13 MeasurementUnit
- **Ontology Class**: `emmo:EMMO_bed1d005_b04e_4a90_94cf_02bc678a8569` / `qudt:Unit`
- **Description**: Unit of measurement (e.g. `unit:EV`, `unit:ANGSTROM`, `unit:G-PER-CentiM3`).
- **Datatype Properties**: `rdfs:label`, `qudt:symbol`.

### 3.14 CalculationMethod / Measurement
- **Ontology Class**: `emmo:EMMO_d8435882_...` / `emmo:EMMO_463bcfda_...`
- **Description**: Computation (DFT, PBE+U) or experimental measurement method producing data.
- **Outgoing Edges**: `emmo:hasInput` → `Material`/`Crystal`, `emmo:hasOutput` → `Property`.

---

## 4. Edge Types (Object Properties) Specifications

All custom edge predicates are defined under `battgpt:` (`https://w3id.org/battgpt/kg#`).

1. `battgpt:hasStructure` (Domain: `Material`, Range: `Crystal`)
2. `battgpt:hasUnitCell` (Domain: `Crystal`, Range: `UnitCell`)
3. `battgpt:containsSite` (Domain: `UnitCell`, Range: `AtomicSite`)
4. `battgpt:containsSpecies` (Domain: `AtomicSite`, Range: `AtomicSpecies`)
5. `battgpt:hasElement` (Domain: `AtomicSpecies`, Range: `Element`)
6. `battgpt:hasSpaceGroup` (Domain: `Crystal`, Range: `SpaceGroup`)
7. `battgpt:hasCrystalSystem` (Domain: `Crystal`, Range: `CrystalSystem`)
8. `battgpt:hasBandGap` (Domain: `Material`|`Crystal`, Range: `Property`)
9. `battgpt:hasFormationEnergy` (Domain: `Material`|`Crystal`, Range: `Property`)
10. `battgpt:hasEnergyAboveHull` (Domain: `Material`|`Crystal`, Range: `Property`)
11. `battgpt:hasCoordinationGeometry` (Domain: `AtomicSite`, Range: `Property`)
12. `battgpt:usesMaterial` (Domain: `Electrode`|`Electrolyte`, Range: `Material`)
13. `battgpt:belongsToElectrode` (Domain: `Material`, Range: `Electrode`)
14. `emmo:hasProperty` (Domain: `Material`|`BatteryCell`|`Electrode`, Range: `Property`)
15. `emmo:hasMeasurementUnit` (Domain: `Property`, Range: `MeasurementUnit`)
16. `prov:wasDerivedFrom` (Domain: `Material`|`Property`, Range: `Material`|`Property`)

---

## 5. Datatype Properties Specifications

Datatype predicates hold numeric or literal string parameters:

1. `emmo:hasNumberValue`: `xsd:double` (Numeric property magnitude)
2. `battgpt:hasFormula`: `xsd:string` (Chemical formula string)
3. `battgpt:hasMaterialProjectId`: `xsd:string` (Materials Project identifier, e.g. `"mp-19017"`)
4. `battgpt:hasSymmetrySymbol`: `xsd:string` (Hermann-Mauguin space group symbol)
5. `battgpt:hasSpaceGroupNumber`: `xsd:integer` (Space group number 1..230)
6. `battgpt:hasLatticea`, `battgpt:hasLatticeb`, `battgpt:hasLatticec`: `xsd:double` (Lattice parameter lengths in Å)
7. `battgpt:hasAlpha`, `battgpt:hasBeta`, `battgpt:hasGamma`: `xsd:double` (Lattice angles in degrees)
8. `battgpt:hasFractionalX`, `battgpt:hasFractionalY`, `battgpt:hasFractionalZ`: `xsd:double` (Atomic site coordinates)
9. `battgpt:hasOxidationState`: `xsd:integer` (Atomic oxidation number)
10. `battgpt:hasElectronegativity`: `xsd:double` (Pauling scale electronegativity)
11. `battgpt:hasSmactValidity`: `xsd:boolean` (SMACT stoichiometry & charge balance validity)
12. `battgpt:isStable`: `xsd:boolean` (Thermodynamic hull stability indicator)

---

## 6. GNN Subgraph Feature Tensor Mapping

To enable direct ingestion by PyTorch Geometric (`torch_geometric.data.HeteroData`):
- **Node Feature Vectors ($X_v$)**:
  - `Element`: Atomic number, electronegativity, atomic radius, valence electrons.
  - `AtomicSpecies`: Element features + oxidation state.
  - `AtomicSite`: Fractional coordinates $(x,y,z)$, site occupancy, polyhedral coordination number.
  - `UnitCell`: Lattice parameters $(a,b,c,\alpha,\beta,\gamma)$, cell volume.
  - `Crystal` / `Material`: Formula embedding, density, space group number, stability flag.
- **Edge Index Tensors ($E_{u,v}$)**:
  - Directed edge lists constructed for each edge type triplet `(src_type, edge_type, dst_type)`.
