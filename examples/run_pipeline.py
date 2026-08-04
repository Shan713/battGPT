#!/usr/bin/env python3
"""
Stage 2.1 Pipeline Runner: Build & Validate Battery Materials Knowledge Graph.

Executes modular ingestion, structural processing, SMACT chemical reasoning,
BattINFO mapping, RDF graph building, extended validation, and multi-format export.
"""
import sys
import logging
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.config import PipelineConfig
from pipeline.ingest import MPIngester
from pipeline.processing import PymatgenProcessor, SMACTProcessor, BattINFOMapper
from pipeline.rdf import RDFBuilder, RDFValidator
from pipeline.export import RDFExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("run_pipeline")


def main():
    logger.info("Starting Battery Materials Knowledge Graph Pipeline (Stage 2.1 Refactor)...")
    config = PipelineConfig()

    # Step 1: Materials Project Ingestion
    logger.info("=== STEP 1: Materials Project Ingestion (Authentic Cache/API) ===")
    ingester = MPIngester(config)
    raw_records = ingester.ingest_batch(config.sample_materials)
    logger.info(f"Ingested {len(raw_records)} material records.")

    # Step 2: Pymatgen Processing
    logger.info("=== STEP 2: Pymatgen Structural Processing & CrystalNN Connectivity ===")
    pmg_processor = PymatgenProcessor()
    for rec in raw_records:
        try:
            pmg_processor.process(rec)
        except Exception as e:
            logger.error(f"Failed Pymatgen processing for {rec.material_id}: {e}")

    # Step 3: SMACT Chemical Processing
    logger.info("=== STEP 3: SMACT Chemical Processing ===")
    smact_processor = SMACTProcessor()
    for rec in raw_records:
        try:
            smact_processor.process(rec)
        except Exception as e:
            logger.error(f"Failed SMACT processing for {rec.material_id}: {e}")

    # Step 4: BattINFO Semantic Mapping
    logger.info("=== STEP 4: BattINFO Semantic Role Mapping ===")
    battinfo_mapper = BattINFOMapper()
    for rec in raw_records:
        try:
            battinfo_mapper.process(rec)
        except Exception as e:
            logger.error(f"Failed BattINFO mapping for {rec.material_id}: {e}")

    # Step 5: RDF Graph Construction
    logger.info("=== STEP 5: RDF Graph Construction ===")
    builder = RDFBuilder()
    graph = builder.build_graph(raw_records)

    # Step 6: Extended Graph Validation
    logger.info("=== STEP 6: Extended Graph Validation ===")
    validator = RDFValidator()
    report = validator.validate(graph, records=raw_records)
    report.save_reports(config.validation_dir)

    if not report.is_valid:
        logger.error("Graph validation FAILED! Check validation/validation_report.txt for details.")
    else:
        logger.info("Graph validation PASSED cleanly!")

    # Step 7: RDF Export
    logger.info("=== STEP 7: RDF Multi-Format Export ===")
    exporter = RDFExporter()
    exported_paths = exporter.export_all(graph, config.output_dir)

    # Pipeline Processing Diagnostics Summary
    successful = [r.material_id for r in raw_records if r.processing_status.get("pmg_success") and r.processing_status.get("smact_success")]
    failed = [r.material_id for r in raw_records if r.material_id not in successful]

    logger.info("======================================================================")
    logger.info("STAGE 2.1 PIPELINE EXECUTION SUMMARY")
    logger.info("======================================================================")
    logger.info(f"Total Materials Processed: {len(raw_records)}")
    logger.info(f"Successful Materials ({len(successful)}): {', '.join(successful)}")
    logger.info(f"Failed Materials ({len(failed)}): {', '.join(failed) if failed else 'None'}")
    logger.info(f"Total RDF Triples Generated: {len(graph)}")
    logger.info(f"Total Connectivity Bonds: {report.total_bonds}")
    logger.info(f"Exported Turtle (.ttl): {exported_paths['turtle']}")
    logger.info(f"Exported RDF/XML (.rdf): {exported_paths['xml']}")
    logger.info(f"Exported JSON-LD (.jsonld): {exported_paths['jsonld']}")
    logger.info("======================================================================")

if __name__ == "__main__":
    main()
