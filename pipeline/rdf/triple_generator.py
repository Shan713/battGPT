"""RDF Triple Emitter for MaterialRecord Entities with Reified Bonds, Periodic Descriptors & Battery Role Individuals."""
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS, XSD, OWL
from ..models import MaterialRecord
from ..models.element_data import get_element_physical_data
from ..config import URIScheme

# Defined Namespaces according to Stage 1, 2, 2.3.1 & 2.3.2 Specifications
EMMO = Namespace("https://w3id.org/emmo#")
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
EMMO_CHEMICAL_SUBSTANCE = EMMO.EMMO_df96cbb6_b5ee_4222_8eab_b3675df24bea  # owl:Class ChemicalSubstance (battgpt: material domain/range)
EMMO_CHEMICAL_ELEMENT = EMMO.EMMO_4f40def1_3cd7_4067_9596_541e9a5134cf   # owl:Class ChemicalElement (battgpt: element domain/range)

ROLE_INDIVIDUAL_MAP = {
    "PositiveElectrode": BATTGPT.PositiveElectrodeRoleIndividual,
    "NegativeElectrode": BATTGPT.NegativeElectrodeRoleIndividual,
    "Electrolyte": BATTGPT.ElectrolyteRoleIndividual,
    "Separator": BATTGPT.SeparatorRoleIndividual,
}

# belongsToElectrode's range was tightened in v0.3.0 to owl:unionOf(PositiveElectrodeRole,
# NegativeElectrodeRole); Electrolyte/SeparatorRole materials are still linked via usesMaterial
# (its inverse, left general over all four BatteryRole subclasses) but must not use belongsToElectrode.
BELONGS_TO_ELECTRODE_ROLES = {"PositiveElectrode", "NegativeElectrode"}

STRUCTURE_FAMILY_INDIVIDUAL_MAP = {
    "LayeredOxideStructure": BATTGPT.LayeredOxideStructureIndividual,
    "SpinelStructure": BATTGPT.SpinelStructureIndividual,
    "RockSaltStructure": BATTGPT.RockSaltStructureIndividual,
    "OlivineStructure": BATTGPT.OlivineStructureIndividual,
    "NASICONStructure": BATTGPT.NASICONStructureIndividual,
    "GarnetStructure": BATTGPT.GarnetStructureIndividual,
    "PerovskiteStructure": BATTGPT.PerovskiteStructureIndividual,
    "LGPSTypeStructure": BATTGPT.LGPSTypeStructureIndividual,
    "ArgyroditeStructure": BATTGPT.ArgyroditeStructureIndividual,
}

# Mirrors STRUCTURE_FAMILY_INDIVIDUAL_MAP: coordination geometry is a small closed
# vocabulary (see GEOMETRY_LOOKUP in pymatgen_processor.py), so every site sharing a
# geometry points at one canonical NamedIndividual instead of minting a disposable
# per-site node.
COORDINATION_GEOMETRY_INDIVIDUAL_MAP = {
    "Linear": BATTGPT.LinearGeometryIndividual,
    "Trigonal Planar": BATTGPT.TrigonalPlanarGeometryIndividual,
    "Tetrahedral": BATTGPT.TetrahedralGeometryIndividual,
    "Square Pyramidal": BATTGPT.SquarePyramidalGeometryIndividual,
    "Octahedral": BATTGPT.OctahedralGeometryIndividual,
    "Pentagonal Bipyramidal": BATTGPT.PentagonalBipyramidalGeometryIndividual,
    "Square Antiprismatic": BATTGPT.SquareAntiprismaticGeometryIndividual,
    "Cuboctahedral": BATTGPT.CuboctahedralGeometryIndividual,
}

# battery:BatteryCell, reused (not redefined) from EMMO domain-battery.
BATTERY_CELL_CLASS = BATTERY.battery_68ed592a_7924_45d0_a108_94d6275d57f0


