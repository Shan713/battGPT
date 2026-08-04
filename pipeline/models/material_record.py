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
    is_stable: bool = False
    e_fermi: float | None = None
    magnetic_ordering: str | None = None
    elastic_k_vrh: float | None = None

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
            props.append(PropertyData("elastic_k_vrh", self.elastic_k_vrh, "http://qudt.org/vocab/unit/GigaPA", "GPa", mp_prov, "Bulk modulus K_VRH"))
        return props
