#!/usr/bin/env python3
"""Phase 1: Verify Materials Project API access.

Loads .env, authenticates, reports API connection details, and fetches
a known material (mp-149) as a smoke test.
"""
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from mp_api.client import MPRester

# Check key is visible after dotenv load
import os
key = os.getenv("MP_API_KEY")
assert key, "MP_API_KEY not loaded from .env"
print(f"[OK] MP_API_KEY loaded from .env (length={len(key)}, prefix='{key[:4]}...')")

with MPRester(key) as mpr:
    # Connection + API version
    print(f"[OK] MPRester context established (key prefix '{key[:4]}...')")
    try:
        v = mpr.api_version
        print(f"[OK] Materials Project API version: {v}")
    except Exception as e:
        print(f"[info] api_version not exposed on client: {e}")

    # Smoke test: fetch mp-149 (Si)
    doc = mpr.materials.summary.get_data_by_id("mp-149")
    print(f"[OK] Fetched mp-149")
    print(f"     formula_pretty      : {doc.formula_pretty}")
    print(f"     structure           : {type(doc.structure).__name__}, {len(doc.structure)} sites")
    print(f"     lattice             : a={doc.structure.lattice.a:.4f} b={doc.structure.lattice.b:.4f} c={doc.structure.lattice.c:.4f}")
    print(f"     volume              : {doc.structure.volume:.3f}")
    print(f"     density             : {doc.density:.4f}")
    print(f"     spacegroup          : {doc.symmetry.symbol} (#{doc.symmetry.number}, {doc.symmetry.crystal_system})")
    print(f"     band_gap            : {doc.band_gap}")
    print(f"     formation_energy/at : {doc.formation_energy_per_atom}")
    print(f"     e_above_hull        : {doc.energy_above_hull}")
    print(f"     is_stable           : {doc.is_stable}")
    print(f"     magnetic_ordering   : {doc.ordering}")  # SummaryDoc field is `ordering`
    print(f"     e_fermi             : {getattr(doc, 'efermi', None)}")  # SummaryDoc field is `efermi`
    print(f"     material_id         : {doc.material_id}")

print("\nPHASE 1: PASS")
