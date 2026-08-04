"""RDF Triple Emitter for MaterialRecord Entities with Provenance & Connectivity Graph."""
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, XSD
from ..models import MaterialRecord
from ..config import URIScheme

# Defined Namespaces according to Stage 1 Specification
EMMO = Namespace("https://w3id.org/emmo#")
CHSUB = Namespace("https://w3id.org/emmo/domain/chemical-substance#")
BATTERY = Namespace("https://w3id.org/emmo/domain/battery#")
CRYST = Namespace("https://w3id.org/emmo/domain/crystallography#")
BATTGPT = Namespace("https://w3id.org/battgpt/kg#")
QUDT = Namespace("http://qudt.org/schema/qudt/")
PROV = Namespace("http://www.w3.org/ns/prov#")
DCTERMS = Namespace("http://purl.org/dc/terms/")

# EMMO Semantic Term IRIs
EMMO_PROPERTY_CLASS = EMMO.EMMO_b7bcff25_ffc3_474e_9ab5_01b1664bd4ba  # owl:Class Property
EMMO_HAS_PROPERTY = EMMO.EMMO_e1097637_70d2_4895_973f_2396f04fa204    # owl:ObjectProperty hasProperty
EMMO_HAS_VALUE = EMMO.EMMO_faf79f53_749d_40b2_807c_d34244c192f4       # owl:DatatypeProperty hasNumberValue
EMMO_HAS_UNIT = EMMO.EMMO_bed1d005_b04e_4a90_94cf_02bc678a8569        # owl:ObjectProperty hasMeasurementUnit

