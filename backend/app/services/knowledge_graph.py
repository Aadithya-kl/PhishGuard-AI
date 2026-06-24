from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from app.models.graph import Relationship, EntityType, RelationshipConfidence
from app.models.scan import EmailScan
import uuid

class KnowledgeGraphService:
    def __init__(self):
        pass

    async def build_graph_from_scan(self, scan_id: uuid.UUID, session: AsyncSession) -> bool:
        stmt = select(EmailScan).where(EmailScan.id == scan_id)
        res = await session.execute(stmt)
        scan = res.scalar_one_or_none()
        if not scan:
            return False

        org_id = scan.organization_id

        # Insert relationship: Sender -> Scan
        rel_sender = Relationship(
            organization_id=org_id,
            source_type=EntityType.sender,
            source_value=scan.sender_address,
            target_type=EntityType.scan,
            target_value=str(scan.id),
            relationship_type="sent",
            confidence=RelationshipConfidence.high
        )
        session.add(rel_sender)

        # If there's an IP in headers (basic mock extraction for graph)
        if "Received" in scan.raw_headers:
            import re
            ips = re.findall(r'[0-9]+(?:\.[0-9]+){3}', scan.raw_headers)
            for ip in set(ips):
                rel_ip = Relationship(
                    organization_id=org_id,
                    source_type=EntityType.ip,
                    source_value=ip,
                    target_type=EntityType.scan,
                    target_value=str(scan.id),
                    relationship_type="routed_through",
                    confidence=RelationshipConfidence.medium
                )
                session.add(rel_ip)

        # URL extraction (mocking for graph)
        import re
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', scan.body_text + scan.body_html)
        for url in set(urls):
            rel_url = Relationship(
                organization_id=org_id,
                source_type=EntityType.url,
                source_value=url,
                target_type=EntityType.scan,
                target_value=str(scan.id),
                relationship_type="contained_in",
                confidence=RelationshipConfidence.high
            )
            session.add(rel_url)

        return True

    async def query_graph(self, node_id: str, depth: int, session: AsyncSession, organization_id: uuid.UUID) -> Dict[str, Any]:
        """Simple breadth-first search up to `depth`."""
        visited_nodes = {node_id}
        edges = []
        current_layer = {node_id}

        for _ in range(depth):
            if not current_layer:
                break
                
            stmt = select(Relationship).where(
                and_(
                    Relationship.organization_id == organization_id,
                    or_(
                        Relationship.source_value.in_(current_layer),
                        Relationship.target_value.in_(current_layer)
                    )
                )
            )
            res = await session.execute(stmt)
            rels = res.scalars().all()

            next_layer = set()
            for r in rels:
                edge = {
                    "source": r.source_value,
                    "target": r.target_value,
                    "type": r.relationship_type,
                    "confidence": r.confidence
                }
                if edge not in edges:
                    edges.append(edge)
                
                if r.source_value not in visited_nodes:
                    visited_nodes.add(r.source_value)
                    next_layer.add(r.source_value)
                if r.target_value not in visited_nodes:
                    visited_nodes.add(r.target_value)
                    next_layer.add(r.target_value)
            
            current_layer = next_layer

        return {
            "nodes": list(visited_nodes),
            "edges": edges
        }

    async def get_graph_data(self, session: AsyncSession, organization_id: uuid.UUID) -> Dict[str, Any]:
        stmt = select(Relationship).where(Relationship.organization_id == organization_id).limit(100)
        res = await session.execute(stmt)
        rels = res.scalars().all()
        
        nodes = set()
        edges = []
        for r in rels:
            nodes.add(r.source_value)
            nodes.add(r.target_value)
            edges.append({
                "source": r.source_value,
                "target": r.target_value,
                "type": r.relationship_type
            })
            
        return {"nodes": list(nodes), "edges": edges}

    async def find_attack_chain(self, scan_id: str, session: AsyncSession, organization_id: uuid.UUID) -> List[Dict[str, Any]]:
        graph = await self.query_graph(scan_id, 2, session, organization_id)
        return graph.get("edges", [])
