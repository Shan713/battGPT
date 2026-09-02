"""Extended Graph Validation Engine for RDF Syntax, Namespace Consistency, and Semantic Integrity."""
from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
from rdflib import Graph, URIRef, RDF, OWL, Namespace
from ..models import MaterialRecord

logger = logging.getLogger(__name__)

BATTGPT = Namespace("https://w3id.org/battgpt/kg#")
PROV = Namespace("http://www.w3.org/ns/prov#")

# EMMO Semantic Term IRIs
EMMO_PROPERTY_CLASS = URIRef("https://w3id.org/emmo#EMMO_b7bcff25_ffc3_474e_9ab5_01b1664bd4ba")
EMMO_HAS_PROPERTY = URIRef("https://w3id.org/emmo#EMMO_e1097637_70d2_4895_973f_2396f04fa204")
EMMO_CHEMICAL_SUBSTANCE = URIRef("https://w3id.org/emmo#EMMO_df96cbb6_b5ee_4222_8eab_b3675df24bea")

@dataclass
class ValidationReport:
    """Structured report summarizing graph validation metrics, warnings, and errors."""
    total_triples: int = 0
    total_materials: int = 0
    total_crystals: int = 0
    total_sites: int = 0
    total_bonds: int = 0
    total_properties: int = 0
    failed_pmg_materials: list[str] = field(default_factory=list)
    failed_smact_materials: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    is_valid: bool = True

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "total_triples": self.total_triples,
            "total_materials": self.total_materials,
            "total_crystals": self.total_crystals,
            "total_sites": self.total_sites,
            "total_bonds": self.total_bonds,
            "total_properties": self.total_properties,
            "failed_pmg_materials": self.failed_pmg_materials,
            "failed_smact_materials": self.failed_smact_materials,
            "errors": self.errors,
            "warnings": self.warnings
        }

    def save_reports(self, output_dir: Path):
        """Write validation report as human-readable text and JSON."""
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "validation_report.json"
        txt_path = output_dir / "validation_report.txt"

        json_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

        summary = f"""======================================================================
BATTERY MATERIALS KNOWLEDGE GRAPH VALIDATION REPORT (Stage 2.2)
======================================================================
Status: {'PASSED (VALID)' if self.is_valid else 'FAILED (ERRORS DETECTED)'}
Total Triples: {self.total_triples}
Total Material Entities: {self.total_materials}
Total Crystal Structures: {self.total_crystals}
Total Atomic Sites: {self.total_sites}
Total Connectivity Bonds: {self.total_bonds}
Total Property Nodes: {self.total_properties}

Failed Pymatgen Materials: {len(self.failed_pmg_materials)}
Failed SMACT Materials: {len(self.failed_smact_materials)}

ERRORS ({len(self.errors)}):
""" + ("  - None\n" if not self.errors else "\n".join(f"  - {e}" for e in self.errors) + "\n") + f"""
WARNINGS ({len(self.warnings)}):
""" + ("  - None\n" if not self.warnings else "\n".join(f"  - {w}" for w in self.warnings) + "\n") + """======================================================================
"""
        txt_path.write_text(summary, encoding="utf-8")
        logger.info(f"Validation reports written to {json_path} and {txt_path}")


