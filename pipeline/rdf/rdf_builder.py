"""Master RDF Graph Builder."""
import logging
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal, RDFS, RDF, OWL, XSD
from ..models import MaterialRecord
from .triple_generator import TripleGenerator

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
SCHEMA_FILE = ROOT_DIR / "BattGpt-Ontology" / "battgpt.ttl"

class RDFBuilder:
    """Master RDF Graph Construction Manager binding Stage 1 namespaces and generating triples."""

    def __init__(self):
        self.graph = Graph()
        self._bind_namespaces()
        self.generator = TripleGenerator()

    def _bind_namespaces(self):
        """Bind all Stage 1 namespace prefixes into the RDF Graph."""
        self.graph.bind("emmo", Namespace("https://w3id.org/emmo#"))
        self.graph.bind("chsub", Namespace("https://w3id.org/emmo/domain/chemical-substance#"))
        self.graph.bind("battery", Namespace("https://w3id.org/emmo/domain/battery#"))
        self.graph.bind("cryst", Namespace("https://w3id.org/emmo/domain/crystallography#"))
        self.graph.bind("battinfo", Namespace("https://w3id.org/battinfo#"))
        self.graph.bind("battgpt", Namespace("https://w3id.org/battgpt/kg#"))
        self.graph.bind("unit", Namespace("http://qudt.org/vocab/unit/"))
        self.graph.bind("prov", Namespace("http://www.w3.org/ns/prov#"))
        self.graph.bind("dcterms", Namespace("http://purl.org/dc/terms/"))
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("rdf", RDF)
        self.graph.bind("owl", OWL)
        self.graph.bind("xsd", XSD)

    def _add_ontology_header_and_schema(self):
        """Merge the ontology header, owl:imports, and predicate/class declarations directly from
        BattGpt-Ontology/battgpt.ttl, so the exported KG always reflects whatever version of
        the ontology that file actually holds (version IRI, imports, and all) instead of a
        hand-duplicated copy that can silently drift out of sync with it."""
        if not SCHEMA_FILE.exists():
            raise FileNotFoundError(
                f"Ontology schema file not found at {SCHEMA_FILE}. The exported KG would be built "
                f"against an undeclared, unversioned battgpt: vocabulary without it."
            )
        schema_g = Graph()
        schema_g.parse(str(SCHEMA_FILE), format="turtle")
        for triple in schema_g:
            self.graph.add(triple)

        # Merge local EMMO 1.0.3 inferred ontology closure for complete hierarchy and UUID triples
        cache_dir = Path(__file__).resolve().parent / "ontology_cache"
        emmo_cache = cache_dir / "emmo_1.0.3_inferred.ttl"
        if emmo_cache.exists():
            logger.info(f"Loading local EMMO ontology closure from {emmo_cache}...")
            emmo_g = Graph()
            emmo_g.parse(str(emmo_cache), format="turtle")
            for triple in emmo_g:
                self.graph.add(triple)
            logger.info(f"Merged EMMO ontology closure ({len(emmo_g):,} triples). Total graph triples now: {len(self.graph):,}")

    def build_graph(self, records: list[MaterialRecord]) -> Graph:
        """Construct knowledge graph from a list of enriched MaterialRecords."""
        logger.info(f"Building RDF Knowledge Graph for {len(records)} material records...")
        self._add_ontology_header_and_schema()
        for idx, rec in enumerate(records):
            self.generator.generate_triples(rec, self.graph)
            if (idx + 1) % 1000 == 0 or (idx + 1) == len(records):
                logger.info(f"Generated RDF triples for {idx + 1}/{len(records)} material records. Current graph triples: {len(self.graph):,}")
        logger.info(f"RDF Graph construction complete. Total triples: {len(self.graph):,}")
        return self.graph
