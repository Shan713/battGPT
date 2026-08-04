"""
Automated Regression Test Suite for Battery Materials Knowledge Graph Pipeline (Stage 2.1).
"""
import unittest
from pathlib import Path
from rdflib import Graph, Namespace, RDF

from pipeline.config import PipelineConfig
from pipeline.ingest import MPIngester
from pipeline.processing import PymatgenProcessor, SMACTProcessor, BattINFOMapper
from pipeline.rdf import RDFBuilder, RDFValidator
from pipeline.export import RDFExporter

BATTGPT = Namespace("https://w3id.org/battgpt/kg#")
CHSUB = Namespace("https://w3id.org/emmo/domain/chemical-substance#")
CRYST = Namespace("https://w3id.org/emmo/domain/crystallography#")
PROV = Namespace("http://www.w3.org/ns/prov#")


class TestBatteryKGPipeline(unittest.TestCase):
    """Regression tests verifying pipeline execution, structural integrity, SMACT reasoning, RDF emission & validation."""

    @classmethod
    def setUpClass(cls):
        cls.config = PipelineConfig()
        cls.ingester = MPIngester(cls.config)
        cls.pmg_processor = PymatgenProcessor()
        cls.smact_processor = SMACTProcessor()
        cls.battinfo_mapper = BattINFOMapper()
        cls.rdf_builder = RDFBuilder()
        cls.validator = RDFValidator()
        cls.exporter = RDFExporter()

        # Ingest and process test dataset
        cls.records = cls.ingester.ingest_batch(cls.config.sample_materials)
        for rec in cls.records:
            cls.pmg_processor.process(rec)
            cls.smact_processor.process(rec)
            cls.battinfo_mapper.process(rec)

        cls.graph = cls.rdf_builder.build_graph(cls.records)

    def test_01_ingestion_completeness(self):
        """Test that all sample materials are ingested with authentic CIF and structure dict."""
        self.assertEqual(len(self.records), 12)
        for rec in self.records:
            self.assertIsNotNone(rec.cif, f"CIF missing for {rec.material_id}")
            self.assertIsNotNone(rec.structure_dict, f"structure_dict missing for {rec.material_id}")
            self.assertGreater(rec.lattice_a, 0, f"lattice_a non-positive for {rec.material_id}")
            self.assertGreater(len(rec.sites), 0, f"No sites for {rec.material_id}")

    def test_02_pymatgen_coordination_and_bonds(self):
        """Test Pymatgen CrystalNN / VoronoiNN coordination and connectivity graph extraction."""
        for rec in self.records:
            self.assertTrue(rec.processing_status["pmg_success"], f"Pymatgen failed for {rec.material_id}")
            self.assertIn(rec.crystal_system, ["Cubic", "Tetragonal", "Orthorhombic", "Hexagonal", "Trigonal", "Monoclinic", "Triclinic"])
            
            total_bonds = sum(len(site.neighbors) for site in rec.sites)
            self.assertGreater(total_bonds, 0, f"No connectivity graph bonds extracted for {rec.material_id}")
            for site in rec.sites:
                self.assertIsNotNone(site.coordination_number, f"Site coordination number missing for {rec.material_id}")

    def test_03_smact_chemical_reasoning(self):
        """Test SMACT Pauling electronegativity mapping and charge neutrality validation."""
        for rec in self.records:
            self.assertTrue(rec.processing_status["smact_success"], f"SMACT failed for {rec.material_id}")
            self.assertTrue(rec.smact_is_valid, f"SMACT flagged invalid composition for {rec.material_id}")
            self.assertGreater(len(rec.electronegativity_map), 0, f"No electronegativities for {rec.material_id}")

    def test_04_battinfo_curated_mapping(self):
        """Test BattINFO curated role assignment for active materials vs generic materials."""
        lco = next(r for r in self.records if r.formula == "LiCoO2")
        self.assertEqual(lco.battery_role, "PositiveElectrode")
        self.assertTrue(lco.is_active_material)

        lto = next(r for r in self.records if r.formula == "Li4Ti5O12")
        self.assertEqual(lto.battery_role, "NegativeElectrode")

        # Authentic MP formula for mp-696128 (ideal stoichiometry Li10GeP2S12)
        lgps = next(r for r in self.records if r.formula == "Li10Ge(PS6)2")
        self.assertEqual(lgps.battery_role, "Electrolyte")

    def test_05_rdf_triples_and_predicates(self):
        """Test RDF graph construction, CIF triples, provenance, and connectivity edges."""
        self.assertGreater(len(self.graph), 1000, "Graph contains fewer triples than expected")

        materials = list(self.graph.subjects(RDF.type, CHSUB.Substance))
        self.assertEqual(len(materials), 12)

        cifs = list(self.graph.triples((None, BATTGPT.hasCif, None)))
        self.assertGreaterEqual(len(cifs), 12, "Fewer CIF triples than crystal structures")

        bonds = list(self.graph.triples((None, BATTGPT.hasBondTo, None)))
        self.assertGreater(len(bonds), 0, "No hasBondTo connectivity triples in graph")

        prov_triples = list(self.graph.triples((None, PROV.wasGeneratedBy, None)))
        self.assertGreater(len(prov_triples), 50, "Fewer provenance statements than expected")

    def test_06_graph_validation(self):
        """Test that the RDF graph passes semantic validation with 0 errors."""
        report = self.validator.validate(self.graph, records=self.records)
        self.assertTrue(report.is_valid, f"Validation failed with errors: {report.errors}")
        self.assertEqual(len(report.errors), 0)

    def test_07_export_and_parsing(self):
        """Test export to Turtle, RDF/XML, JSON-LD and re-parsing."""
        exported = self.exporter.export_all(self.graph, self.config.output_dir)

        # Test Turtle parsing
        g_ttl = Graph()
        g_ttl.parse(source=str(exported["turtle"]), format="turtle")
        self.assertGreater(len(g_ttl), 1000)

        # Test RDF/XML parsing
        g_xml = Graph()
        g_xml.parse(source=str(exported["xml"]), format="xml")
        self.assertGreater(len(g_xml), 1000)

        # Test JSON-LD parsing
        g_jsonld = Graph()
        g_jsonld.parse(source=str(exported["jsonld"]), format="json-ld")
        self.assertGreater(len(g_jsonld), 1000)


if __name__ == "__main__":
    unittest.main()