class RDFValidator:
    """Validator performing extended semantic verification on constructed RDF knowledge graph."""

    def validate(self, graph: Graph, records: list[MaterialRecord] | None = None) -> ValidationReport:
        """Perform comprehensive graph integrity & semantic verification."""
        report = ValidationReport()
        report.total_triples = len(graph)

        # 1. Count Entity Types
        materials = list(graph.subjects(RDF.type, EMMO_CHEMICAL_SUBSTANCE))
        crystals = list(graph.subjects(RDF.type, BATTGPT.CrystalStructure))
        sites = list(graph.subjects(RDF.type, BATTGPT.Site))
        unitcells = list(graph.subjects(RDF.type, BATTGPT.UnitCell))

        report.total_materials = len(materials)
        report.total_crystals = len(crystals)
        report.total_sites = len(sites)

        bonds = list(graph.triples((None, BATTGPT.hasBondTo, None)))
        report.total_bonds = len(bonds)

        properties = list(graph.subjects(RDF.type, EMMO_PROPERTY_CLASS))
        report.total_properties = len(properties)

        # 2. Semantic Integrity: Verify no ObjectProperty is used as rdf:type
        bad_type_triples = list(graph.triples((None, RDF.type, EMMO_HAS_PROPERTY)))
        if bad_type_triples:
            report.errors.append(
                f"Found {len(bad_type_triples)} triples using ObjectProperty emmo:hasProperty "
                f"({EMMO_HAS_PROPERTY}) as rdf:type. Individuals must be typed using owl:Class."
            )

        # 3. Semantic Integrity: Verify ontology header & imports
        ontologies = list(graph.subjects(RDF.type, OWL.Ontology))
        if not ontologies:
            report.warnings.append("Graph does not contain an owl:Ontology subject node.")

        # 4. Semantic Integrity: Check that all custom battgpt predicates are declared as Object/DatatypeProperty
        used_battgpt_preds = set(p for p in graph.predicates() if str(p).startswith(str(BATTGPT)))
        for p in used_battgpt_preds:
            types = set(graph.objects(p, RDF.type))
            if not types.intersection({OWL.ObjectProperty, OWL.DatatypeProperty}):
                report.errors.append(
                    f"Predicate {p} used in graph is not declared as owl:ObjectProperty or owl:DatatypeProperty."
                )

        # 5. Check Record Processing Diagnostics if provided
        if records:
            for r in records:
                if not r.processing_status.get("pmg_success", False):
                    report.failed_pmg_materials.append(r.material_id)
                    report.warnings.append(f"Material {r.material_id} flagged pmg_success=False")
                if not r.processing_status.get("smact_success", False):
                    report.failed_smact_materials.append(r.material_id)
                    report.warnings.append(f"Material {r.material_id} flagged smact_success=False")

        # 6. Check Mandatory Material & Structural Properties
        for mat in materials:
            formulas = list(graph.objects(mat, BATTGPT.hasFormula))
            if not formulas:
                report.errors.append(f"Material node {mat} is missing mandatory battgpt:hasFormula property.")

            structs = list(graph.objects(mat, BATTGPT.hasStructure))
            if not structs:
                report.errors.append(f"Material node {mat} is missing mandatory battgpt:hasStructure edge.")

        # 7. Check Mandatory Crystal & Lattice Parameters
        for cryst in crystals:
            cifs = list(graph.objects(cryst, BATTGPT.hasCif))
            if not cifs:
                report.warnings.append(f"Crystal node {cryst} is missing battgpt:hasCif string.")

            ucs = list(graph.objects(cryst, BATTGPT.hasUnitCell))
            if not ucs:
                report.errors.append(f"Crystal node {cryst} is missing mandatory battgpt:hasUnitCell edge.")

            sgs = list(graph.objects(cryst, BATTGPT.hasSpaceGroup))
            if not sgs:
                report.errors.append(f"Crystal node {cryst} is missing mandatory battgpt:hasSpaceGroup edge.")

        # 8. Check UnitCell Lattice Values
        for uc in unitcells:
            lat_a = list(graph.objects(uc, BATTGPT.hasLatticeA))
            if not lat_a or float(lat_a[0]) <= 0:
                report.errors.append(f"UnitCell {uc} has missing or non-positive lattice parameter a.")

        # 9. Check Provenance Attributes
        prov_triples = list(graph.triples((None, PROV.wasGeneratedBy, None)))
        if len(prov_triples) == 0:
            report.errors.append("Graph contains zero prov:wasGeneratedBy provenance statements.")

        # 10. Check Syntax / Serialization Re-parsing (Sample-based for large graphs)
        try:
            sample_g = Graph()
            count = 0
            for t in graph:
                sample_g.add(t)
                count += 1
                if count >= 2000:
                    break
            temp_g = Graph()
            temp_g.parse(data=sample_g.serialize(format="turtle"), format="turtle")
        except Exception as e:
            report.errors.append(f"Graph failed re-parsing serialization check: {e}")

        # Assess Validity
        if report.errors:
            report.is_valid = False

        return report
