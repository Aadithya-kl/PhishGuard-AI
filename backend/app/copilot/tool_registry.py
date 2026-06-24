from typing import Dict, Any, Callable, List
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.scan import EmailScan
from app.models.investigation import Investigation
from app.models.report import Report
from app.services.knowledge_graph import KnowledgeGraphService

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.kg_service = KnowledgeGraphService()

    def register(self, name: str, func: Callable):
        self.tools[name] = func

    async def execute(self, name: str, params: Dict[str, Any], session: AsyncSession, organization_id: str) -> Dict[str, Any]:
        if name not in self.tools:
            return {"error": f"Tool {name} not found"}
        try:
            logger.info(f"Executing Copilot tool: {name} with params: {params}")
            # Inject session and user_id into params if the tool needs it
            return await self.tools[name](**params, session=session, organization_id=organization_id)
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return {"error": str(e)}

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        # Used to inform the LLM what tools are available
        return [
            {
                "name": "search_scans",
                "description": "Search email scans. Parameters: query (str)",
                "parameters": {"query": "string"}
            },
            {
                "name": "search_investigations",
                "description": "Search investigations. Parameters: query (str)",
                "parameters": {"query": "string"}
            },
            {
                "name": "graph_lookup",
                "description": "Look up an IOC in the knowledge graph. Parameters: ioc_value (str)",
                "parameters": {"ioc_value": "string"}
            },
            {
                "name": "ioc_lookup",
                "description": "Look up an IOC in threat intelligence. Parameters: value (str)",
                "parameters": {"value": "string"}
            },
            {
                "name": "mitre_lookup",
                "description": "Look up a MITRE ATT&CK technique. Parameters: technique_id (str)",
                "parameters": {"technique_id": "string"}
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recommended_actions",
                    "description": "Retrieve playbook-generated deterministic action recommendations for the current scan or investigation context. ALWAYS use this instead of generating hallucinated remediation actions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "scan_id": {
                                "type": "string",
                                "description": "The UUID of the scan to find recommendations for."
                            }
                        },
                        "required": ["scan_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_playbook_metrics",
                    "description": "Retrieve playbook performance metrics including generated, approved, rejected counts and acceptance/false action rates.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_trust_scores",
                    "description": "Retrieve current trust scores for playbooks.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_recommendation_history",
                    "description": "Retrieve the history of recommendation outcomes (approvals, rejections).",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "name": "simulate_response",
                "description": "Simulate an active response action. Parameters: action_type (str), target_entity (str)",
                "parameters": {"action_type": "string", "target_entity": "string"}
            },
            {
                "name": "explain_response",
                "description": "Explain an active response action including impact and mappings. Parameters: action_type (str), target_entity (str)",
                "parameters": {"action_type": "string", "target_entity": "string"}
            },
            {
                "name": "generate_response_plan",
                "description": "Generate a response plan based on context. Parameters: threat_context (str)",
                "parameters": {"threat_context": "string"}
            },
            {
                "name": "get_rollback_steps",
                "description": "Get rollback steps for an action. Parameters: action_type (str)",
                "parameters": {"action_type": "string"}
            }
        ]

registry = ToolRegistry()

# --- Implementations ---

async def search_scans(query: str, session: AsyncSession, organization_id: str) -> Dict[str, Any]:
    # Tenant scoped search
    stmt = select(EmailScan).where(EmailScan.organization_id == organization_id).limit(5)
    # Local search filter
    result = await session.execute(stmt)
    scans = result.scalars().all()
    # Filter by query in python for simplicity in this implementation
    matches = [s for s in scans if query.lower() in s.subject.lower() or query.lower() in s.sender_address.lower()]
    if not matches:
        matches = scans # Return recent if no strict match
    
    return {
        "results": [
            {
                "id": s.id,
                "subject": s.subject,
                "sender": s.sender_address,
                "risk_level": s.risk_level,
                "ai_analysis": s.ai_analysis
            } for s in matches
        ]
    }

async def search_investigations(query: str, session: AsyncSession, organization_id: str) -> Dict[str, Any]:
    stmt = select(Investigation).where(Investigation.organization_id == organization_id).limit(5)
    result = await session.execute(stmt)
    invs = result.scalars().all()
    matches = [i for i in invs if query.lower() in i.title.lower() or query.lower() in i.description.lower()]
    if not matches:
        matches = invs
        
    return {
        "results": [
            {
                "id": i.id,
                "title": i.title,
                "status": i.status,
                "severity": i.severity,
                "findings": i.findings
            } for i in matches
        ]
    }

async def graph_lookup(ioc_value: str, session: AsyncSession, organization_id: str) -> Dict[str, Any]:
    kg = KnowledgeGraphService()
    try:
        data = await kg.query_graph(ioc_value, 2, session, organization_id)
        return {"results": data}
    except Exception as e:
        return {"error": str(e)}

