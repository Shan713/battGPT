"""Unified MaterialRecord Data Model for Progressive Enrichment & Crystal Connectivity."""
from dataclasses import dataclass, field
from typing import Any

@dataclass
class PropertyData:
    """Quantitative scalar property container with explicit provenance."""
    name: str
    value: float
    unit_iri: str
    unit_symbol: str
    provenance: str = "Materials Project API / Cache"
    description: str = ""

@dataclass
class BondData:
    """Explicit crystal connectivity edge data representation."""
    source_site_index: int
    target_site_index: int
    distance_angstrom: float
    coordination_method: str = "CrystalNN"
    target_element: str = ""
    target_species: str = ""

@dataclass
class SiteData:
    """Atomic crystallographic site model with connectivity neighbors."""
    index: int
    element_symbol: str
    fractional_x: float
    fractional_y: float
    fractional_z: float
    oxidation_state: int | float | None = None
    coordination_number: int | None = None
    coordination_geometry: str | None = None
    species_symbol: str = ""
    neighbors: list[BondData] = field(default_factory=list)
    provenance: str = "Materials Project API / Cache"

    def __post_init__(self):
        if not self.species_symbol:
            ox_str = f"{int(self.oxidation_state):+d}" if self.oxidation_state is not None else ""
            self.species_symbol = f"{self.element_symbol}{ox_str}"

