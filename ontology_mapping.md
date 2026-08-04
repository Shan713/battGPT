# Ontology Mapping - Battery Materials Knowledge Graph

This document provides a detailed mapping between the Battery Materials Knowledge Graph concept layer, existing ontologies (EMMO Core, EMMO Chemical Substance, EMMO Electrochemistry, EMMO Crystallography, BattINFO, PROV-O, QUDT), lightweight custom predicates (`battgpt:`), and external battery material databases and computational engines (Materials Project, Pymatgen, SMACT).

---

## 1. Node Types Mapping

All node entities in the knowledge graph instantiate existing OWL classes from imported ontologies. **No custom classes are created in `battgpt:`**.

| Knowledge Graph Node Type | Canonical Ontology Class IRI / Term | Source Ontology | Description |
| :--- | :--- | :--- | :--- |
| **Material** | `emmo:EMMO_4207e895_8bfe_4b08_8e2d_dd53af54e10b` / `chsub:Substance` | EMMO Core / Chemical Substance | A material or chemical substance used in energy storage components |
| **ChemicalEntity** | `chsub:ChemicalEntity` | EMMO Chemical Substance | Molecular or formulaic chemical composition entity |
| **AtomicSpecies** | `chsub:AtomicSpecies` | EMMO Chemical Substance | Specific chemical element with defined oxidation state or ion state |
| **Element** | `chsub:Element` | EMMO Chemical Substance | Chemical element from periodic table (e.g. Li, Ni, Mn, Co, O) |
| **Crystal** | `cryst:Crystal` / `emmo:EMMO_e046edb4_...` | EMMO Crystallography | Periodically ordered solid-state material structure |
| **UnitCell** | `cryst:UnitCell` | EMMO Crystallography | Minimal repeating spatial lattice unit containing basis atoms |
| **AtomicSite** | `cryst:AtomicSite` | EMMO Crystallography | Crystallographic site populated by atomic species with fractional coordinates |
| **SpaceGroup** | `cryst:SpaceGroup` | EMMO Crystallography | Crystallographic space group symmetry definition |
| **CrystalSystem** | `cryst:CrystalSystem` | EMMO Crystallography | Crystal system classification (Cubic, Tetragonal, Orthorhombic, Hexagonal, Trigonal, Monoclinic, Triclinic) |
| **BatteryCell** | `battery:battery_68ed592a_7924_45d0_a108_94d6275d57f0` | EMMO Battery | Physical battery cell device |
| **BatteryCellSpecification** | `battery:battery_1cfbba6c_8824_4932_a23e_2141483acef7` | EMMO Battery | Technical data sheet specification for a battery cell |
| **Electrode** | `battery:battery_179f82fb_...` | EMMO Battery | Battery electrode component |
| **PositiveElectrode** (Cathode) | `battery:battery_b8f04fd5_...` | EMMO Battery | Positive electrode active component (e.g. LCO, NMC811, LFP) |
| **NegativeElectrode** (Anode) | `battery:battery_0a37db91_...` | EMMO Battery | Negative electrode active component (e.g. Graphite, Silicon, Li metal) |
| **Electrolyte** | `battery:battery_b69c4c79_...` | EMMO Battery | Ion-conducting electrolyte phase (liquid, gel, or solid ceramic/polymer) |
| **Separator** | `battery:battery_13e9a59b_...` | EMMO Battery | Porous electronic insulating separator membrane |
| **Property** | `emmo:EMMO_e1097637_70d2_4895_973f_2396f04fa204` | EMMO Core | Observable or calculated attribute of a material or physical system |
| **PhysicalQuantity** | `emmo:EMMO_a4b99a9a_3950_4fee_a1e3_b9e59d9c22d1` | EMMO Core | Quantity with numerical value and measurement unit |
| **Measurement** / **Calculation** | `emmo:EMMO_463bcfda_...` / `emmo:EMMO_d8435882_...` | EMMO Core | Process or workflow producing quantitative property data |
| **MeasurementUnit** | `emmo:EMMO_bed1d005_b04e_4a90_94cf_02bc678a8569` | EMMO Core / QUDT | Unit of measurement (e.g. `unit:EV`, `unit:ANGSTROM`, `unit:G-PER-CentiM3`) |
| **SynthesizedSample** | `prov:Entity` / `emmo:Material` | PROV-O / EMMO | Physical synthesized material batch or specimen |

---

## 2. Edge Types (Object Properties) Mapping

Relationships between nodes reuse EMMO properties where available, falling back to `battgpt:` predicates for domain-specific relationships.

