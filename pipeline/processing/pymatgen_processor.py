"""Pymatgen Structural Processing Engine with CrystalNN / VoronoiNN & Connectivity Extraction."""
import logging
from pymatgen.core import Structure, Lattice, Species
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.analysis.local_env import CrystalNN, VoronoiNN
from ..models import MaterialRecord, SiteData, BondData

logger = logging.getLogger(__name__)

GEOMETRY_LOOKUP = {
    2: "Linear",
    3: "Trigonal Planar",
    4: "Tetrahedral",
    5: "Square Pyramidal",
    6: "Octahedral",
    7: "Pentagonal Bipyramidal",
    8: "Square Antiprismatic",
    12: "Cuboctahedral"
}

class PymatgenProcessor:
    """Enriches MaterialRecord with Pymatgen structure, CrystalNN/VoronoiNN coordination, and connectivity graph."""

    def __init__(self):
        self.cnn = CrystalNN(weighted_cn=False, distance_cutoffs=None)
        self.vnn = VoronoiNN()

    def process(self, record: MaterialRecord) -> MaterialRecord:
        """Progressively enrich MaterialRecord with Pymatgen structural analysis and bonding graph."""
        try:
            struct = self._get_pymatgen_structure(record)
            if not struct:
                record.processing_status["pmg_success"] = False
                record.processing_status["errors"].append(f"Could not construct valid Pymatgen Structure for {record.material_id}")
                return record

            # 1. Spacegroup & Symmetry Analysis
            sga = SpacegroupAnalyzer(struct, symprec=0.1)
            sg_symbol = sga.get_space_group_symbol()
            sg_number = sga.get_space_group_number()
            cryst_sys = sga.get_crystal_system().capitalize()

            if sg_symbol:
                record.symmetry_symbol = sg_symbol
            if sg_number:
                record.spacegroup_number = sg_number
            if cryst_sys:
                record.crystal_system = cryst_sys

            record.provenance_map["symmetry"] = "Pymatgen (SpacegroupAnalyzer)"

            # 2. Refine Lattice Vectors
            record.lattice_a = round(float(struct.lattice.a), 4)
            record.lattice_b = round(float(struct.lattice.b), 4)
            record.lattice_c = round(float(struct.lattice.c), 4)
            record.alpha = round(float(struct.lattice.alpha), 2)
            record.beta = round(float(struct.lattice.beta), 2)
            record.gamma = round(float(struct.lattice.gamma), 2)
            record.provenance_map["lattice"] = "Pymatgen (Lattice)"

            # 3. Perform CrystalNN / VoronoiNN Connectivity Graph Analysis
            coord_method = "CrystalNN"
            for i, site_data in enumerate(record.sites):
                if i >= len(struct):
                    break

                bonds, cn = self._extract_site_neighbors(struct, i)
                site_data.neighbors = bonds
                site_data.coordination_number = cn
                site_data.coordination_geometry = GEOMETRY_LOOKUP.get(cn, f"Coordination-{cn}")
                site_data.provenance = f"Pymatgen ({coord_method})"

            # 3b. Symmetrize the bond graph into a proper undirected adjacency
            #     graph. CrystalNN decides neighbors independently per site, so
            #     borderline long-range contacts (e.g. 2.86-2.92 A Na-O in
            #     NASICON) can be detected from one site but not the other. A
            #     physical bond is mutual, so the distinct-partner edge set is
            #     symmetrized. Crucially, the per-site coordination number is NOT
            #     the graph degree: CrystalNN reports periodic-image neighbors, so
            #     several distinct neighbours can share the same site index. The
            #     coordination number is the sum of image multiplicities over the
            #     (symmetrized) partner set, which preserves the raw CrystalNN CN
            #     (e.g. Li = 3xO + 3xO = 6 in LiCoO2, Si = 4xSi = 4, C = 3x C = 3).
            from collections import Counter, defaultdict
            adj: dict[int, set[int]] = defaultdict(set)      # distinct-partner graph
            mult: dict[int, Counter] = defaultdict(Counter)  # image multiplicity per pair
            dist: dict[tuple[int, int], float] = {}          # shortest image distance per pair
            for i, site_data in enumerate(record.sites):
                for nb in site_data.neighbors:
                    j = int(nb.target_site_index)
                    if j == i or j >= len(record.sites):
                        continue
                    adj[i].add(j)
                    mult[i][j] += 1
                    cur = dist.get((i, j))
                    if cur is None or nb.distance_angstrom < cur:
                        dist[(i, j)] = nb.distance_angstrom
            # physical bond is mutual -> symmetrize the distinct-partner edge set
            for i in list(adj):
                for j in list(adj[i]):
                    adj[j].add(i)
            for i, site_data in enumerate(record.sites):
                nbrs = []
                cn = 0
                for j in sorted(adj.get(i, ())):
                    if j == i or j >= len(record.sites):
                        continue
                    # CN contribution: image multiplicity seen from this side;
                    # a partner added only by symmetrization counts once.
                    cn += mult[i].get(j, 1)
                    d = dist.get((i, j), dist.get((j, i)))
                    if d is None:
                        d = round(float(struct.get_distance(i, j)), 4)
                    else:
                        d = round(float(d), 4)
                    nbrs.append(BondData(
                        source_site_index=i,
                        target_site_index=j,
                        distance_angstrom=d,
                        coordination_method="CrystalNN",
                        target_element=record.sites[j].element_symbol,
                        target_species=record.sites[j].species_symbol or record.sites[j].element_symbol,
                    ))
                site_data.neighbors = nbrs
                site_data.coordination_number = cn
                site_data.coordination_geometry = GEOMETRY_LOOKUP.get(cn, f"Coordination-{cn}")

            record.coordination_method_used = coord_method
            record.provenance_map["coordination"] = f"Pymatgen ({coord_method})"
            record.processing_status["pmg_success"] = True

        except Exception as e:
            logger.error(f"Pymatgen processing error for {record.material_id}: {e}")
            record.processing_status["pmg_success"] = False
            record.processing_status["errors"].append(f"Pymatgen error: {e}")

        return record

    def _get_pymatgen_structure(self, record: MaterialRecord) -> Structure | None:
        """Load Pymatgen Structure directly from structure_dict or lattice/sites."""
        if record.structure_dict:
            try:
                return Structure.from_dict(record.structure_dict)
            except Exception as e:
                logger.debug(f"Structure.from_dict failed for {record.material_id}: {e}")

        if record.lattice_a > 0 and record.sites:
            lat = Lattice.from_parameters(
                record.lattice_a, record.lattice_b, record.lattice_c,
                record.alpha, record.beta, record.gamma
            )
            species_list = []
            coords_list = []
            for s in record.sites:
                coords_list.append([s.fractional_x, s.fractional_y, s.fractional_z])
                if s.oxidation_state is not None:
                    try:
                        species_list.append(Species(s.element_symbol, s.oxidation_state))
                    except Exception:
                        species_list.append(s.element_symbol)
                else:
                    species_list.append(s.element_symbol)
            return Structure(lat, species_list, coords_list)

        return None

    def _extract_site_neighbors(self, struct: Structure, site_idx: int) -> tuple[list[BondData], int]:
        """Extract nearest neighbor bonds and coordination number using CrystalNN with VoronoiNN fallback."""
        bonds: list[BondData] = []
        method = "CrystalNN"

        # Try CrystalNN first
        try:
            nn_info = self.cnn.get_nn_info(struct, site_idx)
            for nn in nn_info:
                target_idx = nn["site_index"]
                if target_idx == site_idx:
                    continue  # guard against self-loop neighbors
                target_site = struct[target_idx]
                dist = float(struct.get_distance(site_idx, target_idx))
                target_elem = target_site.specie.symbol
                target_sp = getattr(target_site.specie, 'symbol', target_elem)

                bonds.append(BondData(
                    source_site_index=site_idx,
                    target_site_index=target_idx,
                    distance_angstrom=round(dist, 4),
                    coordination_method="CrystalNN",
                    target_element=target_elem,
                    target_species=target_sp
                ))
            return bonds, len(bonds)
        except Exception as e:
            logger.debug(f"CrystalNN failed for site {site_idx}: {e}. Trying VoronoiNN.")

        # Fallback to VoronoiNN
        method = "VoronoiNN"
        try:
            nn_info = self.vnn.get_nn_info(struct, site_idx)
            for nn in nn_info:
                target_idx = nn["site_index"]
                if target_idx == site_idx:
                    continue  # guard against self-loop neighbors
                target_site = struct[target_idx]
                dist = float(struct.get_distance(site_idx, target_idx))
                target_elem = target_site.specie.symbol
                target_sp = getattr(target_site.specie, 'symbol', target_elem)

                bonds.append(BondData(
                    source_site_index=site_idx,
                    target_site_index=target_idx,
                    distance_angstrom=round(dist, 4),
                    coordination_method="VoronoiNN",
                    target_element=target_elem,
                    target_species=target_sp
                ))
            return bonds, len(bonds)
        except Exception as e:
            logger.debug(f"VoronoiNN failed for site {site_idx}: {e}. Using distance cutoff fallback.")

        # Fallback distance cutoff (~3.0 Å)
        method = "DistanceCutoff"
        try:
            neighbors = struct.get_neighbors(struct[site_idx], r=3.0)
            for nn in neighbors:
                target_idx = struct.index(nn)
                dist = float(struct.get_distance(site_idx, target_idx))
                target_elem = nn.specie.symbol
                target_sp = getattr(nn.specie, 'symbol', target_elem)
                bonds.append(BondData(
                    source_site_index=site_idx,
                    target_site_index=target_idx,
                    distance_angstrom=round(dist, 4),
                    coordination_method="DistanceCutoff",
                    target_element=target_elem,
                    target_species=target_sp
                ))
            return bonds, len(bonds)
        except Exception:
            return [], 6