async def ioc_lookup(value: str, session: AsyncSession, organization_id: str) -> Dict[str, Any]:
    from app.models.threat import ThreatIntelCache, ThreatCampaign
    
    # Query cache
    stmt = select(ThreatIntelCache).where(ThreatIntelCache.indicator_value == value)
    res = await session.execute(stmt)
    cache = res.scalars().first()
    
    # Query campaigns
    stmt_camp = select(ThreatCampaign).where(
        (ThreatCampaign.organization_id == organization_id)
    )
    res_camp = await session.execute(stmt_camp)
    campaigns = res_camp.scalars().all()
    
    # Find matching campaigns
    matched_campaigns = []
    for c in campaigns:
        if c.indicators and value in c.indicators.get("urls", []) or value in c.indicators.get("domains", []):
            matched_campaigns.append(c.name)
            
    return {
        "ioc": value,
        "reputation": cache.results.get("reputation", "unknown") if cache and cache.results else "unknown",
        "threat_score": cache.results.get("threat_score", 0) if cache and cache.results else 0,
        "associated_campaigns": matched_campaigns
    }

async def mitre_lookup(technique_id: str, session: AsyncSession, organization_id: str) -> Dict[str, Any]:
    # Local MITRE DB
    mitre_db = {
        "T1566": {"name": "Phishing", "description": "Adversaries may send phishing messages to gain access to victim systems."},
        "T1114": {"name": "Email Collection", "description": "Adversaries may target user email to collect sensitive information."},
        "T1566.002": {"name": "Spearphishing Link", "description": "Adversaries may send spearphishing emails with a malicious link."}
    }
    return mitre_db.get(technique_id.upper(), {"error": "Technique not found"})

async def get_recommended_actions(scan_id: str, session: AsyncSession, organization_id: str) -> Dict[str, Any]:
    from app.models.playbook import ActionRecommendation
    
    query = select(ActionRecommendation).where(
        ActionRecommendation.organization_id == organization_id,
        ActionRecommendation.scan_id == scan_id
    )
    res = await session.execute(query)
    actions = res.scalars().all()
    
    if not actions:
        return {"result": "No approved playbook recommendations currently exist. Do NOT invent your own remediations. Tell the user there are no recommendations."}
        
    output = []
    for a in actions:
        output.append({
            "playbook": a.playbook_name,
            "type": a.recommendation_type,
            "confidence_level": a.confidence_level.value,
            "status": a.status.value,
            "evidence": {
                "triggering_detections": a.triggering_detections,
                "triggering_mitre_ids": a.triggering_mitre_ids,
                "triggering_iocs": a.triggering_iocs
            }
        })
        
    return {"result": "Here are the deterministic recommendations you must present to the user without hallucinating new ones:", "recommendations": output}

async def get_playbook_metrics(session: AsyncSession, organization_id: str, **kwargs) -> Dict[str, Any]:
    from app.models.recommendation_feedback import PlaybookPerformanceMetrics
    query = select(PlaybookPerformanceMetrics).where(PlaybookPerformanceMetrics.organization_id == organization_id)
    res = await session.execute(query)
    metrics = res.scalars().all()
    
    return {
        "metrics": [
            {
                "playbook": m.playbook_name,
                "generated": m.recommendations_generated,
                "approved": m.recommendations_approved,
                "rejected": m.recommendations_rejected,
                "acceptance_rate": m.acceptance_rate,
                "false_action_rate": m.false_action_rate,
                "override_rate": m.analyst_override_rate
            } for m in metrics
        ]
    }

async def get_trust_scores(session: AsyncSession, organization_id: str, **kwargs) -> Dict[str, Any]:
    from app.models.recommendation_feedback import PlaybookPerformanceMetrics
    query = select(PlaybookPerformanceMetrics).where(PlaybookPerformanceMetrics.organization_id == organization_id)
    res = await session.execute(query)
    metrics = res.scalars().all()
    
    return {
        "trust_scores": [
            {
                "playbook": m.playbook_name,
                "score": m.trust_score
            } for m in metrics
        ]
    }

async def get_recommendation_history(session: AsyncSession, organization_id: str, **kwargs) -> Dict[str, Any]:
    from app.models.recommendation_feedback import RecommendationOutcome
    query = select(RecommendationOutcome).where(RecommendationOutcome.organization_id == organization_id).order_by(RecommendationOutcome.created_at.desc()).limit(10)
    res = await session.execute(query)
    outcomes = res.scalars().all()
    
    return {
        "history": [
            {
                "outcome_type": o.outcome_type.value,
                "category": o.feedback_category.value if o.feedback_category else "N/A",
                "reason": o.feedback_reason
            } for o in outcomes
        ]
    }

# Register tools
registry.register("search_scans", search_scans)
registry.register("search_investigations", search_investigations)
registry.register("graph_lookup", graph_lookup)
registry.register("ioc_lookup", ioc_lookup)
registry.register("mitre_lookup", mitre_lookup)
registry.register("get_recommended_actions", get_recommended_actions)
registry.register("get_playbook_metrics", get_playbook_metrics)
registry.register("get_trust_scores", get_trust_scores)
registry.register("get_recommendation_history", get_recommendation_history)

from app.copilot.tools.response import simulate_response, explain_response, generate_response_plan, get_rollback_steps
registry.register("simulate_response", simulate_response)
registry.register("explain_response", explain_response)
registry.register("generate_response_plan", generate_response_plan)
registry.register("get_rollback_steps", get_rollback_steps)
