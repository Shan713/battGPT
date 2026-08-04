#!/usr/bin/env python3
"""Audit: bit-for-bit internal consistency of cached_mp_materials.json.

Every field in a cache record claims to derive from one Materials Project
doc.structure (_fetch_from_mp_api). If structure_dict, cif, and the scalar
fields (density/volume/spacegroup/composition) contradict each other, the
record cannot be bit-for-bit consistent with any official MP entry.

Compares, per record:
  A. CIF cell vs structure_dict lattice (a,b,c,alpha,beta,gamma,volume)
  B. CIF atom list vs structure_dict sites (count, species, fractional coords)
  C. density(computed from structure_dict) vs cached density
  D. volume(struct) vs cached volume
  E. composition(from sites) vs cached composition
  F. spglib(spacegroup from structure_dict as stored) vs cached spacegroup_number
"""
import json
import math
import sys
from pathlib import Path
from collections import Counter

import numpy as np
from pymatgen.core import Structure, Composition
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

CACHE = Path(__file__).resolve().parents[1] / "pipeline/data/cached_mp_materials.json"


def parse_cif_cell(cif: str):
    vals = {}
    for line in cif.splitlines():
        line = line.strip()
        if line.startswith("_cell_length_"):
            parts = line.split()
            if len(parts) == 2:
                vals["cell_" + parts[0].split("_")[-1]] = float(parts[1])
        if line.startswith("_cell_angle_"):
            parts = line.split()
            if len(parts) == 2:
                vals["angle_" + parts[0].split("_")[-1]] = float(parts[1])
        if line.startswith("_symmetry_Int_Tables_number"):
            parts = line.split()
            if len(parts) == 2:
                vals["sg_number"] = int(parts[1])
        if line.startswith("_symmetry_space_group_name_H-M"):
            parts = line.split("'")
            if len(parts) >= 2:
                vals["sg_hm"] = parts[1].strip()
    return vals


def parse_cif_atoms(cif: str):
    lines = cif.splitlines()
    # find loop_ block with _atom_site_ labels
    atoms = []
    labels = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("_atom_site_") and labels is None:
            # collect label block
            labels = []
            while i < len(lines) and lines[i].strip().startswith("_atom_site_"):
                labels.append(lines[i].strip())
                i += 1
            # next lines are data rows
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("_"):
                atoms.append(lines[i].split())
                i += 1
            break
        i += 1
    parsed = []
    for row in atoms:
        d = {}
        for lab, val in zip(labels, row):
            key = lab.split()[0]
            d[key] = val
        parsed.append(d)
    return parsed, labels


def cif_frac(lab):
    """Return the _atom_site_fract_* label names."""
    return [l for l in lab if "_fract_" in l]


def elem_symbol(ts):
    """'Li+' -> 'Li'; 'Fe2+' -> 'Fe'; handles plain symbols too."""
    import re
    m = re.match(r"([A-Z][a-z]?)", ts or "")
    return m.group(1) if m else ts


