"""Battery-Cell-Level Electrochemistry Enrichment Engine.

Attaches authentic, Materials-Project-computed insertion-electrode electrochemistry (open-circuit
voltage, gravimetric specific capacity) to cathode/anode MaterialRecords, sourced from
pipeline/data/cached_electrode_data.json — a real API snapshot (mp_api.client.MPRester
.materials.insertion_electrodes.search), not synthesized or estimated values. Materials absent
from that cache (no matching insertion-electrode entry in Materials Project) are left unenriched
rather than backfilled with placeholder numbers.
"""
import json
import logging
from pathlib import Path
from ..models import MaterialRecord

logger = logging.getLogger(__name__)

CACHE_FILE = Path(__file__).resolve().parents[1] / "data" / "cached_electrode_data.json"


def fetch_insertion_electrode_index(mpr, material_ids, working_ions=("Li", "Na")) -> dict:
    """Live MP insertion-electrode data for `material_ids`, in the same entry format as the cache.

    The cache holds 10 materials; MP's insertion-electrode collection covers ~770 of a 5,000-material
    Li/Na KG (K-Ont BUILD_LOG Step 24). A material can belong to several electrodes (every
    intermediate composition is listed); the one kept is, in order: the electrode whose fully
    discharged end member IS this material, then one where it is either end member, then the one with
    the most voltage steps, then by battery formula -- deterministic, and stated in the entry."""
    from datetime import datetime, timezone
    wanted = set(material_ids)
    fetched = datetime.now(timezone.utc).isoformat()
    best = {}
    for ion in working_ions:
        docs = mpr.materials.insertion_electrodes.search(working_ion=ion, fields=[
            "battery_formula", "working_ion", "num_steps", "average_voltage", "capacity_grav", "capacity_vol",
            "energy_grav", "energy_vol", "framework_formula", "max_voltage_step", "material_ids",
            "id_charge", "id_discharge"])
        for d in docs:
            ids = [str(m) for m in (d.material_ids or [])]
            if d.average_voltage is None or d.capacity_grav is None:
                continue
            for mid in wanted.intersection(ids):
                key = (mid == str(d.id_discharge), mid in (str(d.id_charge), str(d.id_discharge)),
                       d.num_steps or 0, str(d.battery_formula))
                if mid not in best or key > best[mid][0]:
                    best[mid] = (key, d, ion)
    index = {}
    for mid, (key, d, ion) in best.items():
        index[mid] = {
            "_meta": {"source": "Materials Project API (live)", "endpoint": "materials.insertion_electrodes.search",
                      "client": "mp-api", "fetched_at_utc": fetched, "matched_material_id": mid,
                      "match": ("discharged end member" if key[0] else "end member" if key[1]
                                else "intermediate composition")},
            "battery_formula": str(d.battery_formula), "working_ion": str(d.working_ion or ion),
            "num_steps": d.num_steps, "average_voltage": float(d.average_voltage),
            "capacity_grav": float(d.capacity_grav),
            "capacity_vol": d.capacity_vol, "energy_grav": d.energy_grav, "energy_vol": d.energy_vol,
            "framework_formula": str(d.framework_formula), "max_voltage_step": d.max_voltage_step,
            "material_ids_in_electrode": [str(m) for m in (d.material_ids or [])],
        }
    return index


class ElectrochemistryProcessor:
    """Enriches MaterialRecords with real MP insertion-electrode electrochemical data."""

    def __init__(self, live_index: dict | None = None):
        self._cache: dict | None = None
        self._live = live_index or {}

    def _load_cache(self) -> dict:
        if self._cache is None:
            if CACHE_FILE.exists():
                self._cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            else:
                logger.warning(f"Electrode data cache not found at {CACHE_FILE}.")
                self._cache = {}
        return self._cache

    def process(self, record: MaterialRecord) -> MaterialRecord:
        """Enrich MaterialRecord with cell-level electrochemistry: the cached snapshot first (so those
        10 materials stay exactly as before), then the live index if one was passed in."""
        entry = self._load_cache().get(record.material_id) or self._live.get(record.material_id)
        if entry:
            record.working_ion = entry["working_ion"]
            record.average_voltage = entry["average_voltage"]
            record.capacity_grav = entry["capacity_grav"]
            record.electrode_battery_formula = entry.get("battery_formula")
            record.electrode_evidence = (
                f"Materials Project insertion-electrode calculation ({entry['working_ion']}-ion, "
                f"{entry.get('num_steps', 1)} voltage step(s)); "
                f"{entry['_meta']['endpoint']}, fetched {entry['_meta']['fetched_at_utc']}"
            )
            logger.debug(
                f"Attached electrochemistry to {record.formula}: "
                f"V_OCV={record.average_voltage:.3f} V, specific capacity={record.capacity_grav:.1f} mAh/g"
            )
        return record
