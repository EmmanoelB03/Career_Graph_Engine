"""
Módulo de Ontologia para o grafo de carreira.

Exporta o grafo NetworkX como RDF/Turtle com um esquema mais rico para
consulta, inspeção e integração com ferramentas semânticas.
"""
from typing import Any, Optional

try:
    from rdflib import Graph, Namespace, URIRef, Literal
    from rdflib.namespace import RDF, RDFS, XSD, SKOS, OWL
    RDFlIB_AVAILABLE = True
except Exception:
    RDFlIB_AVAILABLE = False


DEFAULT_NS = "http://example.org/career#"


def annotate_graph_to_rdf(
    G,
    output_path: str = "output/career_ontology.ttl",
    base_ns: str = DEFAULT_NS,
    market: Optional[dict[str, Any]] = None,
    match_result: Optional[dict[str, Any]] = None,
    candidate_skills: Optional[list[str]] = None,
    target_role: Optional[str] = None,
) -> Optional[str]:
    """Converte o grafo NetworkX em um grafo RDF (Turtle) e salva em disco.

    Retorna o caminho do arquivo salvo ou None se `rdflib` não estiver disponível.
    """
    if not RDFlIB_AVAILABLE:
        return None

    g = Graph()
    NS = Namespace(base_ns)
    g.bind("career", NS)
    g.bind("skos", SKOS)
    g.bind("rdfs", RDFS)
    g.bind("owl", OWL)

    ontology_uri = NS.CareerOntology
    g.add((ontology_uri, RDF.type, OWL.Ontology))
    g.add((ontology_uri, RDFS.label, Literal("Career Graph Ontology", datatype=XSD.string)))
    g.add((ontology_uri, RDFS.comment, Literal("Ontology generated from the Career Graph Engine.")))

    # Classes
    Candidate = NS.Candidate
    Role = NS.Role
    Skill = NS.Skill
    SkillCategory = NS.SkillCategory
    MarketSnapshot = NS.MarketSnapshot
    MatchResult = NS.MatchResult
    Gap = NS.Gap

    for klass, label, comment, parent in [
        (Candidate, "Candidate", "Represents the user profile being analyzed.", NS.Person),
        (Role, "Role", "Represents a target job role.", NS.WorkRole),
        (Skill, "Skill", "Represents a technical or domain skill.", SKOS.Concept),
        (SkillCategory, "Skill Category", "Groups related skills into a conceptual category.", SKOS.ConceptScheme),
        (MarketSnapshot, "Market Snapshot", "Aggregated market view extracted from job postings.", NS.Dataset),
        (MatchResult, "Match Result", "Outcome of the candidate-to-role matching.", NS.Observation),
        (Gap, "Gap", "A missing skill that contributes to a lower match score.", NS.Observation),
    ]:
        g.add((klass, RDF.type, RDFS.Class))
        g.add((klass, RDFS.label, Literal(label, datatype=XSD.string)))
        g.add((klass, RDFS.comment, Literal(comment, datatype=XSD.string)))
        g.add((klass, RDFS.subClassOf, parent))

    # Fallback classes used above to keep the ontology self-contained.
    for klass, label in [
        (NS.Person, "Person"),
        (NS.WorkRole, "Work Role"),
        (NS.Dataset, "Dataset"),
        (NS.Observation, "Observation"),
        (NS.Entity, "Entity"),
    ]:
        g.add((klass, RDF.type, RDFS.Class))
        g.add((klass, RDFS.label, Literal(label, datatype=XSD.string)))

    # Properties
    properties = {
        "hasSkill": (Candidate, Skill),
        "requiresSkill": (Role, Skill),
        "matchedSkill": (MatchResult, Skill),
        "missingSkill": (Gap, Skill),
        "hasRole": (MatchResult, Role),
        "hasScore": (MatchResult, XSD.decimal),
        "hasWeight": (NS.Entity, XSD.decimal),
        "skillFrequency": (Skill, XSD.decimal),
        "appearsInJobs": (Skill, XSD.integer),
        "sourceCount": (MarketSnapshot, XSD.integer),
        "targetRoleName": (MatchResult, XSD.string),
        "nodeType": (NS.Entity, XSD.string),
        "relatedTo": (NS.Entity, NS.Entity),
    }

    for prop_name, (domain, range_) in properties.items():
        prop = NS[prop_name]
        g.add((prop, RDF.type, RDF.Property))
        g.add((prop, RDFS.label, Literal(prop_name, datatype=XSD.string)))
        g.add((prop, RDFS.domain, domain))
        g.add((prop, RDFS.range, range_))

    # Main snapshot node for the generated export.
    snapshot = NS.MarketSnapshotCurrent
    g.add((snapshot, RDF.type, MarketSnapshot))
    g.add((snapshot, RDFS.label, Literal("Current market snapshot", datatype=XSD.string)))
    if market:
        g.add((snapshot, NS.sourceCount, Literal(int(market.get("total_jobs", 0)), datatype=XSD.integer)))
        if market.get("target_role"):
            g.add((snapshot, NS.targetRoleName, Literal(str(market["target_role"]), datatype=XSD.string)))

    # Optional match result node.
    match_node = None
    if match_result:
        match_node = NS["MatchResultCurrent"]
        g.add((match_node, RDF.type, MatchResult))
        g.add((match_node, RDFS.label, Literal("Current match result", datatype=XSD.string)))
        g.add((match_node, NS.hasScore, Literal(float(match_result.get("score", 0.0)), datatype=XSD.decimal)))
        if match_result.get("role"):
            g.add((match_node, NS.targetRoleName, Literal(str(match_result["role"]), datatype=XSD.string)))

    # Map NetworkX nodes to URIs and add triples.
    for node, data in G.nodes(data=True):
        uri = URIRef(f"{base_ns}{_uri_safe(node)}")
        ntype = data.get("node_type", "")
        label = data.get("label", str(node))

        g.add((uri, RDFS.label, Literal(label, datatype=XSD.string)))
        g.add((uri, NS.nodeType, Literal(ntype or "unknown", datatype=XSD.string)))

        if ntype == "candidate":
            g.add((uri, RDF.type, Candidate))
        elif ntype == "role":
            g.add((uri, RDF.type, Role))
        elif ntype in ("candidate_skill", "market_skill", "skill"):
            g.add((uri, RDF.type, Skill))
        else:
            g.add((uri, RDF.type, NS.Entity))

    # Map edges with richer annotations.
    for u, v, data in G.edges(data=True):
        uuri = URIRef(f"{base_ns}{_uri_safe(u)}")
        vuri = URIRef(f"{base_ns}{_uri_safe(v)}")
        etype = data.get("edge_type", "")
        weight = data.get("weight", None)

        if etype == "has_skill":
            g.add((uuri, NS.hasSkill, vuri))
        elif etype == "requires":
            g.add((uuri, NS.requiresSkill, vuri))
        elif etype == "affinity":
            g.add((uuri, NS.relatedTo, vuri))
            if match_node is not None and (u == "CANDIDATE" or v == "CANDIDATE"):
                g.add((match_node, NS.hasRole, vuri if u == "CANDIDATE" else uuri))
        else:
            g.add((uuri, NS.relatedTo, vuri))

        if weight is not None:
            g.add((uuri, NS.hasWeight, Literal(float(weight), datatype=XSD.decimal)))

    # Market-driven skill frequencies when available.
    role_profiles = (market or {}).get("role_profiles", {})
    for role_name, skill_weights in role_profiles.items():
        role_uri = URIRef(f"{base_ns}{_uri_safe(role_name)}")
        g.add((role_uri, RDF.type, Role))
        g.add((role_uri, RDFS.label, Literal(role_name, datatype=XSD.string)))
        for skill_name, skill_weight in skill_weights.items():
            skill_uri = URIRef(f"{base_ns}{_uri_safe(skill_name)}")
            g.add((role_uri, NS.requiresSkill, skill_uri))
            g.add((skill_uri, RDF.type, Skill))
            g.add((skill_uri, NS.skillFrequency, Literal(float(skill_weight), datatype=XSD.decimal)))

    # Candidate skills and match gaps for the currently analyzed role.
    if candidate_skills:
        candidate_uri = NS.CANDIDATE
        for skill_name in candidate_skills:
            skill_uri = URIRef(f"{base_ns}{_uri_safe(skill_name)}")
            g.add((candidate_uri, NS.hasSkill, skill_uri))
            g.add((skill_uri, RDF.type, Skill))

    if match_result:
        result_uri = match_node
        for skill_name in match_result.get("matched_skills", []):
            skill_uri = URIRef(f"{base_ns}{_uri_safe(skill_name)}")
            g.add((result_uri, NS.matchedSkill, skill_uri))

        for gap in match_result.get("gaps", []):
            skill_name = gap.get("skill")
            if not skill_name:
                continue
            gap_uri = URIRef(f"{base_ns}gap_{_uri_safe(skill_name)}")
            g.add((gap_uri, RDF.type, Gap))
            g.add((gap_uri, RDFS.label, Literal(skill_name, datatype=XSD.string)))
            g.add((gap_uri, NS.missingSkill, URIRef(f"{base_ns}{_uri_safe(skill_name)}")))
            g.add((gap_uri, NS.hasWeight, Literal(float(gap.get("impact", 0.0)), datatype=XSD.decimal)))
            g.add((result_uri, NS.missingSkill, gap_uri))

    g.serialize(destination=output_path, format="turtle")
    return output_path


def _uri_safe(label: str) -> str:
    """Cria uma versão segura para URI a partir de um rótulo de nó."""
    if not isinstance(label, str):
        label = str(label)
    # substitui espaços e caracteres especiais por underline
    safe = "".join(c if c.isalnum() else "_" for c in label)
    return safe


def available() -> bool:
    return RDFlIB_AVAILABLE