class TripleGenerator:
    """Generates RDF triples for a MaterialRecord entity using Stage 2.3.2 schema rules."""

    def generate_triples(self, record: MaterialRecord, graph: Graph):
        """Emit all RDF triples for a MaterialRecord into an rdflib Graph."""
        mat_uri = URIRef(URIScheme.material_uri(record.material_id))
        cryst_uri = URIRef(URIScheme.crystal_uri(record.material_id))
        uc_uri = URIRef(URIScheme.unitcell_uri(record.material_id))
        sg_uri = URIRef(URIScheme.spacegroup_uri(record.spacegroup_number))
        cs_uri = URIRef(URIScheme.crystalsystem_uri(record.crystal_system))

        mp_prov = record.provenance_map.get("material_id", "Materials Project API / Cache")

        # ── 1. Material Node ──
        graph.add((mat_uri, RDF.type, EMMO_CHEMICAL_SUBSTANCE))
        graph.add((mat_uri, RDFS.label, Literal(f"Material {record.formula} ({record.material_id})", lang="en")))
        graph.add((mat_uri, BATTGPT.hasFormula, Literal(record.formula, datatype=XSD.string)))
        graph.add((mat_uri, BATTGPT.hasMaterialProjectId, Literal(record.material_id, datatype=XSD.string)))
        graph.add((mat_uri, BATTGPT.isStable, Literal(record.is_stable, datatype=XSD.boolean)))
        if record.is_metal is not None:
            graph.add((mat_uri, BATTGPT.isMetal, Literal(record.is_metal, datatype=XSD.boolean)))
        if record.is_gap_direct is not None:
            graph.add((mat_uri, BATTGPT.isGapDirect, Literal(record.is_gap_direct, datatype=XSD.boolean)))
        if record.chemsys:
            graph.add((mat_uri, BATTGPT.hasChemsys, Literal(record.chemsys, datatype=XSD.string)))
        if record.is_theoretical is not None:
            graph.add((mat_uri, BATTGPT.isTheoretical, Literal(record.is_theoretical, datatype=XSD.boolean)))

        graph.add((mat_uri, BATTGPT.hasStructure, cryst_uri))
        graph.add((mat_uri, DCTERMS.source, Literal(mp_prov, datatype=XSD.string)))

        # ── 2. Crystal Node ──
        graph.add((cryst_uri, RDF.type, BATTGPT.CrystalStructure))
        graph.add((cryst_uri, RDFS.label, Literal(f"Crystal structure of {record.formula}", lang="en")))
        graph.add((cryst_uri, BATTGPT.hasMaterialProjectId, Literal(record.material_id, datatype=XSD.string)))
        graph.add((cryst_uri, BATTGPT.hasUnitCell, uc_uri))
        graph.add((cryst_uri, BATTGPT.hasSpaceGroup, sg_uri))
        graph.add((cryst_uri, BATTGPT.hasCrystalSystem, cs_uri))
        graph.add((cryst_uri, DCTERMS.source, Literal(mp_prov, datatype=XSD.string)))
        if record.point_group:
            graph.add((cryst_uri, BATTGPT.hasPointGroup, Literal(record.point_group, datatype=XSD.string)))
        if record.cif:
            graph.add((cryst_uri, BATTGPT.hasCif, Literal(record.cif, datatype=XSD.string)))
        if record.structure_family and record.structure_family in STRUCTURE_FAMILY_INDIVIDUAL_MAP:
            family_ind_uri = STRUCTURE_FAMILY_INDIVIDUAL_MAP[record.structure_family]
            graph.add((cryst_uri, BATTGPT.hasStructureFamily, family_ind_uri))
            if record.structure_family_evidence:
                graph.add((cryst_uri, RDFS.comment, Literal(f"StructureFamily Evidence: {record.structure_family_evidence}", lang="en")))

        # ── 3. UnitCell Node ──
        graph.add((uc_uri, RDF.type, BATTGPT.UnitCell))
        graph.add((uc_uri, RDFS.label, Literal(f"Unit cell of {record.material_id}", lang="en")))
        graph.add((uc_uri, BATTGPT.hasLatticeA, Literal(record.lattice_a, datatype=XSD.double)))
        graph.add((uc_uri, BATTGPT.hasLatticeB, Literal(record.lattice_b, datatype=XSD.double)))
        graph.add((uc_uri, BATTGPT.hasLatticeC, Literal(record.lattice_c, datatype=XSD.double)))
        graph.add((uc_uri, BATTGPT.hasAlpha, Literal(record.alpha, datatype=XSD.double)))
        graph.add((uc_uri, BATTGPT.hasBeta, Literal(record.beta, datatype=XSD.double)))
        graph.add((uc_uri, BATTGPT.hasGamma, Literal(record.gamma, datatype=XSD.double)))
        graph.add((uc_uri, PROV.wasGeneratedBy, Literal(record.provenance_map.get("lattice", "Pymatgen"), datatype=XSD.string)))

        # ── 4. SpaceGroup Node ──
        graph.add((sg_uri, RDF.type, BATTGPT.SpaceGroup))
        graph.add((sg_uri, RDFS.label, Literal(f"Space Group {record.symmetry_symbol} ({record.spacegroup_number})", lang="en")))
        graph.add((sg_uri, BATTGPT.hasSymmetrySymbol, Literal(record.symmetry_symbol, datatype=XSD.string)))
        graph.add((sg_uri, BATTGPT.hasSpaceGroupNumber, Literal(record.spacegroup_number, datatype=XSD.integer)))
        graph.add((sg_uri, PROV.wasGeneratedBy, Literal(record.provenance_map.get("symmetry", "Pymatgen"), datatype=XSD.string)))

        # ── 5. CrystalSystem Node ──
        graph.add((cs_uri, RDF.type, BATTGPT.CrystalSystem))
        graph.add((cs_uri, RDFS.label, Literal(record.crystal_system, lang="en")))

        # ── 6. Atomic Sites, Species, Elements & Reified Crystal Bonds ──
        for site in record.sites:
            site_uri = URIRef(URIScheme.site_uri(record.material_id, site.index))
            sp_uri = URIRef(URIScheme.species_uri(site.element_symbol, site.oxidation_state))
            elem_uri = URIRef(URIScheme.element_uri(site.element_symbol))

            # Connect UnitCell -> Site
            graph.add((uc_uri, BATTGPT.hasSite, site_uri))

            # Site Node
            graph.add((site_uri, RDF.type, BATTGPT.Site))
            graph.add((site_uri, RDFS.label, Literal(f"Site {site.index} ({site.element_symbol}) in {record.material_id}", lang="en")))
            graph.add((site_uri, BATTGPT.hasFractionalX, Literal(site.fractional_x, datatype=XSD.double)))
            graph.add((site_uri, BATTGPT.hasFractionalY, Literal(site.fractional_y, datatype=XSD.double)))
            graph.add((site_uri, BATTGPT.hasFractionalZ, Literal(site.fractional_z, datatype=XSD.double)))
            graph.add((site_uri, PROV.wasGeneratedBy, Literal(site.provenance, datatype=XSD.string)))

            # Connect Site -> Species
            graph.add((site_uri, BATTGPT.hasSpecies, sp_uri))

            # Species Node
            graph.add((sp_uri, RDF.type, BATTGPT.Species))
            graph.add((sp_uri, RDFS.label, Literal(site.species_symbol, lang="en")))
            if site.oxidation_state is not None:
                graph.add((sp_uri, BATTGPT.hasOxidationState, Literal(int(site.oxidation_state), datatype=XSD.integer)))
            graph.add((sp_uri, BATTGPT.hasElement, elem_uri))

            # Element Node (Augmented with Periodic Table Descriptors)
            graph.add((elem_uri, RDF.type, EMMO_CHEMICAL_ELEMENT))
            graph.add((elem_uri, RDFS.label, Literal(site.element_symbol, lang="en")))
            
            el_data = get_element_physical_data(site.element_symbol)
            graph.add((elem_uri, BATTGPT.hasAtomicMass, Literal(el_data.atomic_mass, datatype=XSD.double)))
            graph.add((elem_uri, BATTGPT.hasGroup, Literal(el_data.group, datatype=XSD.integer)))
            graph.add((elem_uri, BATTGPT.hasPeriod, Literal(el_data.period, datatype=XSD.integer)))
            graph.add((elem_uri, BATTGPT.hasElectronegativity, Literal(el_data.electronegativity, datatype=XSD.double)))
            graph.add((elem_uri, BATTGPT.hasCovalentRadius, Literal(el_data.covalent_radius, datatype=XSD.double)))
            graph.add((elem_uri, BATTGPT.hasValenceElectrons, Literal(el_data.valence_electrons, datatype=XSD.integer)))

            # Coordination Geometry: link to the shared canonical individual for this
            # geometry (see COORDINATION_GEOMETRY_INDIVIDUAL_MAP) rather than minting a
            # new node per site.
            if site.coordination_geometry in COORDINATION_GEOMETRY_INDIVIDUAL_MAP:
                geom_ind_uri = COORDINATION_GEOMETRY_INDIVIDUAL_MAP[site.coordination_geometry]
                graph.add((site_uri, BATTGPT.hasCoordinationGeometry, geom_ind_uri))

            # ── 6b. Reified Crystal Bond Entities & Direct Predicates ──
            for bond in site.neighbors:
                target_site_uri = URIRef(URIScheme.site_uri(record.material_id, bond.target_site_index))
                bond_uri = URIRef(URIScheme.bond_uri(record.material_id, site.index, bond.target_site_index))

                # Reified CrystalBond Entity
                graph.add((site_uri, BATTGPT.hasBond, bond_uri))
                graph.add((bond_uri, RDF.type, BATTGPT.CrystalBond))
                graph.add((bond_uri, RDFS.label, Literal(f"Bond from site {site.index} to site {bond.target_site_index} in {record.material_id}", lang="en")))
                graph.add((bond_uri, BATTGPT.hasSourceSite, site_uri))
                graph.add((bond_uri, BATTGPT.hasTargetSite, target_site_uri))
                graph.add((bond_uri, BATTGPT.hasBondDistance, Literal(bond.distance_angstrom, datatype=XSD.double)))
                graph.add((bond_uri, BATTGPT.hasCoordinationMethod, Literal(bond.coordination_method, datatype=XSD.string)))
                graph.add((bond_uri, PROV.wasGeneratedBy, Literal(f"Pymatgen ({bond.coordination_method})", datatype=XSD.string)))

                # Direct predicate attachment
                graph.add((site_uri, BATTGPT.hasBondTo, target_site_uri))
                graph.add((site_uri, BATTGPT.hasBondDistance, Literal(bond.distance_angstrom, datatype=XSD.double)))

        # ── 7. Physical & Elastic Properties ──
        for prop in record.get_properties():
            prop_uri = URIRef(URIScheme.property_uri(record.material_id, prop.name))
            unit_uri = URIRef(prop.unit_iri)

            # Canonical Attachment via emmo:hasProperty
            graph.add((mat_uri, EMMO_HAS_PROPERTY, prop_uri))

            # Specific property predicate attachment
            if prop.name == "band_gap":
                graph.add((mat_uri, BATTGPT.hasBandGap, prop_uri))
                graph.add((cryst_uri, BATTGPT.hasBandGap, prop_uri))
            elif prop.name == "formation_energy_per_atom":
                graph.add((mat_uri, BATTGPT.hasFormationEnergy, prop_uri))
                graph.add((cryst_uri, BATTGPT.hasFormationEnergy, prop_uri))
            elif prop.name == "energy_above_hull":
                graph.add((mat_uri, BATTGPT.hasEnergyAboveHull, prop_uri))
                graph.add((cryst_uri, BATTGPT.hasEnergyAboveHull, prop_uri))
            elif prop.name == "bulk_modulus":
                graph.add((mat_uri, BATTGPT.hasBulkModulus, prop_uri))
                graph.add((cryst_uri, BATTGPT.hasBulkModulus, prop_uri))
            elif prop.name == "shear_modulus":
                graph.add((mat_uri, BATTGPT.hasShearModulus, prop_uri))
                graph.add((cryst_uri, BATTGPT.hasShearModulus, prop_uri))

            # Property Entity (typed as emmo:Property)
            graph.add((prop_uri, RDF.type, EMMO_PROPERTY_CLASS))
            graph.add((prop_uri, RDFS.label, Literal(f"{prop.name} of {record.material_id}", lang="en")))
            graph.add((prop_uri, EMMO_HAS_VALUE, Literal(prop.value, datatype=XSD.double)))
            graph.add((prop_uri, EMMO_HAS_UNIT, unit_uri))
            graph.add((prop_uri, PROV.wasGeneratedBy, Literal(prop.provenance, datatype=XSD.string)))
            graph.add((unit_uri, RDF.type, EMMO_HAS_UNIT))

        # ── 8. Explicit Battery Role owl:NamedIndividual Annotation (Stage 2.3.2) ──
        if record.battery_role and record.battery_role in ROLE_INDIVIDUAL_MAP:
            role_ind_uri = ROLE_INDIVIDUAL_MAP[record.battery_role]
            # belongsToElectrode's range is restricted (v0.3.0) to Positive/NegativeElectrodeRole only;
            # usesMaterial (its inverse) stays general over all four BatteryRole subclasses.
            if record.battery_role in BELONGS_TO_ELECTRODE_ROLES:
                graph.add((mat_uri, BATTGPT.belongsToElectrode, role_ind_uri))
            graph.add((role_ind_uri, BATTGPT.usesMaterial, mat_uri))
            graph.add((mat_uri, PROV.wasGeneratedBy, Literal(record.provenance_map.get("battinfo", "BattINFO Role Mapping"), datatype=XSD.string)))
            if record.battery_role_evidence:
                graph.add((mat_uri, RDFS.comment, Literal(f"BattINFO Role Evidence: {record.battery_role_evidence}", lang="en")))

        # ── 9. Battery-Cell-Level Electrochemistry (v0.3.0), from real MP insertion-electrode data ──
        if record.average_voltage is not None and record.capacity_grav is not None:
            cell_uri = URIRef(URIScheme.batterycell_uri(record.material_id))
            graph.add((cell_uri, RDF.type, BATTERY_CELL_CLASS))
            graph.add((cell_uri, RDFS.label, Literal(
                f"Battery cell using {record.formula} as {record.battery_role or 'electrode'} active material "
                f"({record.working_ion}-ion)", lang="en")))
            graph.add((cell_uri, DCTERMS.relation, mat_uri))
            graph.add((mat_uri, DCTERMS.relation, cell_uri))

            ocv_uri = URIRef(URIScheme.property_uri(record.material_id, "open_circuit_voltage"))
            graph.add((cell_uri, EMMO_HAS_PROPERTY, ocv_uri))
            graph.add((cell_uri, BATTGPT.hasOpenCircuitVoltage, ocv_uri))
            graph.add((ocv_uri, RDF.type, EMMO_PROPERTY_CLASS))
            graph.add((ocv_uri, RDFS.label, Literal(f"Open-circuit voltage of {record.material_id} cell", lang="en")))
            graph.add((ocv_uri, EMMO_HAS_VALUE, Literal(record.average_voltage, datatype=XSD.double)))
            graph.add((ocv_uri, EMMO_HAS_UNIT, URIRef("http://qudt.org/vocab/unit/V")))
            graph.add((ocv_uri, PROV.wasGeneratedBy, Literal(record.electrode_evidence or "Materials Project insertion-electrode data", datatype=XSD.string)))

            cap_uri = URIRef(URIScheme.property_uri(record.material_id, "specific_capacity"))
            graph.add((cell_uri, EMMO_HAS_PROPERTY, cap_uri))
            graph.add((cell_uri, BATTGPT.hasSpecificCapacity, cap_uri))
            graph.add((cap_uri, RDF.type, EMMO_PROPERTY_CLASS))
            graph.add((cap_uri, RDFS.label, Literal(f"Gravimetric specific capacity of {record.material_id} cell", lang="en")))
            graph.add((cap_uri, EMMO_HAS_VALUE, Literal(record.capacity_grav, datatype=XSD.double)))
            graph.add((cap_uri, EMMO_HAS_UNIT, URIRef("http://qudt.org/vocab/unit/MilliA-HR-PER-GM")))
            graph.add((cap_uri, PROV.wasGeneratedBy, Literal(record.electrode_evidence or "Materials Project insertion-electrode data", datatype=XSD.string)))
