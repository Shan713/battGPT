# Candidate Validation Report — `battgpt_candidate.ttl`

**Compared against:** the current, already-applied `battgpt.ttl` (989 triples — includes the previously-applied `hasRole`/`hasCharacteristicSpaceGroup`/`OxideStructureFamily` reparenting changes).
**Candidate contains:** current `battgpt.ttl` + the three "DEFINITELY ADD" restrictions from `semantic_enrichment_audit.md` Phase 8 (#1–3): `BatteryCell ⊑ ∃hasRole.PositiveElectrodeRole`, `∃hasRole.NegativeElectrodeRole`, `∃hasRole.ElectrolyteRole`. **`battgpt.ttl` itself has not been touched by this candidate pass.**

## Triple counts

| | Count |
|---|---|
| Before (current `battgpt.ttl`) | 989 |
| After (`battgpt_candidate.ttl`) | 1001 |
| Added | 12 (3 restrictions × 4 triples each: `rdf:type owl:Restriction`, `owl:onProperty`, `owl:someValuesFrom`, plus the `rdfs:subClassOf` link) |
| Removed | 0 |
| Changed axioms | 0 (purely additive — no existing triple was modified or removed) |

## RDFLib parse

Passed. `battgpt_candidate.ttl` parses cleanly as valid Turtle, 1001 triples, exactly matching the expected +12 delta.

## ROBOT + ELK (full merged closure via existing catalog)

**Passed with no new issues.** Result: exactly 1 unsatisfiable class — `emmo:CentiMetreSecondDegreeCelsius` — identical to the baseline (both the original pre-session file and the current already-applied `battgpt.ttl`). **Zero new unsatisfiable classes introduced by the 3 candidate restrictions.**

## ROBOT + HermiT (full merged closure)

**Not yet run for this specific candidate** — a HermiT confirmation pass for the previously-applied `battgpt.ttl` was already in progress (started before this candidate was built) and was still running at the time this report was written, to avoid contending for the same CPU with a second concurrent 40-minute HermiT run. The candidate's HermiT pass is queued to run immediately after. Based on: (a) the ELK result above, (b) the structurally identical pattern already HermiT-confirmed safe for the `∃hasRole.BatteryRole` restriction in the previous audit round (these 3 new restrictions use the exact same property, `emmo:hasRole`, just narrowed to more specific range classes — `PositiveElectrodeRole`/`NegativeElectrodeRole`/`ElectrolyteRole` are all subclasses of `BatteryRole`, so they're strictly *more specific*, not a new kind of axiom), there is strong reason to expect an identical "zero new unsatisfiable classes" result. This expectation will be confirmed, not assumed, before final sign-off.

## Inferred hierarchy / unexpected superclass check

Checked directly: adding `∃hasRole.PositiveElectrodeRole` (etc.) to `BatteryCell` does not and cannot make `BatteryCell` a subclass of `PositiveElectrodeRole` itself, or vice versa — an existential restriction only asserts a *relationship requirement*, not a subsumption between the restricted class and the filler class. `PositiveElectrodeRole`/`NegativeElectrodeRole`/`ElectrolyteRole` remain in their existing 4-way `owl:AllDisjointClasses` block, unaffected — that disjointness is between the four `BatteryRole` subclasses themselves, not between `BatteryCell` and any of them, so no conflict arises.

## Domain/range unintended-classification check

`emmo:hasRole`'s domain is `emmo:Whole`. All three new restrictions use the same property, so `BatteryCell ⊑ Whole` is entailed three times over (redundantly, harmlessly) rather than newly — this entailment was already established by the previously-applied generic `∃hasRole.BatteryRole` restriction. No new domain-driven classification appears.

## OWL 2 EL compatibility

All three candidate restrictions are `owl:someValuesFrom` on a named class — the core EL existential-restriction pattern. **All three are OWL 2 EL compatible.** No cardinality, no `allValuesFrom`, no property characteristics, no union/intersection were introduced.

## Summary

| Check | Result |
|---|---|
| RDFLib parse | ✅ Pass |
| ELK (full closure) | ✅ Pass — 0 new unsatisfiable classes |
| HermiT (full closure) | ⏳ Queued, pending — will be appended when complete |
| Unexpected superclass relationships | ✅ None found |
| Domain/range unintended classification | ✅ None beyond the already-established, harmless `Whole` entailment |
| OWL 2 EL compatibility | ✅ All 3 additions are EL-compatible |

**Recommendation: safe to apply, pending the final HermiT confirmation.**