def main():
    cache = json.loads(CACHE.read_text())
    print(f"{'material':<12} {'A:cif_cell':<9} {'B:cif_atoms':<10} {'C:density':<9} {'D:volume':<9} {'E:comp':<7} {'F:symmetry':<9}")
    print("-" * 78)
    issues = 0
    for mid, r in cache.items():
        sd = r.get("structure_dict") or {}
        cif = r.get("cif") or ""
        status = {}
        # ---- A: CIF cell vs structure_dict lattice ----
        latt = sd.get("lattice", {})
        a_cif, b_cif, c_cif = None, None, None
        al_cif, be_cif, ga_cif, vol_cif, sg_cif, hm_cif = None, None, None, None, None, None
        if cif:
            cc = parse_cif_cell(cif)
            a_cif, b_cif, c_cif = cc.get("cell_a"), cc.get("cell_b"), cc.get("cell_c")
            al_cif, be_cif, ga_cif = cc.get("angle_alpha"), cc.get("angle_beta"), cc.get("angle_gamma")
            vol_cif = cc.get("volume")
            sg_cif = cc.get("sg_number")
            hm_cif = cc.get("sg_hm")
        a_sd, b_sd, c_sd = latt.get("a"), latt.get("b"), latt.get("c")
        al_sd, be_sd, ga_sd = latt.get("alpha"), latt.get("beta"), latt.get("gamma")
        if cif and a_sd:
            a_ok = abs(a_cif - a_sd) < 1e-6
            b_ok = abs(b_cif - b_sd) < 1e-6
            c_ok = abs(c_cif - c_sd) < 1e-6
            al_ok = abs(al_cif - al_sd) < 1e-6
            be_ok = abs(be_cif - be_sd) < 1e-6
            ga_ok = abs(ga_cif - ga_sd) < 1e-6
            status["A"] = "OK" if all([a_ok, b_ok, c_ok, al_ok, be_ok, ga_ok]) else "MISMATCH"
        else:
            status["A"] = "n/a"

        # ---- B: CIF atoms vs structure_dict sites ----
        sites = sd.get("sites", [])
        site_elems = [s["species"][0]["element"] for s in sites]
        site_abc = [tuple(round(float(x), 6) for x in s["abc"]) for s in sites]
        if cif:
            atoms, labels = parse_cif_atoms(cif)
            at_elems = [elem_symbol(a.get("_atom_site_type_symbol", a.get("_atom_site_label", ""))) for a in atoms]
            frac_labs = cif_frac(labels or [])
            if len(frac_labs) >= 3:
                at_abc = [tuple(round(float(a[fl]), 6) for fl in frac_labs[:3]) for a in atoms]
            else:
                at_abc = None
            count_ok = len(atoms) == len(sites)
            elem_ok = at_elems == site_elems
            coord_ok = at_abc == site_abc if at_abc is not None else None
            if count_ok and elem_ok and (coord_ok is True):
                status["B"] = "OK"
            elif count_ok and elem_ok and coord_ok is False:
                status["B"] = "coords-differ"
            elif count_ok and elem_ok:
                status["B"] = "no-frac"
            else:
                status["B"] = "MISMATCH"
        else:
            status["B"] = "no-cif"

        # ---- C: density from structure_dict vs cached ----
        if sd and "lattice" in sd and sites:
            try:
                struct = Structure.from_dict(sd)
                dens_comp = struct.density
            except Exception as e:
                dens_comp = float("nan")
                status["C"] = f"ERR({type(e).__name__})"
            cache_dens = r.get("density")
            if status.get("C") != "ERR":
                ratio = dens_comp / cache_dens if cache_dens else float("inf")
                status["C"] = f"{dens_comp:.3f}v{ratio:.2f}x" if ratio and (ratio < 0.999 or ratio > 1.001) else "OK"
        else:
            status["C"] = "n/a"

        # ---- D: volume ----
        if latt and latt.get("volume"):
            status["D"] = "OK" if abs(latt["volume"] - r.get("volume", 0)) < 1e-6 else f"SD{latt['volume']}vs{r.get('volume')}"
        else:
            status["D"] = "n/a"

        # ---- E: composition from sites vs cached ----
        if sites:
            comp_sites = Counter(site_elems)
            comp_cache = Counter({k: float(v) for k, v in r.get("composition", {}).items()})
            if comp_sites == comp_cache:
                status["E"] = "OK"
            else:
                status["E"] = f"SD{dict(comp_sites)}vs{dict(comp_cache)}"
        else:
            status["E"] = "n/a"

        # ---- F: spglib from structure_dict as stored vs cached ----
        if sd:
            try:
                struct = Structure.from_dict(sd)
                sg_derived = SpacegroupAnalyzer(struct, symprec=0.1).get_space_group_number()
                sg_cached = r.get("spacegroup_number")
                # also check what a full-cell construction from the same primitive would give
                status["F"] = "OK" if sg_derived == sg_cached else f"{sg_derived}vs{sg_cached}"
            except Exception as e:
                status["F"] = f"ERR({type(e).__name__})"
        else:
            status["F"] = "n/a"

        bad = [k for k, v in status.items() if v not in ("OK", "n/a")]
        if bad:
            issues += 1
        print(f"{mid:<12} {status.get('A','?'):<9} {status.get('B','?'):<10} {status.get('C','?'):<9} {status.get('D','?'):<9} {status.get('E','?'):<7} {status.get('F','?'):<9}")

    print("-" * 78)
    print(f"Records with >=1 inconsistency: {issues}/12")
    # Extra: CIF internal symmetry header vs cell
    print("\n=== CIF internal symmetry headers vs cell metrics ===")
    for mid, r in cache.items():
        cif = r.get("cif") or ""
        if not cif:
            continue
        cc = parse_cif_cell(cif)
        print(f"{mid:<12} {r['formula']:<14} CIF_sg={cc.get('sg_hm')} (#{cc.get('sg_number')})  a={cc.get('cell_a')} c={cc.get('cell_c')}")


if __name__ == "__main__":
    main()
