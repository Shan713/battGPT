"""Builds a larger battery-materials KG (against the current BattGpt-Ontology, v0.3.2) for the
OnT ABox-extension work in K-Ont/. Extends scripts/build_kg.py's ~22 hand-curated materials with
materials found via targeted Materials Project searches (pipeline/ingest/candidate_search.py),
classified into the ontology's StructureFamily taxonomy by the heuristic tier added to
pipeline/processing/structure_family_mapper.py.

See K-Ont/docs/BUILD_LOG.md for why this exists and how each design choice was made.

Usage:
    python scripts/populate_kg_ont.py --dry-run          # search + classify only, no ingestion
    python scripts/populate_kg_ont.py                    # full run, default cap 250 materials
    python scripts/populate_kg_ont.py --cap 150          # smaller run
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.config import PipelineConfig
from pipeline.ingest import MPIngester
from pipeline.ingest.candidate_search import (
    sweep_candidates, pick_representative_polymorph, sweep_broad_pool, pick_polymorph_group,
)
from pipeline.processing import (
    PymatgenProcessor, SMACTProcessor, BattINFOMapper, StructureFamilyMapper, ElectrochemistryProcessor,
)
from pipeline.rdf import RDFBuilder, RDFValidator
from pipeline.export import RDFExporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CANDIDATES_CACHE = PROJECT_ROOT / "K-Ont" / "data" / "candidate_materials.json"


def build_candidate_list(config: PipelineConfig, cap: int, use_cache: bool) -> tuple[list[str], dict]:
    """Search Materials Project for candidate materials, classify them locally, and return a
    capped, prioritized list of material_ids plus a summary dict for documentation.

    Priority when capping (highest first):
      1. The existing hand-curated + cathode-test materials (always included, exact ids kept --
         we never want to accidentally swap a verified id for a different polymorph of the same
         formula found by the sweep).
      2. New materials the heuristic classifier actually assigned a StructureFamily to -- these
         are the ones that add real type-diversity for OnT's type rows.
      3. Everything else, ordered by lowest energy_above_hull (closer to the hull = more
         physically reasonable / more likely synthesizable), up to the cap.
    """
    from mp_api.client import MPRester

    curated_ids = list(dict.fromkeys(config.sample_materials + config.cathode_test_materials))
    # Formulas we already have a hand-verified entry for. A sweep search has no way to know which
    # specific polymorph a human already checked against MP by hand, so it can (and did, in
    # testing -- see BUILD_LOG.md) come back with a *different* id for the *same* formula, which
    # would silently duplicate that material in the KG under two different mp- URIs. We keep the
    # curated id and drop the sweep's version whenever the formula is already covered.
    cache_file = Path(__file__).resolve().parents[1] / "pipeline" / "data" / "cached_mp_materials.json"
    curated_formulas = set()
    if cache_file.exists():
        for entry in json.loads(cache_file.read_text()).values():
            f = entry.get("formula_pretty") or entry.get("formula")
            if f:
                curated_formulas.add(f)

    if use_cache and CANDIDATES_CACHE.exists():
        logger.info(f"Loading cached candidate search from {CANDIDATES_CACHE}")
        reps = json.loads(CANDIDATES_CACHE.read_text())
    else:
        with MPRester(config.mp_api_key, mute_progress_bars=True) as mpr:
            by_formula = sweep_candidates(mpr)
            reps = {}
            for formula, docs in by_formula.items():
                d, why = pick_representative_polymorph(docs)
                reps[formula] = {
                    "material_id": str(d.material_id), "n_polymorphs": len(docs),
                    "polymorph_choice_reason": why, "energy_above_hull": d.energy_above_hull,
                }
            # classify each representative so we can prioritize classified ones when capping
            ids = [v["material_id"] for v in reps.values()]
            docs2 = []
            for i in range(0, len(ids), 50):
                docs2.extend(mpr.materials.summary.search(
                    material_ids=ids[i:i + 50],
                    fields=["material_id", "formula_pretty", "composition", "symmetry"],
                    num_chunks=1, chunk_size=50,
                ))
        from pipeline.models import MaterialRecord
        mapper = StructureFamilyMapper()
        by_id = {str(d.material_id): d for d in docs2}
        for formula, entry in reps.items():
            d = by_id.get(entry["material_id"])
            if not d:
                continue
            rec = MaterialRecord(material_id=str(d.material_id), formula=d.formula_pretty,
                                  composition={str(k): float(v) for k, v in d.composition.items()})
            rec.spacegroup_number = d.symmetry.number
            mapper.process(rec)
            entry["structure_family_preview"] = rec.structure_family
        CANDIDATES_CACHE.parent.mkdir(parents=True, exist_ok=True)
        CANDIDATES_CACHE.write_text(json.dumps(reps, indent=2))
        logger.info(f"Saved candidate search results to {CANDIDATES_CACHE}")

    # Drop any sweep candidate whose formula is already covered by a curated entry (see above),
    # then split the rest into classified / unclassified for priority ordering.
    reps = {f: e for f, e in reps.items() if f not in curated_formulas}
    classified = [(f, e) for f, e in reps.items() if e.get("structure_family_preview")]
    unclassified = [(f, e) for f, e in reps.items() if not e.get("structure_family_preview")]
    unclassified.sort(key=lambda fe: fe[1].get("energy_above_hull", 1e9))

    final_ids = list(curated_ids)
    seen = set(final_ids)
    added_classified, added_other = 0, 0
    for f, e in classified:
        if len(final_ids) >= cap:
            break
        if e["material_id"] not in seen:
            final_ids.append(e["material_id"]); seen.add(e["material_id"]); added_classified += 1
    for f, e in unclassified:
        if len(final_ids) >= cap:
            break
        if e["material_id"] not in seen:
            final_ids.append(e["material_id"]); seen.add(e["material_id"]); added_other += 1

    summary = {
        "curated_count": len(curated_ids),
        "candidates_found": len(reps),
        "candidates_classified": len(classified),
        "added_classified": added_classified,
        "added_unclassified": added_other,
        "final_total": len(final_ids),
        "cap": cap,
    }
    return final_ids, summary


def build_grown_candidate_list(config: PipelineConfig, cap: int, cache_path: Path, use_cache: bool,
                               polymorph_share: float, max_polymorphs: int, polymorph_window: float):
    """--grow mode (K-Ont BUILD_LOG Step 22): candidates from the ratio sweeps AND the broad Li/Na pool,
    one representative per formula as before, plus polymorph groups so some formulas appear with
    several crystal structures.

    Fill order up to `cap`: curated ids -> every representative the classifier gives a structure
    family -> polymorph groups (representative + extras) until `polymorph_share * cap` materials sit
    in such groups -> remaining representatives by energy above hull. Deterministic for a given
    cache. The original build_candidate_list() path is untouched.
    """
    from pipeline.models import MaterialRecord

    curated_ids = list(dict.fromkeys(config.sample_materials + config.cathode_test_materials))
    cache_file = Path(__file__).resolve().parents[1] / "pipeline" / "data" / "cached_mp_materials.json"
    curated_formulas = set()
    if cache_file.exists():
        for entry in json.loads(cache_file.read_text()).values():
            f = entry.get("formula_pretty") or entry.get("formula")
            if f:
                curated_formulas.add(f)

    if use_cache and cache_path.exists():
        logger.info(f"Loading cached grown candidate search from {cache_path}")
        reps = json.loads(cache_path.read_text())
    else:
        from mp_api.client import MPRester
        mapper = StructureFamilyMapper()
        with MPRester(config.mp_api_key, mute_progress_bars=True) as mpr:
            merged = {}
            for by_formula in (sweep_candidates(mpr), sweep_broad_pool(mpr)):
                for formula, docs in by_formula.items():
                    slot = merged.setdefault(formula, {})
                    for d in docs:
                        slot[str(d.material_id)] = d
            reps, docs_by_formula, need_sym = {}, {}, []
            for formula, by_id in merged.items():
                docs = list(by_id.values())
                d, why = pick_representative_polymorph(docs)
                if d is None:
                    continue
                extras = pick_polymorph_group(docs, str(d.material_id), max_polymorphs, polymorph_window)
                reps[formula] = {
                    "material_id": str(d.material_id), "n_polymorphs": len(docs),
                    "polymorph_choice_reason": why, "energy_above_hull": d.energy_above_hull,
                    "polymorph_extras": [{"material_id": str(x.material_id), "energy_above_hull": x.energy_above_hull}
                                         for x in extras],
                }
                docs_by_formula[formula] = d
                if getattr(d, "symmetry", None) is None:
                    need_sym.append(str(d.material_id))
            # ratio-sweep docs carry no "symmetry"; fetch it only for representatives that lack it
            sym = {}
            for i in range(0, len(need_sym), 50):
                for dd in mpr.materials.summary.search(material_ids=need_sym[i:i + 50],
                                                       fields=["material_id", "symmetry"],
                                                       num_chunks=1, chunk_size=50):
                    sym[str(dd.material_id)] = dd.symmetry.number
        for formula, entry in reps.items():
            d = docs_by_formula[formula]
            sg = sym.get(entry["material_id"]) or (d.symmetry.number if getattr(d, "symmetry", None) else None)
            rec = MaterialRecord(material_id=entry["material_id"], formula=d.formula_pretty,
                                 composition={str(k): float(v) for k, v in d.composition.items()})
            rec.spacegroup_number = sg
            mapper.process(rec)
            entry["structure_family_preview"] = rec.structure_family
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(reps, indent=2))
        logger.info(f"Saved grown candidate search ({len(reps)} formulas) to {cache_path}")

    reps = {f: e for f, e in reps.items() if f not in curated_formulas}

    def by_ehull(fe):
        eh = fe[1].get("energy_above_hull")
        return (eh if eh is not None else 1e9, fe[1]["material_id"])

    classified = sorted([(f, e) for f, e in reps.items() if e.get("structure_family_preview")], key=by_ehull)
    unclassified = sorted([(f, e) for f, e in reps.items() if not e.get("structure_family_preview")], key=by_ehull)

    final_ids = list(curated_ids)
    seen = set(final_ids)

    def add(mid):
        if len(final_ids) < cap and mid not in seen:
            final_ids.append(mid)
            seen.add(mid)
            return True
        return False

    n_classified = sum(add(e["material_id"]) for _, e in classified)
    # polymorph groups: classified formulas first (their structures matter most), then the rest
    budget = int(round(polymorph_share * cap))
    in_groups, groups = 0, []
    for f, e in classified + unclassified:
        if in_groups >= budget or len(final_ids) >= cap:
            break
        extras = [x["material_id"] for x in e.get("polymorph_extras", [])]
        if not extras:
            continue
        members = [e["material_id"]] + extras
        for m in members:
            add(m)
        kept = [m for m in members if m in seen]
        if len(kept) >= 2:
            groups.append({"formula": f, "material_ids": kept})
            in_groups += len(kept)
    n_rest = sum(add(e["material_id"]) for _, e in unclassified)

    summary = {
        "mode": "grow", "cap": cap, "curated_count": len(curated_ids),
        "candidate_formulas": len(reps), "candidates_classified": len(classified),
        "added_classified": n_classified, "polymorph_groups": len(groups),
        "materials_in_polymorph_groups": in_groups, "polymorph_share_target": polymorph_share,
        "added_other": n_rest, "final_total": len(final_ids),
    }
    return final_ids, summary, groups


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=250, help="Max total materials in the final KG.")
    ap.add_argument("--dry-run", action="store_true", help="Search + classify only, print summary, no ingestion.")
    ap.add_argument("--use-cache", action="store_true", help="Reuse a previous candidate search (K-Ont/data/candidate_materials.json) instead of hitting the API again.")
    ap.add_argument("--grow", action="store_true", help="K-Ont Step 22: broad Li/Na pool + polymorph groups (build_grown_candidate_list).")
    ap.add_argument("--out-dir", type=Path, default=None, help="Output folder (default output/battgpt_kg_ont, or output/battgpt_kg_grow_<cap> with --grow).")
    ap.add_argument("--cache", type=Path, default=None, help="--grow candidate cache (default K-Ont/data/candidate_materials_grow.json).")
    ap.add_argument("--polymorph-share", type=float, default=0.25, help="--grow: target fraction of the KG in polymorph groups.")
    ap.add_argument("--max-polymorphs", type=int, default=3, help="--grow: at most this many structures per formula.")
    ap.add_argument("--polymorph-window", type=float, default=0.05, help="--grow: extra polymorphs within this many eV/atom of the hull.")
    ap.add_argument("--ids-file", type=Path, default=None,
                    help="K-Ont Step 56: ingest exactly these material ids (JSON list), skipping candidate selection -- "
                         "lets a large KG be built in chunks that fit in memory. Requires --out-dir.")
    args = ap.parse_args()

    config = PipelineConfig()
    default_out = f"battgpt_kg_grow_{args.cap}" if args.grow else "battgpt_kg_ont"
    output_dir = args.out_dir or (PROJECT_ROOT / "output" / default_out)

    logger.info("Step 1: Searching + classifying candidate materials...")
    groups = []
    if args.ids_file:
        if not args.out_dir:
            ap.error("--ids-file requires --out-dir")
        material_ids = list(dict.fromkeys(json.loads(args.ids_file.read_text())))
        summary = {"mode": "ids-file", "ids_file": str(args.ids_file), "final_total": len(material_ids)}
    elif args.grow:
        cache_path = args.cache or (PROJECT_ROOT / "K-Ont" / "data" / "candidate_materials_grow.json")
        material_ids, summary, groups = build_grown_candidate_list(
            config, args.cap, cache_path, args.use_cache,
            args.polymorph_share, args.max_polymorphs, args.polymorph_window)
    else:
        material_ids, summary = build_candidate_list(config, args.cap, args.use_cache)
    logger.info(f"Candidate summary: {json.dumps(summary, indent=2)}")

    if args.dry_run:
        if groups:
            logger.info(f"Example polymorph groups: {json.dumps(groups[:5])}")
        logger.info(f"Dry run: would ingest {len(material_ids)} materials. Exiting without building the KG.")
        return
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "selected_material_ids.json").write_text(json.dumps(
        {"material_ids": material_ids, "polymorph_groups": groups, "summary": summary}, indent=2))

    logger.info(f"Step 2: Ingesting {len(material_ids)} materials (cache-first, live API fallback)...")
    ingester = MPIngester(config)
    pmg = PymatgenProcessor(); smact = SMACTProcessor(); mapper = BattINFOMapper()
    structure_family = StructureFamilyMapper()
    # Live MP insertion-electrode data for the selected materials (the cache alone covers 10).
    from mp_api.client import MPRester
    from pipeline.processing.electrochemistry_processor import fetch_insertion_electrode_index
    with MPRester(config.mp_api_key, mute_progress_bars=True) as mpr:
        electrode_index = fetch_insertion_electrode_index(mpr, material_ids)
    logger.info(f"Live insertion-electrode data found for {len(electrode_index)}/{len(material_ids)} materials.")
    electrochemistry = ElectrochemistryProcessor(live_index=electrode_index)

    def ingest_with_retry(mid):
        # MPIngester returns a placeholder record (formula = the id, no composition, no structure)
        # when the live fetch fails -- e.g. the ~7 min DNS outage that put 52 fake materials into the
        # first 5,000 build. Retry with backoff instead of writing that into the KG.
        for wait in (0, 30, 60, 120, 240):
            if wait:
                logger.warning(f"  {mid}: live fetch failed, retrying in {wait}s")
                time.sleep(wait)
            rec = ingester.ingest_material(mid)
            if rec.provenance_map.get("material_id") != "Offline Fallback Default":
                return rec
        raise RuntimeError("still a placeholder record after retries")

    records, failed = [], []
    t_start = time.time()
    for i, mid in enumerate(material_ids):
        try:
            rec = ingest_with_retry(mid)
            pmg.process(rec)
            smact.process(rec)
            mapper.process(rec)
            structure_family.process(rec)
            electrochemistry.process(rec)
            records.append(rec)
        except Exception as e:
            logger.error(f"  SKIPPED {mid}: {e}")
            failed.append(mid)
        if (i + 1) % 25 == 0:
            elapsed = time.time() - t_start
            rate = (i + 1) / elapsed
            eta = (len(material_ids) - i - 1) / rate if rate > 0 else float("nan")
            logger.info(f"  ...{i + 1}/{len(material_ids)} done ({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)")

    logger.info(f"Step 2 Complete: {len(records)}/{len(material_ids)} materials ingested successfully.")
    if failed:
        logger.error(f"{len(failed)} materials could not be ingested: {failed}. Not building a KG with gaps.")
        sys.exit(1)

    logger.info("Step 3: Constructing RDF Knowledge Graph...")
    builder = RDFBuilder()
    graph = builder.build_graph(records)
    logger.info(f"Step 3 Complete: {len(graph):,} triples.")

    logger.info("Step 4: Validating...")
    validator = RDFValidator()
    report = validator.validate(graph, records=records)
    logger.info(f"Validation: is_valid={report.is_valid}, errors={len(report.errors)}, warnings={len(report.warnings)}")
    for e in report.errors:
        logger.error(f"  VALIDATION ERROR: {e}")
    report.save_reports(output_dir)

    logger.info(f"Step 5: Exporting to {output_dir}...")
    exporter = RDFExporter()
    exported = exporter.export_all(graph, output_dir=output_dir)
    for fmt, path in exported.items():
        logger.info(f"  {fmt}: {path} ({path.stat().st_size:,} bytes)")

    # Write a plain-language summary alongside the KG for documentation.
    fam_counts: dict[str, int] = {}
    role_counts: dict[str, int] = {}
    for rec in records:
        if rec.structure_family:
            fam_counts[rec.structure_family] = fam_counts.get(rec.structure_family, 0) + 1
        if rec.battery_role:
            role_counts[rec.battery_role] = role_counts.get(rec.battery_role, 0) + 1
    run_summary = {
        "total_materials": len(records),
        "structure_family_counts": fam_counts,
        "battery_role_counts": role_counts,
        "unclassified_structure_family": len(records) - sum(fam_counts.values()),
        "no_battery_role": len(records) - sum(role_counts.values()),
        "candidate_search_summary": summary,
    }
    (output_dir / "population_summary.json").write_text(json.dumps(run_summary, indent=2))
    logger.info(f"Run summary: {json.dumps(run_summary, indent=2)}")


if __name__ == "__main__":
    main()
