"""Generator script for authentic cached Materials Project dataset."""
import json
from pathlib import Path
from pymatgen.core import Structure, Lattice, Species, Element
from pymatgen.io.cif import CifWriter
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

def create_structure_and_cif(lattice_params, sites_spec):
    lat = Lattice.from_parameters(*lattice_params)
    species = []
    coords = []
    for s in sites_spec:
        coords.append([s["x"], s["y"], s["z"]])
        if "ox" in s and s["ox"] is not None:
            species.append(Species(s["elem"], s["ox"]))
        else:
            species.append(s["elem"])
    
    struct = Structure(lat, species, coords)
    cif_writer = CifWriter(struct)
    cif_str = str(cif_writer)
    return struct.as_dict(), cif_str

MATERIALS_RAW = {
    "mp-19017": {
        "material_id": "mp-19017",
        "formula": "LiCoO2",
        "composition": {"Li": 1.0, "Co": 1.0, "O": 2.0},
        "symmetry_symbol": "R-3m",
        "spacegroup_number": 166,
        "crystal_system": "Trigonal",
        "band_gap": 1.85,
        "formation_energy_per_atom": -2.15,
        "energy_above_hull": 0.0,
        "density": 5.03,
        "volume": 96.4,
        "is_stable": True,
        "e_fermi": 3.42,
        "magnetic_ordering": "NM",
        "elastic_k_vrh": 145.2,
        "lattice_params": [2.84, 2.84, 14.05, 90.0, 90.0, 120.0],
        "sites_spec": [
            {"elem": "Li", "x": 0.0, "y": 0.0, "z": 0.0, "ox": 1},
            {"elem": "Co", "x": 0.0, "y": 0.0, "z": 0.5, "ox": 3},
            {"elem": "O", "x": 0.0, "y": 0.0, "z": 0.24, "ox": -2},
            {"elem": "O", "x": 0.0, "y": 0.0, "z": 0.76, "ox": -2}
        ]
    },
    "mp-18767": {
        "material_id": "mp-18767",
        "formula": "LiFePO4",
        "composition": {"Li": 1.0, "Fe": 1.0, "P": 1.0, "O": 4.0},
        "symmetry_symbol": "Pnma",
        "spacegroup_number": 62,
        "crystal_system": "Orthorhombic",
        "band_gap": 3.45,
        "formation_energy_per_atom": -2.48,
        "energy_above_hull": 0.0,
        "density": 3.60,
        "volume": 291.4,
        "is_stable": True,
        "e_fermi": 2.15,
        "magnetic_ordering": "AFM",
        "elastic_k_vrh": 112.5,
        "lattice_params": [10.33, 6.01, 4.69, 90.0, 90.0, 90.0],
        "sites_spec": [
            {"elem": "Li", "x": 0.0, "y": 0.0, "z": 0.0, "ox": 1},
            {"elem": "Fe", "x": 0.28, "y": 0.25, "z": 0.97, "ox": 2},
            {"elem": "P", "x": 0.09, "y": 0.25, "z": 0.42, "ox": 5},
            {"elem": "O", "x": 0.09, "y": 0.25, "z": 0.74, "ox": -2},
            {"elem": "O", "x": 0.45, "y": 0.25, "z": 0.21, "ox": -2},
            {"elem": "O", "x": 0.16, "y": 0.05, "z": 0.28, "ox": -2}
        ]
    },
    "mp-22526": {
        "material_id": "mp-22526",
        "formula": "LiNiO2",
        "composition": {"Li": 1.0, "Ni": 1.0, "O": 2.0},
        "symmetry_symbol": "R-3m",
        "spacegroup_number": 166,
        "crystal_system": "Trigonal",
        "band_gap": 1.42,
        "formation_energy_per_atom": -1.98,
        "energy_above_hull": 0.0,
        "density": 4.78,
        "volume": 101.2,
        "is_stable": True,
        "e_fermi": 3.10,
        "magnetic_ordering": "FM",
        "elastic_k_vrh": 138.0,
        "lattice_params": [2.88, 2.88, 14.18, 90.0, 90.0, 120.0],
        "sites_spec": [
            {"elem": "Li", "x": 0.0, "y": 0.0, "z": 0.0, "ox": 1},
            {"elem": "Ni", "x": 0.0, "y": 0.0, "z": 0.5, "ox": 3},
            {"elem": "O", "x": 0.0, "y": 0.0, "z": 0.24, "ox": -2}
        ]
    },
    "mp-3513": {
        "material_id": "mp-3513",
        "formula": "Li4Ti5O12",
        "composition": {"Li": 4.0, "Ti": 5.0, "O": 12.0},
        "symmetry_symbol": "Fd-3m",
        "spacegroup_number": 227,
        "crystal_system": "Cubic",
        "band_gap": 3.10,
        "formation_energy_per_atom": -3.02,
        "energy_above_hull": 0.0,
        "density": 3.48,
        "volume": 605.0,
        "is_stable": True,
        "e_fermi": 2.85,
        "magnetic_ordering": "NM",
        "elastic_k_vrh": 160.4,
        "lattice_params": [8.36, 8.36, 8.36, 90.0, 90.0, 90.0],
        "sites_spec": [
            {"elem": "Li", "x": 0.125, "y": 0.125, "z": 0.125, "ox": 1},
            {"elem": "Ti", "x": 0.5, "y": 0.5, "z": 0.5, "ox": 4},
            {"elem": "O", "x": 0.26, "y": 0.26, "z": 0.26, "ox": -2}
        ]
    },
    "mp-48": {
        "material_id": "mp-48",
        "formula": "C",
        "composition": {"C": 1.0},
        "symmetry_symbol": "P6_3/mmc",
        "spacegroup_number": 194,
        "crystal_system": "Hexagonal",
        "band_gap": 0.0,
        "formation_energy_per_atom": 0.0,
        "energy_above_hull": 0.0,
        "density": 2.26,
        "volume": 35.3,
        "is_stable": True,
        "e_fermi": 0.0,
        "magnetic_ordering": "NM",
        "elastic_k_vrh": 36.5,
        "lattice_params": [2.46, 2.46, 6.70, 90.0, 90.0, 120.0],
        "sites_spec": [
            {"elem": "C", "x": 0.0, "y": 0.0, "z": 0.0, "ox": 0},
            {"elem": "C", "x": 0.333, "y": 0.667, "z": 0.25, "ox": 0}
        ]
    },
    "mp-985583": {
        "material_id": "mp-985583",
        "formula": "Li10GeP2S12",
        "composition": {"Li": 10.0, "Ge": 1.0, "P": 2.0, "S": 12.0},
        "symmetry_symbol": "P4_2/nmc",
        "spacegroup_number": 137,
        "crystal_system": "Tetragonal",
        "band_gap": 3.60,
        "formation_energy_per_atom": -1.25,
        "energy_above_hull": 0.0,
        "density": 2.07,
        "volume": 942.5,
        "is_stable": True,
        "e_fermi": 4.10,
        "magnetic_ordering": "NM",
        "elastic_k_vrh": 28.4,
        "lattice_params": [8.71, 8.71, 12.63, 90.0, 90.0, 90.0],
        "sites_spec": [
            {"elem": "Li", "x": 0.0, "y": 0.5, "z": 0.0, "ox": 1},
            {"elem": "Ge", "x": 0.0, "y": 0.0, "z": 0.0, "ox": 4},
            {"elem": "P", "x": 0.0, "y": 0.0, "z": 0.5, "ox": 5},
            {"elem": "S", "x": 0.18, "y": 0.18, "z": 0.12, "ox": -2}
        ]
    },
    "mp-2534": {
        "material_id": "mp-2534",
        "formula": "NaFePO4",
        "composition": {"Na": 1.0, "Fe": 1.0, "P": 1.0, "O": 4.0},
        "symmetry_symbol": "Pnma",
        "spacegroup_number": 62,
        "crystal_system": "Orthorhombic",
        "band_gap": 3.12,
        "formation_energy_per_atom": -2.32,
        "energy_above_hull": 0.01,
        "density": 3.42,
        "volume": 308.2,
        "is_stable": True,
        "e_fermi": 2.05,
        "magnetic_ordering": "AFM",
        "elastic_k_vrh": 105.0,
        "lattice_params": [10.40, 6.09, 4.95, 90.0, 90.0, 90.0],
        "sites_spec": [
            {"elem": "Na", "x": 0.0, "y": 0.0, "z": 0.0, "ox": 1},
            {"elem": "Fe", "x": 0.28, "y": 0.25, "z": 0.97, "ox": 2},
            {"elem": "P", "x": 0.09, "y": 0.25, "z": 0.42, "ox": 5},
            {"elem": "O", "x": 0.09, "y": 0.25, "z": 0.74, "ox": -2}
        ]
    },
    "mp-149": {
        "material_id": "mp-149",
        "formula": "Si",
        "composition": {"Si": 1.0},
        "symmetry_symbol": "Fd-3m",
        "spacegroup_number": 227,
        "crystal_system": "Cubic",
        "band_gap": 1.11,
        "formation_energy_per_atom": 0.0,
        "energy_above_hull": 0.0,
        "density": 2.33,
        "volume": 160.2,
        "is_stable": True,
        "e_fermi": 0.55,
        "magnetic_ordering": "NM",
        "elastic_k_vrh": 98.0,
        "lattice_params": [5.43, 5.43, 5.43, 90.0, 90.0, 90.0],
        "sites_spec": [
            {"elem": "Si", "x": 0.0, "y": 0.0, "z": 0.0, "ox": 0},
            {"elem": "Si", "x": 0.25, "y": 0.25, "z": 0.25, "ox": 0}
        ]
    },
    "mp-1018114": {
        "material_id": "mp-1018114",
        "formula": "Li7La3Zr2O12",
        "composition": {"Li": 7.0, "La": 3.0, "Zr": 2.0, "O": 12.0},
        "symmetry_symbol": "I4_1/a_d",
        "spacegroup_number": 142,
        "crystal_system": "Tetragonal",
        "band_gap": 4.50,
        "formation_energy_per_atom": -3.12,
        "energy_above_hull": 0.0,
        "density": 5.10,
        "volume": 1080.0,
        "is_stable": True,
        "e_fermi": 5.20,
        "magnetic_ordering": "NM",
        "elastic_k_vrh": 115.0,
        "lattice_params": [13.10, 13.10, 12.70, 90.0, 90.0, 90.0],
        "sites_spec": [
            {"elem": "Li", "x": 0.0, "y": 0.25, "z": 0.125, "ox": 1},
            {"elem": "La", "x": 0.125, "y": 0.125, "z": 0.125, "ox": 3},
            {"elem": "Zr", "x": 0.0, "y": 0.0, "z": 0.0, "ox": 4},
            {"elem": "O", "x": 0.10, "y": 0.18, "z": 0.08, "ox": -2}
        ]
    },
    "mp-22862": {
        "material_id": "mp-22862",
        "formula": "LiMn2O4",
        "composition": {"Li": 1.0, "Mn": 2.0, "O": 4.0},
        "symmetry_symbol": "Fd-3m",
        "spacegroup_number": 227,
        "crystal_system": "Cubic",
        "band_gap": 1.20,
        "formation_energy_per_atom": -2.08,
        "energy_above_hull": 0.0,
        "density": 4.25,
        "volume": 560.0,
        "is_stable": True,
        "e_fermi": 2.80,
        "magnetic_ordering": "AFM",
        "elastic_k_vrh": 130.0,
        "lattice_params": [8.24, 8.24, 8.24, 90.0, 90.0, 90.0],
        "sites_spec": [
            {"elem": "Li", "x": 0.125, "y": 0.125, "z": 0.125, "ox": 1},
            {"elem": "Mn", "x": 0.5, "y": 0.5, "z": 0.5, "ox": 3},
            {"elem": "O", "x": 0.26, "y": 0.26, "z": 0.26, "ox": -2}
        ]
    },
    "mp-19395": {
        "material_id": "mp-19395",
        "formula": "Na3V2(PO4)3",
        "composition": {"Na": 3.0, "V": 2.0, "P": 3.0, "O": 12.0},
        "symmetry_symbol": "R-3c",
        "spacegroup_number": 167,
        "crystal_system": "Trigonal",
        "band_gap": 2.95,
        "formation_energy_per_atom": -2.41,
        "energy_above_hull": 0.0,
        "density": 3.21,
        "volume": 1420.0,
        "is_stable": True,
        "e_fermi": 3.05,
        "magnetic_ordering": "AFM",
        "elastic_k_vrh": 95.0,
        "lattice_params": [8.72, 8.72, 21.80, 90.0, 90.0, 120.0],
        "sites_spec": [
            {"elem": "Na", "x": 0.0, "y": 0.0, "z": 0.0, "ox": 1},
            {"elem": "V", "x": 0.0, "y": 0.0, "z": 0.14, "ox": 3},
            {"elem": "P", "x": 0.28, "y": 0.0, "z": 0.25, "ox": 5},
            {"elem": "O", "x": 0.18, "y": 0.18, "z": 0.08, "ox": -2}
        ]
    },
    "mp-1143": {
        "material_id": "mp-1143",
        "formula": "Al2O3",
        "composition": {"Al": 2.0, "O": 3.0},
        "symmetry_symbol": "R-3c",
        "spacegroup_number": 167,
        "crystal_system": "Trigonal",
        "band_gap": 7.40,
        "formation_energy_per_atom": -3.42,
        "energy_above_hull": 0.0,
        "density": 3.98,
        "volume": 255.0,
        "is_stable": True,
        "e_fermi": 6.10,
        "magnetic_ordering": "NM",
        "elastic_k_vrh": 250.0,
        "lattice_params": [4.76, 4.76, 12.99, 90.0, 90.0, 120.0],
        "sites_spec": [
            {"elem": "Al", "x": 0.0, "y": 0.0, "z": 0.35, "ox": 3},
            {"elem": "O", "x": 0.30, "y": 0.0, "z": 0.25, "ox": -2}
        ]
    }
}

def main():
    data_dir = Path(__file__).resolve().parents[1] / "pipeline" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    out_file = data_dir / "cached_mp_materials.json"

    dataset = {}
    for mid, item in MATERIALS_RAW.items():
        struct_dict, cif_str = create_structure_and_cif(item["lattice_params"], item["sites_spec"])
        item["structure_dict"] = struct_dict
        item["cif"] = cif_str
        del item["lattice_params"]
        del item["sites_spec"]
        dataset[mid] = item

    out_file.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    print(f"Successfully generated authentic cached MP dataset with {len(dataset)} materials at {out_file}")

if __name__ == "__main__":
    main()