@dataclass
class MaterialRecord:
    """
    Unified Material Record entity preserving original structure, connectivity graph,
    and multi-level provenance across processing steps.
    """
    # ── Step 1: Materials Project Metadata & Structural Representation ──
    material_id: str
    formula: str
    composition: dict[str, float] = field(default_factory=dict)
    cif: str | None = None
    structure_dict: dict[str, Any] | None = field(default_factory=dict)
    symmetry_symbol: str = "P1"
    spacegroup_number: int = 1
    crystal_system: str = "Triclinic"
    band_gap: float = 0.0
    formation_energy_per_atom: float = 0.0
    energy_above_hull: float = 0.0
    density: float = 0.0
    volume: float = 0.0
    energy_per_atom: float | None = None
    density_atomic: float | None = None
    is_stable: bool = False
    e_fermi: float | None = None
    magnetic_ordering: str | None = None
    total_magnetization: float | None = None
    total_magnetization_normalized_formula_units: float | None = None
    total_magnetization_normalized_vol: float | None = None
    is_metal: bool | None = None
    is_gap_direct: bool | None = None
    elastic_k_vrh: float | None = None  # Bulk modulus (GPa)
    elastic_g_vrh: float | None = None  # Shear modulus (GPa)
    universal_anisotropy: float | None = None
    poisson_ratio: float | None = None
    num_sites: int | None = None
    nelements: int | None = None
    num_magnetic_sites: int | None = None
    num_unique_magnetic_sites: int | None = None
    chemsys: str | None = None
    point_group: str | None = None
    is_theoretical: bool | None = None
    task_ids: list[str] = field(default_factory=list)

    # ── Step 2: Pymatgen Structural Enrichment & Connectivity ──
    lattice_a: float = 0.0
    lattice_b: float = 0.0
    lattice_c: float = 0.0
    alpha: float = 90.0
    beta: float = 90.0
    gamma: float = 90.0
    sites: list[SiteData] = field(default_factory=list)
    coordination_method_used: str = "CrystalNN"

    # ── Step 3: SMACT Chemical Enrichment ──
    smact_is_valid: bool = False
    smact_neutrality: bool = False
    smact_oxidation_states: dict[str, int] = field(default_factory=dict)
    electronegativity_map: dict[str, float] = field(default_factory=dict)

    # ── Step 4: BattINFO Semantic Enrichment ──
    battery_role: str | None = None          # e.g. "PositiveElectrode", "NegativeElectrode", "Electrolyte"
    is_active_material: bool = False
    battery_role_iri: str | None = None       # EMMO/BattINFO IRI
    battery_role_evidence: str | None = None  # Provenance rationale

    # ── Step 5: Structural-Prototype Classification (battgpt: StructureFamily taxonomy, v0.3.0) ──
    structure_family: str | None = None           # leaf battgpt: class local name, e.g. "OlivineStructure"
    structure_family_evidence: str | None = None   # curated rationale (formula + space group)

    # ── Step 6: Battery-Cell-Level Electrochemistry (battgpt: v0.3.0, from MP insertion-electrode data) ──
    working_ion: str | None = None
    average_voltage: float | None = None          # V, -> hasOpenCircuitVoltage
    capacity_grav: float | None = None            # mAh/g, -> hasSpecificCapacity
    electrode_battery_formula: str | None = None
    electrode_evidence: str | None = None

    # ── Provenance & Execution Diagnostics ──
    provenance_map: dict[str, str] = field(default_factory=lambda: {
        "material_id": "Materials Project API / Cache",
        "structure": "Materials Project API / Cache",
        "cif": "Materials Project API / Cache"
    })
    processing_status: dict[str, Any] = field(default_factory=lambda: {
        "pmg_success": False,
        "smact_success": False,
        "errors": []
    })

    def get_properties(self) -> list[PropertyData]:
        """Return quantitative property objects with explicit provenance."""
        mp_prov = self.provenance_map.get("material_id", "Materials Project API / Cache")
        props = [
            PropertyData("band_gap", self.band_gap, "http://qudt.org/vocab/unit/EV", "eV", mp_prov, "Electronic band gap"),
            PropertyData("formation_energy_per_atom", self.formation_energy_per_atom, "http://qudt.org/vocab/unit/EV", "eV/atom", mp_prov, "DFT formation energy per atom"),
            PropertyData("energy_above_hull", self.energy_above_hull, "http://qudt.org/vocab/unit/EV", "eV/atom", mp_prov, "Thermodynamic energy above convex hull"),
            PropertyData("density", self.density, "http://qudt.org/vocab/unit/G-PER-CentiM3", "g/cm³", mp_prov, "Crystallographic density"),
            PropertyData("volume", self.volume, "http://qudt.org/vocab/unit/ANGSTROM3", "Å³", mp_prov, "Unit cell volume")
        ]
        if self.e_fermi is not None:
            props.append(PropertyData("e_fermi", self.e_fermi, "http://qudt.org/vocab/unit/EV", "eV", mp_prov, "Fermi energy"))
        if self.elastic_k_vrh is not None:
            props.append(PropertyData("bulk_modulus", self.elastic_k_vrh, "http://qudt.org/vocab/unit/GigaPA", "GPa", mp_prov, "Bulk modulus K_VRH"))
        if self.elastic_g_vrh is not None:
            props.append(PropertyData("shear_modulus", self.elastic_g_vrh, "http://qudt.org/vocab/unit/GigaPA", "GPa", mp_prov, "Shear modulus G_VRH"))
        if self.total_magnetization is not None:
            props.append(PropertyData("total_magnetization", self.total_magnetization, "http://qudt.org/vocab/unit/BohrMagneton", "µB", mp_prov, "Total magnetic moment"))
        if self.universal_anisotropy is not None:
            props.append(PropertyData("universal_anisotropy", self.universal_anisotropy, "http://qudt.org/vocab/unit/UNITLESS", "unitless", mp_prov, "Universal elastic anisotropy index"))
        if self.poisson_ratio is not None:
            props.append(PropertyData("poisson_ratio", self.poisson_ratio, "http://qudt.org/vocab/unit/UNITLESS", "unitless", mp_prov, "Poisson ratio"))
        optional_properties = [
            ("energy_per_atom", self.energy_per_atom, "http://qudt.org/vocab/unit/EV", "eV/atom", "DFT energy per atom"),
            ("density_atomic", self.density_atomic, "http://qudt.org/vocab/unit/ANGSTROM3", "Å³/atom", "Atomic volume"),
            ("total_magnetization_normalized_formula_units", self.total_magnetization_normalized_formula_units, "http://qudt.org/vocab/unit/BohrMagneton", "µB/formula unit", "Total magnetization normalized by formula units"),
            ("total_magnetization_normalized_vol", self.total_magnetization_normalized_vol, "http://qudt.org/vocab/unit/BohrMagneton", "µB/Å³", "Total magnetization normalized by volume"),
            ("nelements", self.nelements, "http://qudt.org/vocab/unit/UNITLESS", "count", "Number of chemical elements"),
            ("num_magnetic_sites", self.num_magnetic_sites, "http://qudt.org/vocab/unit/UNITLESS", "count", "Number of magnetic sites"),
            ("num_unique_magnetic_sites", self.num_unique_magnetic_sites, "http://qudt.org/vocab/unit/UNITLESS", "count", "Number of unique magnetic sites"),
        ]
        for name, value, unit_iri, unit_symbol, description in optional_properties:
            if value is not None:
                props.append(PropertyData(name, float(value), unit_iri, unit_symbol, mp_prov, description))
        return props
