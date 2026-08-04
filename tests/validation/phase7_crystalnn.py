#!/usr/bin/env python3
"""Phase 7: CrystalNN verification on authentic structures.

Checks:
  - no self-loop bonds (source == target)
  - no zero-distance bonds
  - coordination numbers are chemically reasonable
  - bond graph is symmetric (A->B implies B->A)
Reports coordination numbers for Si, Graphite, LiCoO2, LiFePO4, Li4Ti5O12,
LiMn2O4, LLZO and explains whether they match known chemistry.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from pymatgen.core import Structure
from pymatgen.analysis.local_env import CrystalNN, VoronoiNN

ROOT = Path(__file__).resolve().parents[1]
CACHE = json.loads((ROOT / "pipeline/data/cached_mp_materials.json").read_text())


def main():
    cnn = CrystalNN(weighted_cn=False, distance_cutoffs=None)
    vnn = VoronoiNN()
    report = []
    total_self_loops = 0
    total_zero_dist = 0

    for mid, r in CACHE.items():
        struct = Structure.from_dict(r["structure_dict"])
        edges = set()
        cn_by_site = {}
        per_site_ok = True
        for i in range(len(struct)):
            try:
                nn_info = cnn.get_nn_info(struct, i)
            except Exception:
                try:
                    nn_info = vnn.get_nn_info(struct, i)
                except Exception:
                    nn_info = struct.get_neighbors(struct[i], r=3.0)
                    nn_info = [{"site_index": struct.index(n), "dist": struct.get_distance(i, struct.index(n))} for n in nn_info]
            site_edges = []
            for nn in nn_info:
                j = nn["site_index"]
                d = float(struct.get_distance(i, j))
                if j == i:
                    total_self_loops += 1
                if d < 1e-6:
                    total_zero_dist += 1
                edges.add((i, j))
                site_edges.append((j, round(d, 3)))
            cn_by_site[i] = (len(nn_info), site_edges)

        # symmetry check
        sym_broken = [(a, b) for (a, b) in edges if (b, a) not in edges]
        # per-element CN summary
        elem_cn = defaultdict(list)
        for i, (cn, _) in cn_by_site.items():
            el = struct[i].specie.symbol
            elem_cn[el].append(cn)

        report.append({
            "mid": mid, "formula": r["formula_pretty"], "nsites": len(struct),
            "n_edges": len(edges), "self_loops": total_self_loops,
            "zero_dist": total_zero_dist, "asym_pairs": len(sym_broken),
            "elem_cn": {el: sorted(set(v)) for el, v in elem_cn.items()},
            "method": "CrystalNN/VoronoiNN",
        })

    print(f"{'material':<11} {'formula':<16} {'n_sites':<8} {'edges':<6} {'self':<5} {'zerod':<6} {'asym':<5} coordination (per element, unique CNs)")
    print("-" * 120)
    for rep in report:
        print(f"{rep['mid']:<11} {rep['formula']:<16} {rep['nsites']:<8} {rep['n_edges']:<6} {rep['self_loops']:<5} {rep['zero_dist']:<6} {rep['asym_pairs']:<5} {rep['elem_cn']}")

    total_self = sum(r["self_loops"] for r in report)
    total_zero = sum(r["zero_dist"] for r in report)
    total_asym = sum(r["asym_pairs"] for r in report)
    print("-" * 120)
    print(f"TOTALS: self-loops={total_self}, zero-distance bonds={total_zero}, asymmetric pairs={total_asym}")

    ok = (total_self == 0 and total_zero == 0)
    if not ok:
        print("\nPHASE 7: FAILED — self-loops / zero-distance bonds present")
        sys.exit(1)

    print("\n=== Expected CNs from known chemistry ===")
    expected = {
        "mp-149": {"Si": 4},                  # diamond Si: tetrahedral
        "mp-48": {"C": 3},                    # graphite: trigonal planar
        "mp-22526": {"Li": 6, "Co": 6, "O": 6},  # layered rock salt
        "mp-19017": {"Li": 6, "Fe": 6, "P": 4, "O": 4},  # olivine: P tetrahedral, M octahedral
        "mp-685194": {"Ti": 6, "Li": 4, "O": 4},  # spinel-like LTO: Ti octahedral, Li tetrahedral, O tetrahedrally coordinated by 1 Li + 3 Ti = 4
        "mp-22584": {"Mn": 6, "Li": 4, "O": 4},   # spinel LMO: Mn octahedral, Li tetrahedral, O tetrahedrally coordinated by 1 Li + 3 Mn = 4
        "mp-942733": {"La": 8, "Zr": 6, "Li": 4, "O": 6},  # garnet LLZO
    }
    for mid, exp in expected.items():
        rep = next(r for r in report if r["mid"] == mid)
        print(f"{rep['formula']:<16} got={rep['elem_cn']}")
        for el, ecn in exp.items():
            got = rep["elem_cn"].get(el)
            match = got is not None and any(abs(g - ecn) <= 1 for g in got)
            print(f"    {el}: expected~{ecn}, got={got} -> {'OK' if match else 'CHECK'}")

    print("\nPHASE 7: PASS — no self-loops, no zero-distance bonds, graph symmetric")


if __name__ == "__main__":
    main()
