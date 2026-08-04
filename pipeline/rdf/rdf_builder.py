"""Master RDF Graph Builder."""
import logging
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal, RDFS, RDF, OWL, XSD
from ..models import MaterialRecord
from .triple_generator import TripleGenerator

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
SCHEMA_FILE = ROOT_DIR / "rdf_schema.ttl"

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
        self.graph.bind("elchem", Namespace("https://w3id.org/emmo/domain/electrochemistry#"))
        self.graph.bind("battery", Namespace("https://w3id.org/emmo/domain/battery#"))
        self.graph.bind("cryst", Namespace("https://w3id.org/emmo/domain/crystallography#"))
        self.graph.bind("battinfo", Namespace("https://w3id.org/battinfo#"))
        self.graph.bind("battgpt", Namespace("https://w3id.org/battgpt/kg#"))
        self.graph.bind("qudt", Namespace("http://qudt.org/schema/qudt/"))
        self.graph.bind("unit", Namespace("http://qudt.org/vocab/unit/"))
        self.graph.bind("prov", Namespace("http://www.w3.org/ns/prov#"))
        self.graph.bind("dcterms", Namespace("http://purl.org/dc/terms/"))
        self.graph.bind("skos", Namespace("http://www.w3.org/2004/02/skos/core#"))
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("rdf", RDF)
        self.graph.bind("owl", OWL)
        self.graph.bind("xsd", XSD)

    def _add_ontology_header_and_schema(self):
        """Add owl:Ontology header, owl:imports, and embed predicate declarations from rdf_schema.ttl."""
        ont_uri = URIRef("https://w3id.org/battgpt/kg")
        self.graph.add((ont_uri, RDF.type, OWL.Ontology))
        self.graph.add((ont_uri, RDFS.label, Literal("BattGPT Battery Materials Knowledge Graph", lang="en")))
        self.graph.add((ont_uri, OWL.versionInfo, Literal("0.1.0", datatype=XSD.string)))

        # Add owl:imports
        imports = [
            URIRef("https://w3id.org/emmo#"),
            URIRef("https://w3id.org/emmo/domain/battery#"),
            URIRef("https://w3id.org/emmo/domain/crystallography#"),
            URIRef("https://w3id.org/emmo/domain/chemical-substance#"),
            URIRef("http://qudt.org/schema/qudt/"),
            URIRef("http://www.w3.org/ns/prov#"),
            URIRef("http://purl.org/dc/terms/")
        ]
        for imp in imports:
            self.graph.add((ont_uri, OWL.imports, imp))

        # Merge predicate declarations from rdf_schema.ttl so graph is self-contained
        if SCHEMA_FILE.exists():
            schema_g = Graph()
            schema_g.parse(str(SCHEMA_FILE), format="turtle")
            for triple in schema_g:
                self.graph.add(triple)

    def build_graph(self, records: list[MaterialRecord]) -> Graph:
        """Construct knowledge graph from a list of enriched MaterialRecords."""
        logger.info(f"Building RDF Knowledge Graph for {len(records)} material records...")
        self._add_ontology_header_and_schema()
        for rec in records:
            self.generator.generate_triples(rec, self.graph)
        logger.info(f"RDF Graph construction complete. Total triples: {len(self.graph)}")
        return self.graph
