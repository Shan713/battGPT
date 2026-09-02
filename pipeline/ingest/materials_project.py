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
                logger.info(f"Loaded authentic cached MP dataset with {len(self._cached_dataset)} materials from {CACHE_FILE}")
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

    def ingest_all_cached(self) -> list[MaterialRecord]:
        """Ingest all materials present in the authentic cache snapshot."""
        cache = self._load_cache()
        return self.ingest_batch(list(cache.keys()))

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

            # Parse elastic moduli
            k_vrh = None
            if hasattr(doc, "bulk_modulus") and doc.bulk_modulus is not None:
                if isinstance(doc.bulk_modulus, dict):
                    k_vrh = doc.bulk_modulus.get("vrh")
                elif isinstance(doc.bulk_modulus, (int, float)):
                    k_vrh = float(doc.bulk_modulus)

            g_vrh = None
            if hasattr(doc, "shear_modulus") and doc.shear_modulus is not None:
                if isinstance(doc.shear_modulus, dict):
                    g_vrh = doc.shear_modulus.get("vrh")
                elif isinstance(doc.shear_modulus, (int, float)):
                    g_vrh = float(doc.shear_modulus)

            poisson = getattr(doc, "homogeneous_poisson", getattr(doc, "poisson_ratio", None))

            return MaterialRecord(
                material_id=doc.material_id.string if hasattr(doc.material_id, 'string') else str(doc.material_id),
                formula=doc.formula_pretty,
                composition={str(k): float(v) for k, v in doc.composition.items()},
                cif=cif_str,
                structure_dict=struct.as_dict(),
                symmetry_symbol=doc.symmetry.symbol if doc.symmetry else "P1",
                spacegroup_number=doc.symmetry.number if doc.symmetry else 1,
                crystal_system=doc.symmetry.crystal_system.name if doc.symmetry else "Triclinic",
                band_gap=float(doc.band_gap) if doc.band_gap is not None else 0.0,
                formation_energy_per_atom=float(doc.formation_energy_per_atom) if doc.formation_energy_per_atom is not None else 0.0,
                energy_above_hull=float(doc.energy_above_hull) if doc.energy_above_hull is not None else 0.0,
                density=float(doc.density) if doc.density is not None else 0.0,
                volume=float(doc.volume) if doc.volume is not None else 0.0,
                is_stable=bool(doc.is_stable) if doc.is_stable is not None else False,
                e_fermi=float(doc.efermi) if getattr(doc, "efermi", None) is not None else getattr(doc, "e_fermi", None),
                magnetic_ordering=str(doc.ordering) if getattr(doc, "ordering", None) else None,
                total_magnetization=float(doc.total_magnetization) if getattr(doc, "total_magnetization", None) is not None else None,
                is_metal=bool(doc.is_metal) if getattr(doc, "is_metal", None) is not None else None,
                is_gap_direct=bool(doc.is_gap_direct) if getattr(doc, "is_gap_direct", None) is not None else None,
                elastic_k_vrh=float(k_vrh) if k_vrh is not None else None,
                elastic_g_vrh=float(g_vrh) if g_vrh is not None else None,
                universal_anisotropy=float(doc.universal_anisotropy) if getattr(doc, "universal_anisotropy", None) is not None else None,
                poisson_ratio=float(poisson) if poisson is not None else None,
                num_sites=int(doc.nsites) if getattr(doc, "nsites", None) is not None else len(struct),
                chemsys=str(doc.chemsys) if getattr(doc, "chemsys", None) else "",
                point_group=str(getattr(doc.symmetry, "point_group", "")) if doc.symmetry else "",
                is_theoretical=bool(doc.theoretical) if getattr(doc, "theoretical", None) is not None else None,
                task_ids=[str(t) for t in doc.task_ids] if getattr(doc, "task_ids", None) else [str(doc.material_id)],
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
        """Load from authentic cached dataset snapshot."""
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
        bulk_mod = data.get("bulk_modulus")
        if isinstance(bulk_mod, dict):
            bulk_mod = bulk_mod.get("vrh")
        shear_mod = data.get("shear_modulus")
        if isinstance(shear_mod, dict):
            shear_mod = shear_mod.get("vrh")

        k_vrh = bulk_mod if bulk_mod is not None else data.get("elastic_k_vrh")
        g_vrh = shear_mod if shear_mod is not None else data.get("elastic_g_vrh")

        return MaterialRecord(
            material_id=data["material_id"],
            formula=data.get("formula_pretty") or data.get("formula", material_id),
            composition=data.get("composition", {}),
            cif=data.get("cif"),
            structure_dict=struct_dict,
            symmetry_symbol=data.get("spacegroup_symbol") or data.get("symmetry_symbol", "P1"),
            spacegroup_number=data.get("spacegroup_number", 1),
            crystal_system=data.get("crystal_system", "Triclinic"),
            band_gap=float(data.get("band_gap", 0.0)),
            formation_energy_per_atom=float(data.get("formation_energy_per_atom", 0.0)),
            energy_above_hull=float(data.get("energy_above_hull", 0.0)),
            density=float(data.get("density", 0.0)),
            volume=float(data.get("volume", 0.0)),
            energy_per_atom=float(data["energy_per_atom"]) if data.get("energy_per_atom") is not None else None,
            density_atomic=float(data["density_atomic"]) if data.get("density_atomic") is not None else None,
            is_stable=bool(data.get("is_stable", False)),
            e_fermi=float(data["efermi"]) if data.get("efermi") is not None else (float(data["e_fermi"]) if data.get("e_fermi") is not None else None),
            magnetic_ordering=data.get("ordering") or data.get("magnetic_ordering"),
            total_magnetization=float(data["total_magnetization"]) if data.get("total_magnetization") is not None else None,
            total_magnetization_normalized_formula_units=float(data["total_magnetization_normalized_formula_units"]) if data.get("total_magnetization_normalized_formula_units") is not None else None,
            total_magnetization_normalized_vol=float(data["total_magnetization_normalized_vol"]) if data.get("total_magnetization_normalized_vol") is not None else None,
            is_metal=bool(data["is_metal"]) if data.get("is_metal") is not None else None,
            is_gap_direct=bool(data["is_gap_direct"]) if data.get("is_gap_direct") is not None else None,
            elastic_k_vrh=float(k_vrh) if k_vrh is not None else None,
            elastic_g_vrh=float(g_vrh) if g_vrh is not None else None,
            universal_anisotropy=float(data["universal_anisotropy"]) if data.get("universal_anisotropy") is not None else None,
            poisson_ratio=float(data["poisson_ratio"]) if data.get("poisson_ratio") is not None else None,
            num_sites=int(data["num_sites"]) if data.get("num_sites") is not None else len(sites),
            nelements=int(data["nelements"]) if data.get("nelements") is not None else None,
            num_magnetic_sites=int(data["num_magnetic_sites"]) if data.get("num_magnetic_sites") is not None else None,
            num_unique_magnetic_sites=int(data["num_unique_magnetic_sites"]) if data.get("num_unique_magnetic_sites") is not None else None,
            chemsys=data.get("chemsys", ""),
            point_group=data.get("point_group", ""),
            is_theoretical=bool(data["is_theoretical"]) if data.get("is_theoretical") is not None else None,
            task_ids=data.get("task_ids", [data["material_id"]]),
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
