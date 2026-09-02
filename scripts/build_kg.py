"""Builds the battery materials Knowledge Graph against the BattGpt-Ontology extension.

Ingests curated Materials Project records from the offline cache
(pipeline/data/cached_mp_materials.json), runs the Pymatgen / SMACT / BattINFO / StructureFamily /
Electrochemistry enrichment stages, constructs an RDF graph bound to
BattGpt-Ontology/battgpt.ttl, validates it, and exports Turtle/RDF-XML/JSON-LD.

Usage:
    python scripts/build_kg.py            # build with all curated materials -> output/battgpt_kg/
    python scripts/build_kg.py 10          # build with the first N curated materials
    python scripts/build_kg.py cathodes    # build the 10-cathode test set -> output/battgpt_kg_cathodes/
"""
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import PipelineConfig
from pipeline.ingest import MPIngester
from pipeline.processing import (
    PymatgenProcessor, SMACTProcessor, BattINFOMapper, StructureFamilyMapper, ElectrochemistryProcessor,
)
from pipeline.rdf import RDFBuilder, RDFValidator
from pipeline.export import RDFExporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    config = PipelineConfig()
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    if arg == "cathodes":
        material_ids = config.cathode_test_materials
        output_dir = PROJECT_ROOT / "output" / "battgpt_kg_cathodes"
    else:
        num_materials = int(arg) if arg else len(config.sample_materials)
        material_ids = config.sample_materials[:num_materials]
        output_dir = PROJECT_ROOT / "output" / "battgpt_kg"

    logger.info(f"Selected {len(material_ids)} materials: {material_ids}")

    logger.info("Step 1: Ingesting materials from authentic offline MP cache...")
    ingester = MPIngester(config)
    records = ingester.ingest_batch(material_ids)
    logger.info(f"Step 1 Complete: Ingested {len(records)} records.")

    logger.info("Step 2: Running Pymatgen / SMACT / BattINFO / StructureFamily / Electrochemistry enrichment...")
    pmg = PymatgenProcessor()
    smact = SMACTProcessor()
    mapper = BattINFOMapper()
    structure_family = StructureFamilyMapper()
    electrochemistry = ElectrochemistryProcessor()
    for rec in records:
        pmg.process(rec)
        smact.process(rec)
        mapper.process(rec)
        structure_family.process(rec)
        electrochemistry.process(rec)
    logger.info("Step 2 Complete.")

    logger.info("Step 3: Constructing RDF Knowledge Graph against BattGpt-Ontology/battgpt.ttl...")
    builder = RDFBuilder()
    graph = builder.build_graph(records)
    logger.info(f"Step 3 Complete: Built RDF Graph with {len(graph):,} triples.")

    logger.info("Step 4: Validating RDF Knowledge Graph...")
    validator = RDFValidator()
    report = validator.validate(graph, records=records)
    logger.info(f"Validation: is_valid={report.is_valid}, errors={len(report.errors)}, warnings={len(report.warnings)}")
    for e in report.errors:
        logger.error(f"  VALIDATION ERROR: {e}")
    report.save_reports(output_dir)

    logger.info(f"Step 5: Exporting RDF Graph (Turtle, RDF/XML, JSON-LD) to {output_dir}...")
    exporter = RDFExporter()
    exported = exporter.export_all(graph, output_dir=output_dir)
    for fmt, path in exported.items():
        logger.info(f"  {fmt}: {path} ({path.stat().st_size:,} bytes)")

    logger.info("Done. Materials in this KG:")
    for rec in records:
        cell = f", OCV={rec.average_voltage:.2f}V, Q={rec.capacity_grav:.1f}mAh/g" if rec.average_voltage is not None else ""
        logger.info(f"  {rec.material_id}: {rec.formula} -- role={rec.battery_role}, family={rec.structure_family}{cell}")


if __name__ == "__main__":
    main()
