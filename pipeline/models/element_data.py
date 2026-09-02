"""
Static Periodic Table Physical Properties Lookup Module (Stage 2.3.1).
Provides authentic physical elemental descriptors (atomic number, atomic mass, group, period,
electronegativity, covalent radius, valence electron count) for all periodic elements.
"""

from dataclasses import dataclass
from pymatgen.core import Element as PmgElement

@dataclass
class ElementPhysicalData:
    symbol: str
    atomic_number: int
    atomic_mass: float
    group: int
    period: int
    electronegativity: float
    covalent_radius: float
    valence_electrons: int

_ELEMENT_CACHE: dict[str, ElementPhysicalData] = {}

def get_element_physical_data(symbol: str) -> ElementPhysicalData:
    """Retrieve physical element data for a given chemical symbol using pymatgen Element."""
    if symbol in _ELEMENT_CACHE:
        return _ELEMENT_CACHE[symbol]

    try:
        el = PmgElement(symbol)
        z = int(el.Z)
        mass = float(el.atomic_mass)
        group = int(el.group) if el.group else 0
        period = int(el.row) if el.row else 0
        en = float(el.X) if el.X else 0.0
        
        # Radius lookup cascade: covalent_radius_pyykko -> atomic_radius -> atomic_radius_calculated
        r_cov = 0.0
        if hasattr(el, "covalent_radius_pyykko") and getattr(el, "covalent_radius_pyykko", None) is not None:
            r_cov = float(el.covalent_radius_pyykko)
        elif hasattr(el, "atomic_radius") and getattr(el, "atomic_radius", None) is not None:
            r_cov = float(el.atomic_radius)
        elif hasattr(el, "atomic_radius_calculated") and getattr(el, "atomic_radius_calculated", None) is not None:
            r_cov = float(el.atomic_radius_calculated)

        # Calculate valence electrons based on periodic table group
        if group <= 2:
            valence = group
        elif 13 <= group <= 18:
            valence = group - 10
        elif group > 0:
            valence = group  # Transition metals
        else:
            valence = 0

        data = ElementPhysicalData(
            symbol=symbol,
            atomic_number=z,
            atomic_mass=round(mass, 4),
            group=group,
            period=period,
            electronegativity=round(en, 2),
            covalent_radius=round(r_cov, 3),
            valence_electrons=valence
        )
    except Exception as exc:
        # Fallback for unknown or placeholder symbols
        data = ElementPhysicalData(
            symbol=symbol,
            atomic_number=0,
            atomic_mass=0.0,
            group=0,
            period=0,
            electronegativity=0.0,
            covalent_radius=0.0,
            valence_electrons=0
        )

    _ELEMENT_CACHE[symbol] = data
    return data
