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


class ElectrochemistryProcessor:
    """Enriches MaterialRecords with real MP insertion-electrode electrochemical data."""

    def __init__(self):
        self._cache: dict | None = None

    def _load_cache(self) -> dict:
        if self._cache is None:
            if CACHE_FILE.exists():
                self._cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            else:
                logger.warning(f"Electrode data cache not found at {CACHE_FILE}.")
                self._cache = {}
        return self._cache

    def process(self, record: MaterialRecord) -> MaterialRecord:
        """Enrich MaterialRecord with cell-level electrochemistry if a cached entry exists."""
        entry = self._load_cache().get(record.material_id)
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
            logger.info(
                f"Attached electrochemistry to {record.formula}: "
                f"V_OCV={record.average_voltage:.3f} V, specific capacity={record.capacity_grav:.1f} mAh/g"
            )
        return record
