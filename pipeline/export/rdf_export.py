"""Multi-format RDF Exporter."""
import logging
import math
from pathlib import Path
from rdflib import Graph, URIRef
from rdflib.term import Literal
from rdflib.plugins.serializers.turtle import TurtleSerializer

logger = logging.getLogger(__name__)

_XSD_DOUBLE = URIRef("http://www.w3.org/2001/XMLSchema#double")


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

        return paths
