"""Multi-format RDF Exporter."""
import logging
import math
import os
from pathlib import Path
from rdflib import Graph, URIRef
from rdflib.term import Literal
from rdflib.plugins.serializers.turtle import TurtleSerializer

logger = logging.getLogger(__name__)

_XSD_DOUBLE = URIRef("http://www.w3.org/2001/XMLSchema#double")

# BattGpt-Ontology/imports/ holds local snapshots of every ontology battgpt.ttl imports. Each
# exported KG declares the same owl:imports (see RDFBuilder), so a catalog mapping those IRIs to
# these local files is written alongside it, letting Protege resolve them offline.
_IMPORTS_DIR = Path(__file__).resolve().parents[2] / "BattGpt-Ontology" / "imports"
_CATALOG_ENTRIES = [
    ("https://w3id.org/emmo", "emmo.ttl"),
    ("https://w3id.org/emmo/domain/battery", "battery.ttl"),
    ("https://w3id.org/emmo/domain/chemical-substance", "chemical-substance.ttl"),
    ("https://w3id.org/battinfo", "battinfo.ttl"),
    # battinfo.ttl itself nests an import of this specific versioned battery IRI.
    ("https://w3id.org/emmo/domain/battery/0.13.0-beta/battery", "battery.ttl"),
]


class _FullPrecisionTurtleSerializer(TurtleSerializer):
    """Turtle serializer that preserves full IEEE-754 double precision.

    Upstream rdflib's TurtleWriter formats ``xsd:double`` literals with
    ``f"{value:e}"`` (only ~6 significant digits; see the "Only limited
    precision available for floats" note in rdflib.term.Literal._literal_n3),
    silently rounding values such as 3.8734991245808144 down to 3.873499e+00.
    RDF/XML and JSON-LD writers keep the full float, so the three exports were
    not bit-identical.

    This override writes doubles in the quoted form ``"<full-precision
    lexical>"^^xsd:double``, which round-trips to the identical Literal term
    (full precision AND correct datatype). A bare numeric such as ``1.61``
    would re-parse as xsd:decimal under the Turtle grammar, and ``repr(v)``
    alone cannot express doubles faithfully, so both precision and datatype
    must be carried explicitly.
    """

    def label(self, node, position):
        if isinstance(node, Literal) and node.datatype == _XSD_DOUBLE and node.value is not None:
            value = float(node)
            if math.isfinite(value):
                return node._literal_n3(use_plain=False, qname_callback=lambda dt: self.get_pname(dt, True))
        return super().label(node, position)


class RDFExporter:
    """Exports rdflib Graph into Turtle (.ttl), RDF/XML (.rdf), and JSON-LD (.jsonld)."""

    def export_all(self, graph: Graph, output_dir: Path) -> dict[str, Path]:
        """Serialize graph to Turtle, RDF/XML, and JSON-LD formats."""
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {}

        # 1. Turtle (.ttl) — full-precision doubles via custom serializer
        ttl_path = output_dir / "battery_kg.ttl"
        with open(ttl_path, "wb") as stream:
            _FullPrecisionTurtleSerializer(graph).serialize(stream, encoding="utf-8", base=None)
        paths["turtle"] = ttl_path
        logger.info(f"Exported Turtle graph to {ttl_path}")

        # 2. RDF/XML (.rdf)
        xml_path = output_dir / "battery_kg.rdf"
        graph.serialize(destination=str(xml_path), format="xml")
        paths["xml"] = xml_path
        logger.info(f"Exported RDF/XML graph to {xml_path}")

        # 3. JSON-LD (.jsonld)
        jsonld_path = output_dir / "battery_kg.jsonld"
        graph.serialize(destination=str(jsonld_path), format="json-ld")
        paths["jsonld"] = jsonld_path
        logger.info(f"Exported JSON-LD graph to {jsonld_path}")

        self._write_catalog(output_dir)

        return paths

    def _write_catalog(self, output_dir: Path):
        """Write an OASIS XML catalog next to the exported KG mapping its owl:imports IRIs to the
        local BattGpt-Ontology/imports/ snapshots, so Protege resolves them offline."""
        if not _IMPORTS_DIR.exists():
            logger.warning(f"BattGpt-Ontology/imports/ not found at {_IMPORTS_DIR}; skipping catalog generation.")
            return

        rel_imports_dir = os.path.relpath(_IMPORTS_DIR, output_dir)
        lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            '<catalog prefer="public" xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">',
        ]
        for uri_name, filename in _CATALOG_ENTRIES:
            lines.append(f'    <uri name="{uri_name}" uri="{rel_imports_dir}/{filename}"/>')
        lines.append("</catalog>")

        catalog_path = output_dir / "catalog-v001.xml"
        catalog_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.info(f"Wrote offline import catalog to {catalog_path}")
