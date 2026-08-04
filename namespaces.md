# Namespace Registry - Battery Materials Knowledge Graph

This document details all namespaces, prefixes, and IRIs integrated into the Battery Materials Knowledge Graph foundation.

## 1. Overview & Strategy

The Knowledge Graph schema follows a strict semantic hierarchy:
1. **EMMO Core & Domain Ontologies**: Authoritative sources for foundational physical science, materials, chemical entities, crystallographic structures, and electrochemical processes.
2. **BattINFO Application Ontology**: Pinned application ontology for battery domain concepts, cell specifications, test protocols, and record structures.
3. **Lightweight Custom Namespace (`battgpt:`)**: `https://w3id.org/battgpt/kg#` reserved exclusively for non-existing predicates (properties and edge types). **No OWL classes are defined in `battgpt:`**.
4. **Standard W3C / OBO Ontologies**: Reused for provenance (`prov:`), administrative metadata (`dcterms:`), quantities/units (`qudt:`, `unit:`), and controlled vocabularies (`skos:`).
5. **External Data Provider Namespaces**: Virtual namespace identifiers for Materials Project, Pymatgen, and SMACT entities.

---

## 2. Master Namespace Prefix Table

| Prefix | Full IRI | Source Ontology / Standard | Usage Context & Purpose | Import Status |
| :--- | :--- | :--- | :--- | :--- |
| `emmo` | `https://w3id.org/emmo#` | EMMO Core (v1.0.0) | Top-level physical objects, properties, quantities, spatial parts | Reused (Core) |
| `chsub` | `https://w3id.org/emmo/domain/chemical-substance#` | EMMO Chemical Substance | Chemical entities, substances, atomic species, elements | Reused (Domain) |
| `elchem` | `https://w3id.org/emmo/domain/electrochemistry#` | EMMO Electrochemistry | Electrochemical quantities, potentials, capacity, cell kinetics | Reused (Domain) |
| `battery` | `https://w3id.org/emmo/domain/battery#` | EMMO Domain Battery | Battery cells, electrodes (cathode/anode), electrolytes, separators | Reused (Domain) |
| `cryst` | `https://w3id.org/emmo/domain/crystallography#` | EMMO Domain Crystallography | Crystals, unit cells, atomic sites, crystal systems, space groups | Reused (Domain) |
| `battinfo` | `https://w3id.org/battinfo#` (App) / `<https://w3id.org/battinfo/>` (Record) | BattINFO Ecosystem | Battery record layer, test specifications, conformance vocabularies | Reused (App/Record) |
| `battgpt` | `https://w3id.org/battgpt/kg#` | **BattGPT Custom KG** | **Lightweight predicates ONLY** (e.g. `hasBandGap`, `hasFormationEnergy`) | Custom Predicates |
| `mp` | `https://materialsproject.org/materials/` | Materials Project | Entity URIs for MP materials (e.g. `mp:mp-19017`) | External Identifiers |
| `pymatgen` | `https://w3id.org/battgpt/kg/pymatgen#` | Pymatgen Metadata | Property identifiers for Pymatgen structures & symmetry output | Structural Engine |
| `smact` | `https://w3id.org/battgpt/kg/smact#` | SMACT Metadata | Property identifiers for SMACT oxidation states & stoichiometry rules | Chemical Engine |
| `qudt` | `http://qudt.org/schema/qudt/` | QUDT Schema | Quantity types, unit definitions, dimension vectors | Standard Reused |
| `unit` | `http://qudt.org/vocab/unit/` | QUDT Units | Measurement units (eV, eV/atom, Å, g/cm³, mAh/g, V) | Standard Reused |
| `schema` | `https://schema.org/` | Schema.org | Basic descriptive metadata (name, model, manufacturer) | Standard Reused |
| `dcterms` | `http://purl.org/dc/terms/` | Dublin Core Terms | Bibliographic and record provenance metadata | Standard Reused |
| `prov` | `http://www.w3.org/ns/prov#` | W3C PROV-O | Data derivation, activity tracing, calculation provenance | Standard Reused |
| `skos` | `http://www.w3.org/2004/02/skos/core#` | W3C SKOS | Controlled vocabularies, concept schemes, conformance status | Standard Reused |
| `rdf` | `http://www.w3.org/1999/02/22-rdf-syntax-ns#` | W3C RDF | Basic triples, types, RDF properties | Core Standard |
| `rdfs` | `http://www.w3.org/2000/01/rdf-schema#` | W3C RDFS | Subclasses, subproperties, domain/range definitions, labels | Core Standard |
| `owl` | `http://www.w3.org/2002/07/owl#` | W3C OWL 2 | Object properties, datatype properties, ontology declarations | Core Standard |
| `xsd` | `http://www.w3.org/2001/XMLSchema#` | W3C XML Schema | Datatypes (`xsd:double`, `xsd:integer`, `xsd:string`, `xsd:boolean`) | Core Standard |

---

## 3. Custom Namespace Rules (`battgpt:`)

1. **IRI Base**: `https://w3id.org/battgpt/kg#`
2. **Class Restriction**: Under no circumstances shall `battgpt:` define `owl:Class` or `rdfs:Class` entities. All node entities in the graph must instantiate existing classes from `emmo:`, `chsub:`, `cryst:`, `battery:`, `elchem:`, `battinfo:`, or standard W3C ontologies.
3. **Property Restriction**: `battgpt:` contains ONLY `owl:ObjectProperty`, `owl:DatatypeProperty`, or `rdf:Property` definitions for domain relationships and properties not covered by EMMO/BattINFO.
