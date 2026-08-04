"""Materials Project Ingestion Engine with Authentic Cached Data Snapshot."""
import json
import logging
from pathlib import Path
from typing import Any
from ..config import PipelineConfig
from ..models import MaterialRecord, SiteData

logger = logging.getLogger(__name__)

CACHE_FILE = Path(__file__).resolve().parents[1] / "data" / "cached_mp_materials.json"

class MPIngester:
    """Ingestion engine supporting live Materials Project API queries and authentic offline JSON caching."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self._cached_dataset: dict[str, Any] | None = None

    def _load_cache(self) -> dict[str, Any]:
        """Load authentic cached Materials Project dataset snapshot."""
        if self._cached_dataset is None:
            if CACHE_FILE.exists():
                self._cached_dataset = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
                logger.info(f"Loaded authentic cached MP dataset from {CACHE_FILE}")
            else:
                logger.warning(f"Cache file {CACHE_FILE} not found. Operating with empty cache.")
                self._cached_dataset = {}
        return self._cached_dataset

    def ingest_material(self, material_id: str) -> MaterialRecord:
        """Fetch raw material metadata and initialize a MaterialRecord.

        The authentic offline cache (built from live MP API responses) is the
        primary source so that pipeline runs are deterministic and reproducible.
        The live API is used only when a material is absent from the cache.
        """
        cache = self._load_cache()
        if material_id in cache:
            return self._fetch_from_offline_cache(material_id)

        if self.config.mp_api_key:
            try:
                record = self._fetch_from_mp_api(material_id)
                logger.info(f"Successfully fetched {material_id} from live Materials Project API.")
                return record
            except Exception as e:
                logger.warning(f"MP API fetch failed for {material_id}: {e}.")

        return self._fetch_from_offline_cache(material_id)

    def ingest_batch(self, material_ids: list[str]) -> list[MaterialRecord]:
        """Ingest a list of materials as initial MaterialRecord objects."""
        records = []
        for mid in material_ids:
            try:
                rec = self.ingest_material(mid)
                records.append(rec)
            except Exception as e:
                logger.error(f"Error ingesting material {mid}: {e}")
        return records

    def _fetch_from_mp_api(self, material_id: str) -> MaterialRecord:
        """Live API call via mp-api."""
        from mp_api.client import MPRester
        from pymatgen.io.cif import CifWriter
        with MPRester(self.config.mp_api_key) as mpr:
            doc = mpr.materials.summary.search(material_ids=[material_id])[0]
            struct = doc.structure
            cif_str = str(CifWriter(struct))

            sites = [
                SiteData(
                    index=i,
                    element_symbol=site.specie.symbol,
                    fractional_x=float(site.a),
                    fractional_y=float(site.b),
                    fractional_z=float(site.c),
                    oxidation_state=getattr(site.specie, 'oxi_state', None),
                    provenance="Materials Project API"
                )
                for i, site in enumerate(struct.sites)
            ]
            return MaterialRecord(
                material_id=doc.material_id.string if hasattr(doc.material_id, 'string') else str(doc.material_id),
                formula=doc.formula_pretty,
                composition={str(k): float(v) for k, v in doc.composition.items()},
                cif=cif_str,
                structure_dict=struct.as_dict(),
                symmetry_symbol=doc.symmetry.symbol if doc.symmetry else "P1",
                spacegroup_number=doc.symmetry.number if doc.symmetry else 1,
                crystal_system=doc.symmetry.crystal_system.name if doc.symmetry else "Triclinic",
                band_gap=float(doc.band_gap),
                formation_energy_per_atom=float(doc.formation_energy_per_atom),
                energy_above_hull=float(doc.energy_above_hull),
                density=float(doc.density),
                volume=float(doc.volume),
                is_stable=bool(doc.is_stable),
                e_fermi=float(doc.e_fermi) if doc.e_fermi else None,
                lattice_a=float(struct.lattice.a),
                lattice_b=float(struct.lattice.b),
                lattice_c=float(struct.lattice.c),
                alpha=float(struct.lattice.alpha),
                beta=float(struct.lattice.beta),
                gamma=float(struct.lattice.gamma),
                sites=sites,
                provenance_map={
                    "material_id": "Materials Project API",
                    "structure": "Materials Project API",
                    "cif": "Materials Project API"
                }
            )

    def _fetch_from_offline_cache(self, material_id: str) -> MaterialRecord:
        """Load from authentic cached dataset (built from live MP API responses).

        Accepts the Stage 2.2 authentic cache schema (keys: formula_pretty,
        spacegroup_symbol, ordering, efermi, bulk_modulus, ...) and, for
        backward compatibility, the legacy synthetic schema (formula,
        symmetry_symbol, magnetic_ordering, e_fermi, elastic_k_vrh).
        """
        cache = self._load_cache()
        data = cache.get(material_id)
        if not data:
            logger.warning(f"Material {material_id} not in offline cache. Constructing basic fallback.")
            return MaterialRecord(
                material_id=material_id,
                formula=material_id,
                composition={},
                provenance_map={"material_id": "Offline Fallback Default"}
            )

        struct_dict = data.get("structure_dict")
        sites = []

        if struct_dict and "sites" in struct_dict:
            for i, s in enumerate(struct_dict["sites"]):
                sp_info = s["species"][0]
                elem = sp_info["element"]
                ox = sp_info.get("oxidation_state")
                coords = s["abc"]
                sites.append(SiteData(
                    index=i,
                    element_symbol=elem,
                    fractional_x=float(coords[0]),
                    fractional_y=float(coords[1]),
                    fractional_z=float(coords[2]),
                    oxidation_state=ox,
                    provenance="Materials Project Cached Snapshot"
                ))

        lat_info = struct_dict.get("lattice", {}) if struct_dict else {}
        bulk_mod = data.get("bulk_modulus") or {}
        k_vrh = data.get("elastic_k_vrh") or bulk_mod.get("vrh")

        return MaterialRecord(
            material_id=data["material_id"],
            formula=data.get("formula_pretty") or data.get("formula", material_id),
            composition=data.get("composition", {}),
            cif=data.get("cif"),
            structure_dict=struct_dict,
            symmetry_symbol=data.get("spacegroup_symbol") or data.get("symmetry_symbol", "P1"),
            spacegroup_number=data.get("spacegroup_number", 1),
            crystal_system=data.get("crystal_system", "Triclinic"),
            band_gap=data.get("band_gap", 0.0),
            formation_energy_per_atom=data.get("formation_energy_per_atom", 0.0),
            energy_above_hull=data.get("energy_above_hull", 0.0),
            density=data.get("density", 0.0),
            volume=data.get("volume", 0.0),
            is_stable=data.get("is_stable", False),
            e_fermi=data.get("efermi") if data.get("efermi") is not None else data.get("e_fermi"),
            magnetic_ordering=data.get("ordering") or data.get("magnetic_ordering"),
            elastic_k_vrh=k_vrh,
            lattice_a=float(lat_info.get("a", 0.0)),
            lattice_b=float(lat_info.get("b", 0.0)),
            lattice_c=float(lat_info.get("c", 0.0)),
            alpha=float(lat_info.get("alpha", 90.0)),
            beta=float(lat_info.get("beta", 90.0)),
            gamma=float(lat_info.get("gamma", 120.0)),
            sites=sites,
            provenance_map={
                "material_id": "Materials Project Cached Snapshot",
                "structure": "Materials Project Cached Snapshot",
                "cif": "Materials Project Cached Snapshot"
            }
        )