class TripleGenerator:
    """Generates RDF triples for a single MaterialRecord using Stage 1 schema rules."""

    def generate_triples(self, record: MaterialRecord, graph: Graph):
        """Emit all RDF triples for a MaterialRecord into an rdflib Graph."""
        mat_uri = URIRef(URIScheme.material_uri(record.material_id))
        cryst_uri = URIRef(URIScheme.crystal_uri(record.material_id))
        uc_uri = URIRef(URIScheme.unitcell_uri(record.material_id))
        sg_uri = URIRef(URIScheme.spacegroup_uri(record.spacegroup_number))
        cs_uri = URIRef(URIScheme.crystalsystem_uri(record.crystal_system))

        mp_prov = record.provenance_map.get("material_id", "Materials Project API / Cache")

        # ── 1. Material Node ──
        graph.add((mat_uri, RDF.type, CHSUB.Substance))
        graph.add((mat_uri, RDFS.label, Literal(f"Material {record.formula} ({record.material_id})", lang="en")))
        graph.add((mat_uri, BATTGPT.hasFormula, Literal(record.formula, datatype=XSD.string)))
        graph.add((mat_uri, BATTGPT.hasMaterialProjectId, Literal(record.material_id, datatype=XSD.string)))
        graph.add((mat_uri, BATTGPT.isStable, Literal(record.is_stable, datatype=XSD.boolean)))
        graph.add((mat_uri, BATTGPT.hasStructure, cryst_uri))
        graph.add((mat_uri, DCTERMS.source, Literal(mp_prov, datatype=XSD.string)))

        # ── 2. Crystal Node ──
        graph.add((cryst_uri, RDF.type, CRYST.Crystal))
        graph.add((cryst_uri, RDFS.label, Literal(f"Crystal structure of {record.formula}", lang="en")))
        graph.add((cryst_uri, BATTGPT.hasMaterialProjectId, Literal(record.material_id, datatype=XSD.string)))
        graph.add((cryst_uri, BATTGPT.hasUnitCell, uc_uri))
        graph.add((cryst_uri, BATTGPT.hasSpaceGroup, sg_uri))
        graph.add((cryst_uri, BATTGPT.hasCrystalSystem, cs_uri))
        graph.add((cryst_uri, DCTERMS.source, Literal(mp_prov, datatype=XSD.string)))
        if record.cif:
            graph.add((cryst_uri, BATTGPT.hasCif, Literal(record.cif, datatype=XSD.string)))

        # ── 3. UnitCell Node ──
        graph.add((uc_uri, RDF.type, CRYST.UnitCell))
        graph.add((uc_uri, RDFS.label, Literal(f"Unit cell of {record.material_id}", lang="en")))
        graph.add((uc_uri, BATTGPT.hasLatticea, Literal(record.lattice_a, datatype=XSD.double)))
        graph.add((uc_uri, BATTGPT.hasLatticeb, Literal(record.lattice_b, datatype=XSD.double)))
        graph.add((uc_uri, BATTGPT.hasLatticec, Literal(record.lattice_c, datatype=XSD.double)))
        graph.add((uc_uri, BATTGPT.hasAlpha, Literal(record.alpha, datatype=XSD.double)))
        graph.add((uc_uri, BATTGPT.hasBeta, Literal(record.beta, datatype=XSD.double)))
        graph.add((uc_uri, BATTGPT.hasGamma, Literal(record.gamma, datatype=XSD.double)))
        graph.add((uc_uri, PROV.wasGeneratedBy, Literal(record.provenance_map.get("lattice", "Pymatgen"), datatype=XSD.string)))

        # ── 4. SpaceGroup Node ──
        graph.add((sg_uri, RDF.type, CRYST.SpaceGroup))
        graph.add((sg_uri, RDFS.label, Literal(f"Space Group {record.symmetry_symbol} ({record.spacegroup_number})", lang="en")))
        graph.add((sg_uri, BATTGPT.hasSymmetrySymbol, Literal(record.symmetry_symbol, datatype=XSD.string)))
        graph.add((sg_uri, BATTGPT.hasSpaceGroupNumber, Literal(record.spacegroup_number, datatype=XSD.integer)))
        graph.add((sg_uri, PROV.wasGeneratedBy, Literal(record.provenance_map.get("symmetry", "Pymatgen"), datatype=XSD.string)))

        # ── 5. CrystalSystem Node ──
        graph.add((cs_uri, RDF.type, CRYST.CrystalSystem))
        graph.add((cs_uri, RDFS.label, Literal(record.crystal_system, lang="en")))

        # ── 6. Atomic Sites, Species & Crystal Connectivity Graph Edges ──
        for site in record.sites:
            site_uri = URIRef(URIScheme.site_uri(record.material_id, site.index))
            sp_uri = URIRef(URIScheme.species_uri(site.element_symbol, site.oxidation_state))
            elem_uri = URIRef(URIScheme.element_uri(site.element_symbol))

            # Connect UnitCell -> Site
            graph.add((uc_uri, BATTGPT.containsSite, site_uri))

            # Site Node
            graph.add((site_uri, RDF.type, CRYST.AtomicSite))
            graph.add((site_uri, RDFS.label, Literal(f"Site {site.index} ({site.element_symbol}) in {record.material_id}", lang="en")))
            graph.add((site_uri, BATTGPT.hasFractionalX, Literal(site.fractional_x, datatype=XSD.double)))
            graph.add((site_uri, BATTGPT.hasFractionalY, Literal(site.fractional_y, datatype=XSD.double)))
            graph.add((site_uri, BATTGPT.hasFractionalZ, Literal(site.fractional_z, datatype=XSD.double)))
            graph.add((site_uri, PROV.wasGeneratedBy, Literal(site.provenance, datatype=XSD.string)))

            # Connect Site -> Species
            graph.add((site_uri, BATTGPT.containsSpecies, sp_uri))

            # Species Node
            graph.add((sp_uri, RDF.type, CHSUB.AtomicSpecies))
            graph.add((sp_uri, RDFS.label, Literal(site.species_symbol, lang="en")))
            if site.oxidation_state is not None:
                graph.add((sp_uri, BATTGPT.hasOxidationState, Literal(int(site.oxidation_state), datatype=XSD.integer)))
            graph.add((sp_uri, BATTGPT.hasElement, elem_uri))

            # Element Node
            graph.add((elem_uri, RDF.type, CHSUB.Element))
            graph.add((elem_uri, RDFS.label, Literal(site.element_symbol, lang="en")))
            en = record.electronegativity_map.get(site.element_symbol)
            if en is not None:
                graph.add((elem_uri, BATTGPT.hasElectronegativity, Literal(en, datatype=XSD.double)))
                graph.add((elem_uri, PROV.wasGeneratedBy, Literal(record.provenance_map.get("smact", "SMACT 4.0"), datatype=XSD.string)))

            # Coordination Geometry Property Node
            if site.coordination_geometry:
                geom_prop_uri = URIRef(URIScheme.property_uri(record.material_id, f"site_{site.index}_coordination"))
                graph.add((site_uri, BATTGPT.hasCoordinationGeometry, geom_prop_uri))
                graph.add((site_uri, EMMO_HAS_PROPERTY, geom_prop_uri))
                graph.add((geom_prop_uri, RDF.type, EMMO_PROPERTY_CLASS)) # emmo:Property
                graph.add((geom_prop_uri, RDFS.label, Literal(site.coordination_geometry, lang="en")))
                graph.add((geom_prop_uri, PROV.wasGeneratedBy, Literal(site.provenance, datatype=XSD.string)))

            # ── Explicit Crystal Connectivity Graph Edges (Bonds) ──
            for bond in site.neighbors:
                target_site_uri = URIRef(URIScheme.site_uri(record.material_id, bond.target_site_index))
                graph.add((site_uri, BATTGPT.hasBondTo, target_site_uri))
                graph.add((site_uri, BATTGPT.hasBondDistance, Literal(bond.distance_angstrom, datatype=XSD.double)))
                graph.add((site_uri, PROV.wasGeneratedBy, Literal(f"Pymatgen ({bond.coordination_method})", datatype=XSD.string)))

        # ── 7. Physical Properties ──
        for prop in record.get_properties():
            prop_uri = URIRef(URIScheme.property_uri(record.material_id, prop.name))
            unit_uri = URIRef(prop.unit_iri)

            # Canonical Attachment via emmo:hasProperty
            graph.add((mat_uri, EMMO_HAS_PROPERTY, prop_uri))

            # Specific property predicate attachment
            if prop.name in ("band_gap", "formation_energy_per_atom", "energy_above_hull"):
                pred = getattr(BATTGPT, f"has{'BandGap' if prop.name == 'band_gap' else ('FormationEnergy' if prop.name == 'formation_energy_per_atom' else 'EnergyAboveHull')}")
                graph.add((cryst_uri, pred, prop_uri))
                graph.add((mat_uri, pred, prop_uri))

            # Property Entity (typed as emmo:Property)
            graph.add((prop_uri, RDF.type, EMMO_PROPERTY_CLASS))
            graph.add((prop_uri, RDFS.label, Literal(f"{prop.name} of {record.material_id}", lang="en")))
            graph.add((prop_uri, EMMO_HAS_VALUE, Literal(prop.value, datatype=XSD.double)))
            graph.add((prop_uri, EMMO_HAS_UNIT, unit_uri))
            graph.add((prop_uri, PROV.wasGeneratedBy, Literal(prop.provenance, datatype=XSD.string)))

            # Link unit to type without mutating shared vocabulary symbol literals
            graph.add((unit_uri, RDF.type, EMMO_HAS_UNIT))

        # ── 8. Curated BattINFO Battery Role Annotation ──
        if record.battery_role_iri:
            role_type_uri = URIRef(record.battery_role_iri)
            graph.add((mat_uri, BATTGPT.belongsToElectrode, role_type_uri))
            graph.add((role_type_uri, BATTGPT.usesMaterial, mat_uri))
            graph.add((mat_uri, PROV.wasGeneratedBy, Literal(record.provenance_map.get("battinfo", "BattINFO Curated Role Mapping"), datatype=XSD.string)))
            if record.battery_role_evidence:
                graph.add((mat_uri, RDFS.comment, Literal(f"BattINFO Role Evidence: {record.battery_role_evidence}", lang="en")))
