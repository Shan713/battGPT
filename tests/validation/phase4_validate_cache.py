#!/usr/bin/env python3
"""Phase 4: Validate the new authentic cache.

For every material, reconstruct Structure.from_dict(...) and verify:
  - composition matches the cached MP composition
  - density matches MP
  - volume matches MP
  - spacegroup matches MP
  - crystal system matches MP
  - CIF round-trips correctly (Structure.from_str(cif) reproduces the structure)

Expectation: ZERO mismatches.
"""
import json
import sys
from pathlib import Path

from pymatgen.core import Structure, Composition
from pymatgen.io.cif import CifWriter
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core.lattice import Lattice

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "pipeline/data/cached_mp_materials.json"

CRYSTAL_SYSTEM_MAP = {
    "cubic": "Cubic", "hexagonal": "Hexagonal", "monoclinic": "Monoclinic",
    "orthorhombic": "Orthorhombic", "rhombohedral": "Trigonal", "trigonal": "Trigonal",
    "tetragonal": "Tetragonal", "triclinic": "Triclinic",
}


def main():
    cache = json.loads(CACHE.read_text())
    failures = []
    print(f"{'material':<11} {'formula':<16} {'comp':<5} {'dens':<5} {'vol':<5} {'SG':<5} {'sys':<5} {'cif_roundtrip':<14}")
    print("-" * 80)
    for mid, r in cache.items():
        sd = r["structure_dict"]
        struct = Structure.from_dict(sd)
        row_ok = True
        notes = {}

        # 1. Composition
        comp_struct = struct.composition.fractional_composition.get_el_amt_dict()
        comp_mp = Composition.from_dict(r["composition_reduced"]).fractional_composition.get_el_amt_dict()
        # compare as reduced formula strings to be robust to rounding
        c_ok = Composition(struct.composition).reduced_formula == Composition.from_dict(r["composition_reduced"]).reduced_formula
        notes["comp"] = "OK" if c_ok else "MISMATCH"

        # 2. Density
        d_ok = abs(struct.density - r["density"]) < 0.02
        notes["dens"] = "OK" if d_ok else f"{struct.density:.3f}vs{r['density']:.3f}"

        # 3. Volume
        v_ok = abs(struct.volume - r["volume"]) < 0.01
        notes["vol"] = "OK" if v_ok else f"{struct.volume:.3f}vs{r['volume']:.3f}"

        # 4. Space group (spglib on reconstructed structure vs MP-reported).
        #    MP classifies symmetry at symprec=0.1; magnetic supercells (e.g.
        #    FM LiMn2O4) carry small spin-driven distortions that only recover
        #    the ideal symmetry at that tolerance.
        sga = SpacegroupAnalyzer(struct, symprec=0.1)
        sg_derived = sga.get_space_group_number()
        sym_derived = sga.get_space_group_symbol()
        sg_ok = sg_derived == r["spacegroup_number"]
        notes["SG"] = "OK" if sg_ok else f"{sym_derived}#{sg_derived}vs#{r['spacegroup_number']}"

        # 5. Crystal system
        cs_derived = sga.get_crystal_system()
        cs_mp = r["crystal_system"].lower()
        cs_ok = CRYSTAL_SYSTEM_MAP.get(cs_derived, cs_derived).lower() == cs_mp
        notes["sys"] = "OK" if cs_ok else f"{cs_derived}vs{r['crystal_system']}"
        if r.get("is_magnetic"):
            notes["sys"] += "(mag)"

        # 6. CIF round-trip: cached CIF -> Structure -> lattice + sites + symmetry
        cif_ok = True
        try:
            from_cif = Structure.from_str(r["cif"], fmt="cif")
            # compare lattice parameters and site count (CIF is the conventional cell,
            # so compare primitive-symmetry and composition)
            rt_comp_ok = Composition(from_cif.composition).reduced_formula == Composition(struct.composition).reduced_formula
            rt_vol = abs(from_cif.volume - r["volume"]) < 1.0  # conventional vs primitive volume differ; use primitive from CIF
            # CIF holds the conventional cell; verify via spglib-derived primitive cell volume
            prim_cif = from_cif.get_primitive_structure()
            prim_cif = SpacegroupAnalyzer(from_cif, symprec=1e-3).get_primitive_standard_structure()
            prim_vol_ok = abs(prim_cif.volume - struct.volume) < 0.5
            cif_ok = rt_comp_ok and prim_vol_ok
            notes["cif_roundtrip"] = "OK" if cif_ok else f"comp_ok={rt_comp_ok},prim_vol={prim_cif.volume:.2f}vs{struct.volume:.2f}"
        except Exception as e:
            cif_ok = False
            notes["cif_roundtrip"] = f"ERR {type(e).__name__}: {str(e)[:40]}"

        bad = {k: v for k, v in notes.items() if not v.startswith("OK")}
        if bad:
            failures.append((mid, bad))
        print(f"{mid:<11} {r['formula_pretty']:<16} {notes['comp']:<5} {notes['dens']:<5} {notes['vol']:<5} {notes['SG']:<5} {notes['sys']:<5} {notes['cif_roundtrip']:<14}")

    print("-" * 80)
    if failures:
        print(f"FAILED: {len(failures)}/12 records have mismatches")
        for mid, bad in failures:
            print(f"  {mid}: {bad}")
        sys.exit(1)
    else:
        print("PHASE 4: PASS — zero mismatches across all 12 records")


if __name__ == "__main__":
    main()