| Knowledge Graph Edge Type | Source Term / IRI | Source Ontology | Domain | Range | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `hasProperty` | `emmo:EMMO_e1097637_70d2_4895_973f_2396f04fa204` | EMMO Core | `Material` / `BatteryCell` | `Property` | Connects material or cell to a property entity |
| `hasNumericalPart` | `emmo:EMMO_8ef3cd6d_ae58_4a8d_9fc0_ad8f49015cd0` | EMMO Core | `Property` | `emmo:Real` | Connects property to numerical value holder |
| `hasMeasurementUnit` | `emmo:EMMO_bed1d005_b04e_4a90_94cf_02bc678a8569` | EMMO Core | `Property` | `MeasurementUnit` | Links quantity to unit of measure |
| `hasStructure` | `battgpt:hasStructure` | `battgpt:` | `Material` | `Crystal` | Connects material to crystallographic structure |
| `containsSite` | `battgpt:containsSite` | `battgpt:` | `UnitCell` | `AtomicSite` | Connects unit cell to atomic site |
| `containsSpecies` | `battgpt:containsSpecies` | `battgpt:` | `AtomicSite` | `AtomicSpecies` | Connects atomic site to atomic species occupying it |
| `hasElement` | `battgpt:hasElement` | `battgpt:` | `AtomicSpecies` | `Element` | Connects atomic species to periodic element |
| `hasUnitCell` | `battgpt:hasUnitCell` | `battgpt:` | `Crystal` | `UnitCell` | Connects crystal to its repeating unit cell |
| `hasSpaceGroup` | `battgpt:hasSpaceGroup` | `battgpt:` | `Crystal` | `SpaceGroup` | Connects crystal to space group symmetry |
| `hasCrystalSystem` | `battgpt:hasCrystalSystem` | `battgpt:` | `Crystal` | `CrystalSystem` | Connects crystal to crystal system classification |
| `hasBandGap` | `battgpt:hasBandGap` | `battgpt:` | `Material` / `Crystal` | `Property` | Connects material/crystal to electronic band gap |
| `hasFormationEnergy` | `battgpt:hasFormationEnergy` | `battgpt:` | `Material` / `Crystal` | `Property` | Connects material/crystal to DFT formation energy |
| `hasEnergyAboveHull` | `battgpt:hasEnergyAboveHull` | `battgpt:` | `Material` / `Crystal` | `Property` | Connects material/crystal to thermodynamic energy above convex hull |
| `hasCoordinationGeometry`| `battgpt:hasCoordinationGeometry` | `battgpt:` | `AtomicSite` | `Property` | Connects atomic site to polyhedral coordination environment |
| `usesMaterial` | `battgpt:usesMaterial` | `battgpt:` | `Electrode` / `Electrolyte` | `Material` | Connects component to constituent material |
| `belongsToElectrode` | `battgpt:belongsToElectrode` | `battgpt:` | `Material` | `Electrode` | Inverse connection from material to electrode |
| `hasInput` | `emmo:EMMO_36e69413_...` | EMMO Core | `Measurement` / `Calculation` | `Material` | Connects calculation/measurement process to input |
| `hasOutput` | `emmo:EMMO_c4bace1d_...` | EMMO Core | `Measurement` / `Calculation` | `Property` | Connects process to output property |
| `wasDerivedFrom` | `prov:wasDerivedFrom` | PROV-O | `Material` / `Property` | `Material` / `Property` | Traces material/property lineage and derivation |

---

## 3. Datatype Properties Mapping

Literal scalar attributes associated with nodes or property entities.

