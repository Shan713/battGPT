"""SMACT Chemical Processing Engine using genuine smact package calls."""
import logging
from smact import Element as SmactElement
from smact.screening import smact_validity
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

            # 3. SMACT validity: can the composition be charge-balanced with SMACT's allowed oxidation
            #    states, with electronegativity ordered sensibly (Pauling test)? This is SMACT's own
            #    screening function, independent of the oxidation states assigned to the sites. The
            #    previous version defaulted to "valid" whenever oxidation states were missing, which
            #    was every live-fetched material (K-Ont BUILD_LOG Step 24); unknown now stays None
            #    and nothing is written for it.
            if record.composition:
                comp = "".join(f"{el}{amt:g}" for el, amt in record.composition.items())
                record.smact_is_valid = bool(smact_validity(comp))
                record.smact_neutrality = record.smact_is_valid
            else:
                record.smact_is_valid = None
                record.smact_neutrality = None
            record.provenance_map["smact"] = "SMACT 4.0 Chemical Engine"
            record.processing_status["smact_success"] = True

        except Exception as e:
            logger.error(f"SMACT processing error for {record.material_id}: {e}")
            record.processing_status["smact_success"] = False
            record.processing_status["errors"].append(f"SMACT error: {e}")

        return record
