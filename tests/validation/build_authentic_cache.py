#!/usr/bin/env python3
"""Phase 3: Build an authentic Materials Project cache.

Fetches every battery material directly from the live Materials Project API and
stores exactly what MP returns (structure, symmetry, properties). Nothing is
synthesized, approximated, or reused from the archived synthetic dataset.

Usage:
    python validation/build_authentic_cache.py [output.json]

Output (default pipeline/data/cached_mp_materials.json):
    { material_id: { ...record... } }
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

import os
from mp_api.client import MPRester
from pymatgen.io.cif import CifWriter

# The pipeline's intended battery materials mapped to their API-verified
# current Materials Project IDs (see pipeline/config/config.py).
BATTERY_IDS = [
    "mp-22526",   # LiCoO2   (Cathode)
    "mp-19017",   # LiFePO4  (Cathode)
    "mp-25411",   # LiNiO2   (Cathode)
    "mp-685194",  # Li4Ti5O12(Anode)
    "mp-48",      # C        (Anode)
    "mp-696128",  # LGPS     (Solid Electrolyte)
    "mp-19226",   # NaFePO4  (Na-ion Cathode)
    "mp-149",     # Si       (Anode)
    "mp-942733",  # LLZO     (Solid Electrolyte)
    "mp-22584",   # LiMn2O4  (Spinel Cathode)
    "mp-776557",  # Na3V2(PO4)3 (NASICON Na Cathode)
    "mp-1143",    # Al2O3    (Separator coating)
]


def fetch_record(mpr, material_id: str) -> dict:
    """Fetch one material and store EXACTLY what the MP API returns."""
    doc = mpr.materials.summary.get_data_by_id(material_id)
    struct = doc.structure
    latt = struct.lattice
    sym = doc.symmetry

    # CIF generated from the authentic MP Structure, with symmetry reduction so
    # the CIF header carries the correct space group.
    cif = str(CifWriter(struct, symprec=1e-3))

    return {
        "_meta": {
            "source": "Materials Project API (live)",
            "endpoint": "materials.summary.get_data_by_id",
            "client": "mp-api",
            "client_version": "0.46.4",
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "material_id": material_id,
        },
        # Identity / composition — verbatim from MP
        "material_id": str(doc.material_id),
        "formula_pretty": doc.formula_pretty,
        "formula_anonymous": doc.formula_anonymous,
        "composition": {str(k): float(v) for k, v in doc.composition.items()},
        "composition_reduced": {str(k): float(v) for k, v in doc.composition_reduced.items()},
        "chemsys": doc.chemsys,
        "elements": [str(e) for e in doc.elements],
        "nelements": doc.nelements,
        "nsites": doc.nsites,
        # Structure — verbatim as returned by MP (charge==0.0 for real structures)
        "structure_dict": struct.as_dict(),
        "lattice": {
            "a": float(latt.a),
            "b": float(latt.b),
            "c": float(latt.c),
            "alpha": float(latt.alpha),
            "beta": float(latt.beta),
            "gamma": float(latt.gamma),
            "volume": float(latt.volume),
            "matrix": latt.matrix.tolist(),
        },
        # CIF generated from the MP structure
        "cif": cif,
        # Symmetry — verbatim from MP
        "spacegroup_number": sym.number,
        "spacegroup_symbol": sym.symbol,
        "crystal_system": sym.crystal_system.value if hasattr(sym.crystal_system, "value") else str(sym.crystal_system),
        "symmetry_hall": getattr(sym, "hall", None),
        "symmetry_point_group": getattr(sym, "point_group", None),
        # Thermodynamic / electronic properties
        "band_gap": doc.band_gap,
        "is_gap_direct": doc.is_gap_direct,
        "is_metal": doc.is_metal,
        "formation_energy_per_atom": doc.formation_energy_per_atom,
        "energy_above_hull": doc.energy_above_hull,
        "energy_per_atom": doc.energy_per_atom,
        "is_stable": doc.is_stable,
        "efermi": doc.efermi,
        "density": doc.density,
        "density_atomic": doc.density_atomic,
        "volume": doc.volume,
        # Magnetic ordering / magnetism
        "ordering": doc.ordering,
        "is_magnetic": doc.is_magnetic,
        "total_magnetization": doc.total_magnetization,
        "total_magnetization_normalized_formula_units": doc.total_magnetization_normalized_formula_units,
        "total_magnetization_normalized_vol": doc.total_magnetization_normalized_vol,
        "num_magnetic_sites": doc.num_magnetic_sites,
        "num_unique_magnetic_sites": doc.num_unique_magnetic_sites,
        "types_of_magnetic_species": [str(s) for s in doc.types_of_magnetic_species] if doc.types_of_magnetic_species else None,
        # Elastic properties (as provided on SummaryDoc)
        "bulk_modulus": doc.bulk_modulus,
        "shear_modulus": doc.shear_modulus,
        "universal_anisotropy": doc.universal_anisotropy,
        "homogeneous_poisson": doc.homogeneous_poisson,
        # Provenance / misc
        "theoretical": doc.theoretical,
        "last_updated": doc.last_updated.isoformat() if doc.last_updated else None,
        "task_ids": [str(t) for t in doc.task_ids] if doc.task_ids else None,
        "warnings": doc.warnings,
    }


def main():
    out_path = ROOT / "pipeline" / "data" / "cached_mp_materials.json"
    if len(sys.argv) > 1:
        out_path = Path(sys.argv[1])

    key = os.getenv("MP_API_KEY")
    if not key:
        print("FATAL: MP_API_KEY not loaded from .env", file=sys.stderr)
        sys.exit(1)

    cache = {}
    with MPRester(key) as mpr:
        for mid in BATTERY_IDS:
            print(f"Fetching {mid} ...", flush=True)
            cache[mid] = fetch_record(mpr, mid)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    print(f"\nWrote {len(cache)} authentic records to {out_path}")


if __name__ == "__main__":
    main()
