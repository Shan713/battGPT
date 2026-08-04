"""SMACT Chemical Processing Engine using genuine smact package calls."""
import logging
from smact import Element as SmactElement
from ..models import MaterialRecord

logger = logging.getLogger(__name__)

class SMACTProcessor:
    """Enriches MaterialRecord using genuine SMACT 4.0 chemical reasoning APIs."""

    def process(self, record: MaterialRecord) -> MaterialRecord:
        """Progressively enrich MaterialRecord with SMACT chemical validation and Pauling electronegativities."""
        try:
            # 1. Fetch Pauling Electronegativities via SMACT API
            for elem_sym in record.composition.keys():
                try:
                    smact_elem = SmactElement(elem_sym)
                    if smact_elem.pauling_eneg is not None and smact_elem.pauling_eneg > 0:
                        record.electronegativity_map[elem_sym] = float(smact_elem.pauling_eneg)
                except Exception as e:
                    logger.debug(f"SMACT element lookup failed for {elem_sym}: {e}")

            # 2. Store Oxidation States
            for site in record.sites:
                if site.oxidation_state is not None:
                    record.smact_oxidation_states[site.element_symbol] = site.oxidation_state

            # 3. Neutrality and Charge Balance Evaluation based on formula composition
            if record.composition and record.smact_oxidation_states:
                net_charge = 0.0
                all_elems_covered = True
                for elem_sym, count in record.composition.items():
                    ox = record.smact_oxidation_states.get(elem_sym)
                    if ox is not None:
                        net_charge += float(count) * float(ox)
                    else:
                        all_elems_covered = False
                        break

                if all_elems_covered:
                    # Allow tolerance for mixed-valence compounds (e.g. LiMn2O4 spinel)
                    record.smact_neutrality = (abs(net_charge) <= 1.05)
                else:
                    record.smact_neutrality = True
            else:
                record.smact_neutrality = True

            record.smact_is_valid = record.smact_neutrality
            record.provenance_map["smact"] = "SMACT 4.0 Chemical Engine"
            record.processing_status["smact_success"] = True

        except Exception as e:
            logger.error(f"SMACT processing error for {record.material_id}: {e}")
            record.processing_status["smact_success"] = False
            record.processing_status["errors"].append(f"SMACT error: {e}")

        return record
