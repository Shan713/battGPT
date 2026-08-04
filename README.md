# Battery Materials Knowledge Graph (battGPT)

A semantic foundation and modular data ingestion pipeline for building a research-grade **Battery Materials Knowledge Graph** integrating **BattINFO**, **EMMO ontologies** (Core, Chemical Substance, Electrochemistry, Crystallography), **Materials Project**, **Pymatgen**, and **SMACT**.

---

## 1. Project Overview

This project constructs a validated RDF Knowledge Graph representing battery materials, crystal structures, unit cell geometry, atomic sites, chemical species, space groups, crystal connectivity graphs, computed physical properties (band gap, formation energy, convex hull stability), and curated battery role semantics.

The Knowledge Graph is designed specifically to serve as the semantic graph layer for downstream Graph Neural Network (GNN) embeddings and **CrystalLLM** integration.

---

## 2. Pipeline Architecture & Modular Structure

The pipeline is completely modular and follows a strict progressive enrichment model:

```
pipeline/
├── config/
│   └── config.py               # Pipeline configuration & deterministic URIScheme
├── data/
│   └── cached_mp_materials.json# Authentic Materials Project dataset snapshot
├── models/
│   └── material_record.py     # Single unified MaterialRecord & SiteData / BondData
├── ingest/
│   └── materials_project.py    # Materials Project API client & authentic dataset loader
├── processing/
│   ├── pymatgen_processor.py   # Pymatgen structure, CrystalNN/VoronoiNN connectivity processor
│   ├── smact_processor.py      # SMACT chemical validity & electronegativity engine
│   └── battinfo_mapper.py      # Curated BattINFO battery role semantic mapper
├── rdf/
│   ├── rdf_builder.py          # Master RDF graph builder and namespace binder
│   ├── triple_generator.py     # RDF triple emitter for material-centric nodes & predicates
│   └── validator.py            # Extended semantic graph validation engine
└── export/
    └── rdf_export.py           # Serialization to Turtle (.ttl), RDF/XML (.rdf), JSON-LD (.jsonld)
```

---

## 3. Key Pipeline Features & Fixes (Stage 2.1 Refactor)

1. **Authentic Materials Project Snapshot** (`pipeline/data/cached_mp_materials.json`): Stores full `pymatgen.core.Structure.as_dict()`, authentic CIF strings, spacegroup symbols/numbers, lattice parameters, and physical properties.
2. **Original Crystallographic Structure Preservation**: Retains CIF strings (`rec.cif`) and Pymatgen structure dictionaries throughout the pipeline, emitting `battgpt:hasCif` literals on `cryst:Crystal` nodes.
3. **Crystallographic Connectivity Graph Extraction**: Uses Pymatgen `CrystalNN` (primary) and `VoronoiNN` (fallback) to extract site-to-site bonding relationships (`battgpt:hasBondTo` and `battgpt:hasBondDistance`) as ready-to-use edges for downstream GNN graph construction.
4. **Genuine SMACT Package Integration**: Uses `smact.Element(symbol).pauling_eneg` and SMACT charge neutrality reasoning.
5. **Multi-Level Provenance Tracking**: Attaches `prov:wasGeneratedBy` and `dcterms:source` annotations to all material nodes, crystal structures, sites, bonds, and properties.
6. **Extended Semantic Validation Engine**: Audits missing lattice parameters, space groups, sites, species, provenance, site connectivity bonds, and processing flags (`pmg_success`, `smact_success`).
7. **Automated Regression Test Suite** (`tests/test_pipeline.py`): Full integration test suite covering pipeline execution, CrystalNN connectivity, SMACT reasoning, RDF triples, multi-format parsing, and validation.

---

## 4. Deterministic URI Scheme

To prevent node collisions and ensure reproducible RDF triple generation across pipelines:

| Entity Class | URI Template | Example URI |
| :--- | :--- | :--- |
| **Material** | `https://w3id.org/battgpt/kg/material/{material_id}` | `.../material/mp-19017` |
| **Crystal** | `https://w3id.org/battgpt/kg/crystal/{material_id}` | `.../crystal/mp-19017` |
| **UnitCell** | `https://w3id.org/battgpt/kg/unitcell/{material_id}` | `.../unitcell/mp-19017` |
| **SpaceGroup** | `https://w3id.org/battgpt/kg/spacegroup/{spacegroup_number}` | `.../spacegroup/166` |
| **CrystalSystem** | `https://w3id.org/battgpt/kg/crystalsystem/{system_name}` | `.../crystalsystem/trigonal` |
| **AtomicSite** | `https://w3id.org/battgpt/kg/site/{material_id}/{site_index}` | `.../site/mp-19017/0` |
| **AtomicSpecies** | `https://w3id.org/battgpt/kg/species/{symbol}_{oxidation_state}` | `.../species/Co_3` |
| **Element** | `https://w3id.org/battgpt/kg/element/{symbol}` | `.../element/Co` |
| **Property** | `https://w3id.org/battgpt/kg/property/{material_id}/{prop_name}` | `.../property/mp-19017/band_gap` |

---

## 5. Environment Setup & Execution

### Prerequisites
- Python 3.10+
- `uv` package manager

### Running Pipeline
```bash
uv run --directory battinfo/battinfo python ../../examples/run_pipeline.py
```

### Running Automated Test Suite
```bash
PYTHONPATH=../../ uv run --directory battinfo/battinfo python -m unittest discover -s ../../tests -p "test_*.py"
```

---

## 6. Output Artifacts

- **`output/`**: `battery_kg.ttl` (Turtle), `battery_kg.rdf` (RDF/XML), `battery_kg.jsonld` (JSON-LD).
- **`validation/`**: `validation_report.txt`, `validation_report.json`.