| Datatype Property | Source Term / IRI | Datatype | Applicable Nodes | Description |
| :--- | :--- | :--- | :--- | :--- |
| `hasNumberValue` | `emmo:EMMO_faf79f53_749d_40b2_807c_d34244c192f4` | `xsd:double` | `Property` | Scalar numeric value |
| `battgpt:hasFormula` | `battgpt:hasFormula` | `xsd:string` | `Material`, `ChemicalEntity` | Reduced or IUPAC chemical formula (e.g. `"LiNi0.8Mn0.1Co0.1O2"`) |
| `battgpt:hasMaterialProjectId` | `battgpt:hasMaterialProjectId` | `xsd:string` | `Material`, `Crystal` | Materials Project ID (e.g. `"mp-19017"`) |
| `battgpt:hasSymmetrySymbol` | `battgpt:hasSymmetrySymbol` | `xsd:string` | `SpaceGroup` | Hermann-Mauguin space group symbol (e.g. `"R-3m"`, `"Fd-3m"`) |
| `battgpt:hasSpaceGroupNumber` | `battgpt:hasSpaceGroupNumber` | `xsd:integer` | `SpaceGroup` | International space group number (1 to 230) |
| `battgpt:hasLatticea` | `battgpt:hasLatticea` | `xsd:double` | `UnitCell` | Lattice parameter *a* in Ångströms |
| `battgpt:hasLatticeb` | `battgpt:hasLatticeb` | `xsd:double` | `UnitCell` | Lattice parameter *b* in Ångströms |
| `battgpt:hasLatticec` | `battgpt:hasLatticec` | `xsd:double` | `UnitCell` | Lattice parameter *c* in Ångströms |
| `battgpt:hasAlpha` | `battgpt:hasAlpha` | `xsd:double` | `UnitCell` | Lattice angle α in degrees |
| `battgpt:hasBeta` | `battgpt:hasBeta` | `xsd:double` | `UnitCell` | Lattice angle β in degrees |
| `battgpt:hasGamma` | `battgpt:hasGamma` | `xsd:double` | `UnitCell` | Lattice angle γ in degrees |
| `battgpt:hasFractionalX` | `battgpt:hasFractionalX` | `xsd:double` | `AtomicSite` | Fractional coordinate *x* |
| `battgpt:hasFractionalY` | `battgpt:hasFractionalY` | `xsd:double` | `AtomicSite` | Fractional coordinate *y* |
| `battgpt:hasFractionalZ` | `battgpt:hasFractionalZ` | `xsd:double` | `AtomicSite` | Fractional coordinate *z* |
| `battgpt:hasOxidationState` | `battgpt:hasOxidationState` | `xsd:integer` | `AtomicSpecies` | Formal oxidation state (e.g. `+3`, `+4`, `-2`) |
| `battgpt:hasElectronegativity` | `battgpt:hasElectronegativity` | `xsd:double` | `Element` | Pauling electronegativity scale value |
| `battgpt:hasSmactValidity` | `battgpt:hasSmactValidity` | `xsd:boolean` | `ChemicalEntity` | SMACT charge balance and neutrality validity flag |
| `battgpt:isStable` | `battgpt:isStable` | `xsd:boolean` | `Material`, `Crystal` | Thermodynamic convex hull stability flag (`true` if energy_above_hull == 0) |

---

## 4. External Software & Database Alignment

### 4.1 Materials Project (MP) Integration
Materials Project data items map into RDF graph structures as follows:
- `material_id` → Entity identifier `mp:<material_id>` + property `battgpt:hasMaterialProjectId`.
- `formula_pretty` → `battgpt:hasFormula` literal on `Material`.
- `band_gap` → `Property` linked via `battgpt:hasBandGap` with `unit:EV`.
- `formation_energy_per_atom` → `Property` linked via `battgpt:hasFormationEnergy` with `unit:EV-PER-NUM`.
- `energy_above_hull` → `Property` linked via `battgpt:hasEnergyAboveHull` with `unit:EV-PER-NUM`.
- `density` → `Property` linked via `emmo:hasProperty` with `unit:G-PER-CentiM3`.
- `symmetry` → Node `SpaceGroup` with `battgpt:hasSymmetrySymbol` and `battgpt:hasSpaceGroupNumber`.

### 4.2 Pymatgen Integration
Pymatgen objects map into crystallographic graph nodes:
- `pymatgen.core.Structure` → `cryst:Crystal` node.
- `pymatgen.core.Lattice` → `cryst:UnitCell` node with `battgpt:hasLatticea...gamma` parameters.
- `pymatgen.core.PeriodicSite` → `cryst:AtomicSite` node with `battgpt:hasFractionalX...Z`.
- `pymatgen.core.Element` / `Specie` → `chsub:AtomicSpecies` and `chsub:Element` nodes.
- `pymatgen.analysis.chemenv` → `Property` node linked via `battgpt:hasCoordinationGeometry`.

### 4.3 SMACT Integration
SMACT (Semiconducting Materials Automated Archetype Creation Toolkit) data items map into neutrality & composition nodes:
- Neutrality & Charge Balance Checks → `battgpt:hasSmactValidity` (`xsd:boolean`).
- Allowed Oxidation States → `battgpt:hasOxidationState` on `chsub:AtomicSpecies`.
- Electronegativity Differences → `battgpt:hasElectronegativity` on `chsub:Element`.
