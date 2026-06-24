import uuid
import base64
import os
import io
from datetime import datetime
from PIL import Image
from fpdf import FPDF
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.report import Report, ReportType, ReportStatus, ReportFormat
from app.models.scan import EmailScan
from app.models.investigation import Investigation

class SOCReportPDF(FPDF):
    def __init__(self, title="Security Report"):
        super().__init__()
        self.report_title = title
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Arial bold 15
        self.set_font('helvetica', 'B', 15)
        self.set_text_color(0, 51, 102)
        # Title
        self.cell(0, 10, 'PhishGuard AI - SOC Intelligence Platform', 0, 1, 'C')
        self.set_font('helvetica', 'I', 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, self.report_title, 0, 1, 'C')
        self.line(10, 30, 200, 30)
        self.ln(10)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        # Page number
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        self.cell(0, 10, f'Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}', 0, 0, 'R')

    def chapter_title(self, title):
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, title, 0, 1, 'L')
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('helvetica', '', 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 7, body)
        self.ln()

    def add_key_value(self, key, value):
        self.set_font('helvetica', 'B', 11)
        self.set_text_color(50, 50, 50)
        self.cell(50, 7, f"{key}:", border=0)
        self.set_font('helvetica', '', 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 7, str(value))

class ReportGeneratorService:
    def __init__(self, db: Session):
        self.db = db
        self.reports_dir = "/app/reports" if os.path.exists("/app") else "./reports"
        os.makedirs(self.reports_dir, exist_ok=True)

    def fetch_scan_data(self, scan_id: uuid.UUID):
        scan = self.db.execute(select(EmailScan).where(EmailScan.id == scan_id)).scalar_one_or_none()
        if not scan:
            raise ValueError(f"Scan {scan_id} not found")
        return {
            "title": f"Scan Report: {scan.subject}",
            "summary": "This report details the security findings for the analyzed email.",
            "metadata": {
                "Subject": scan.subject,
                "Sender": f"{scan.sender_display_name} <{scan.sender_address}>",
                "Recipient": scan.recipient,
                "Risk Level": scan.risk_level.value.upper(),
                "Overall Score": scan.overall_risk_score,
                "Attack Type": scan.attack_type or "None"
            },
            "findings": scan.ai_analysis.technical_summary if scan.ai_analysis else "No AI analysis available.",
            "recommendations": scan.ai_analysis.executive_summary if scan.ai_analysis else "No recommendations.",
            "mitre": scan.ai_analysis.tactics_detected if scan.ai_analysis else {},
            "iocs": [f"{ioc.ioc_type.value}: {ioc.value}" for ioc in scan.iocs]
        }

    def fetch_investigation_data(self, investigation_id: uuid.UUID):
        inv = self.db.execute(select(Investigation).where(Investigation.id == investigation_id)).scalar_one_or_none()
        if not inv:
            raise ValueError(f"Investigation {investigation_id} not found")
        return {
            "title": f"Investigation Report: {inv.title}",
            "summary": inv.summary or "Detailed investigation report.",
            "metadata": {
                "Priority": inv.priority.value.upper(),
                "Severity": inv.severity.value.upper(),
                "Status": inv.status.value.upper(),
                "Created At": inv.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
            },
            "findings": "Investigation nodes and correlations.",
            "recommendations": "Based on investigation findings, perform remediation.",
            "mitre": inv.mitre_tactics or [],
            "iocs": []
        }

    def generate_pdf(self, report_data: dict, graph_b64: str = None, automation_data: dict = None) -> str:
        pdf = SOCReportPDF(title=report_data.get("title", "Report"))
        
        # Cover Page
        pdf.add_page()
        pdf.set_y(100)
        pdf.set_font("helvetica", "B", 24)
        pdf.cell(0, 15, "Security Intelligence Report", 0, 1, "C")
        pdf.set_font("helvetica", "I", 14)
        pdf.cell(0, 10, report_data.get("title", "Untitled"), 0, 1, "C")
        pdf.ln(20)
        pdf.set_font("helvetica", "", 12)
        pdf.cell(0, 10, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d')}", 0, 1, "C")
        
        # Executive Summary
        pdf.add_page()
        pdf.chapter_title("Executive Summary")
        for k, v in report_data.get("metadata", {}).items():
            pdf.add_key_value(k, v)
        pdf.ln(5)
        pdf.chapter_body(report_data.get("summary", ""))
        
        # Technical Findings
        pdf.chapter_title("Technical Findings")
        pdf.chapter_body(report_data.get("findings", ""))
        
        # MITRE ATT&CK Mapping
        if report_data.get("mitre"):
            pdf.chapter_title("MITRE ATT&CK Mapping")
            for t in report_data.get("mitre", []):
                pdf.chapter_body(f"- {t}")
        
        # Detected IOCs
        if report_data.get("iocs"):
            pdf.chapter_title("Detected Indicators of Compromise (IOCs)")
            for ioc in report_data.get("iocs", []):
                pdf.chapter_body(f"- {ioc}")
                
        # Graph Snapshot
        if graph_b64:
            pdf.add_page()
            pdf.chapter_title("Knowledge Graph Snapshot")
            try:
                # Remove data URI prefix if present
                if "," in graph_b64:
                    graph_b64 = graph_b64.split(",")[1]
                img_data = base64.b64decode(graph_b64)
                img = Image.open(io.BytesIO(img_data))
                # Save temp image for FPDF
                temp_img_path = f"/tmp/{uuid.uuid4().hex}.png"
                img.save(temp_img_path)
                # Add image, width 190mm
                pdf.image(temp_img_path, w=190)
                os.remove(temp_img_path)
            except Exception as e:
                pdf.chapter_body(f"Error rendering graph snapshot: {str(e)}")
                
        # Automation Intelligence Section
        if automation_data:
            pdf.add_page()
            pdf.chapter_title("Automation Intelligence & Trust")
            pdf.chapter_body("Summary of playbook performance and analyst trust metrics.")
            pdf.ln(5)
            for k, v in automation_data.items():
                if isinstance(v, list):
                    pdf.add_key_value(k, ", ".join(v) if v else "None")
                else:
                    pdf.add_key_value(k, v)
                pdf.ln(2)
                
        # Recommendations
        pdf.add_page()
        pdf.chapter_title("Recommendations")
        pdf.chapter_body(report_data.get("recommendations", ""))
        
        file_id = uuid.uuid4().hex
        file_path = os.path.join(self.reports_dir, f"report_{file_id}.pdf")
        pdf.output(file_path)
        return file_path

    def generate_executive_report(self, data: dict) -> dict:
        """
        Generate the Executive Security Operations Report in PDF and JSON formats.
        """
        file_id = uuid.uuid4().hex
        pdf = SOCReportPDF(title="Executive Security Operations Report")
        
        pdf.add_page()
        pdf.set_y(100)
        pdf.set_font("helvetica", "B", 24)
        pdf.cell(0, 15, "Executive Security Operations Report", 0, 1, "C")
        pdf.set_font("helvetica", "I", 14)
        pdf.cell(0, 10, "Monthly Organizational Posture & Intelligence", 0, 1, "C")
        pdf.ln(20)
        pdf.set_font("helvetica", "", 12)
        pdf.cell(0, 10, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d')}", 0, 1, "C")
        
        # 1. Security Posture
        pdf.add_page()
        pdf.chapter_title("Security Posture")
        if "posture" in data:
            pdf.add_key_value("Security Score", f"{data['posture'].get('score')} / 100")
            pdf.add_key_value("Rating", data['posture'].get('rating'))
            pdf.ln(5)
            pdf.chapter_body("Key Factors:")
            for k, v in data['posture'].get('factors', {}).items():
                pdf.add_key_value(k.replace('_', ' ').title(), v)
                
        # 2. Threat Landscape
        pdf.add_page()
        pdf.chapter_title("Threat Landscape")
        if "overview" in data:
            for k, v in data['overview'].items():
                pdf.add_key_value(k.replace('_', ' ').title(), v)
                
        # 3. MITRE Coverage
        pdf.add_page()
        pdf.chapter_title("MITRE ATT&CK Coverage")
        if "mitre" in data:
            pdf.add_key_value("Detection Success Rate", f"{data['mitre'].get('detection_success_rate')}%")
            pdf.ln(5)
            pdf.chapter_body("Top Detected Techniques:")
            for tech in data['mitre'].get("most_triggered_techniques", []):
                pdf.chapter_body(f"- {tech['name']} ({tech['count']})")
                
        # 4. Automation Effectiveness
        pdf.add_page()
        pdf.chapter_title("Automation Effectiveness")
        if "automation" in data:
            for k, v in data['automation'].items():
                # Avoid printing large lists
                if not isinstance(v, list):
                    pdf.add_key_value(k.replace('_', ' ').title(), v)
                    
        # 5. Copilot Performance
        pdf.add_page()
        pdf.chapter_title("Copilot Operational Performance")
        if "copilot" in data:
            for cat, metrics in data['copilot'].items():
                pdf.chapter_body(f"[{cat.upper()}]")
                for k, v in metrics.items():
                    pdf.add_key_value(k.replace('_', ' ').title(), v)
                pdf.ln(5)
                
        # 6. Strategic Recommendations
        pdf.add_page()
        pdf.chapter_title("Strategic Recommendations")
        pdf.chapter_body("Based on the current security posture and operational metrics, the following strategic actions are recommended:")
        pdf.chapter_body("- Review playbooks with Trust Score below 70.")
        pdf.chapter_body("- Address the active critical investigations immediately to improve posture.")
        pdf.chapter_body("- Investigate detection gaps in newly identified MITRE techniques.")
        
        pdf_path = os.path.join(self.reports_dir, f"exec_report_{file_id}.pdf")
        pdf.output(pdf_path)
        
        json_path = os.path.join(self.reports_dir, f"exec_report_{file_id}.json")
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
            
        return {"pdf_path": pdf_path, "json_path": json_path, "data": data}

    def generate_active_response_readiness_report(self, data: dict) -> dict:
        """
        Generate the Active Response Readiness Report in PDF and JSON formats.
        """
        file_id = uuid.uuid4().hex
        pdf = SOCReportPDF(title="Active Response Readiness Report")
        
        pdf.add_page()
        pdf.set_y(100)
        pdf.set_font("helvetica", "B", 24)
        pdf.cell(0, 15, "Active Response Readiness Report", 0, 1, "C")
        pdf.set_font("helvetica", "I", 14)
        pdf.cell(0, 10, "Operational Trust Validation", 0, 1, "C")
        pdf.ln(20)
        pdf.set_font("helvetica", "", 12)
        pdf.cell(0, 10, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d')}", 0, 1, "C")
        
        # 1. Final Recommendation
        pdf.add_page()
        pdf.chapter_title("Readiness Determination")
        if "readiness" in data:
            status = data["readiness"].get("status", "UNKNOWN")
            score = data["readiness"].get("readiness_score", 0.0)
            pdf.add_key_value("Readiness Status", status)
            pdf.add_key_value("Readiness Score", str(score))
            pdf.ln(5)
            
            if data["readiness"].get("reasons"):
                pdf.chapter_body("Failure Reasons:")
                for r in data["readiness"]["reasons"]:
                    pdf.chapter_body(f"- {r}")
                    
        # 2. Automation Trust
        pdf.add_page()
        pdf.chapter_title("Automation Trust")
        if "trust" in data:
            pdf.chapter_body(f"Overall Trend: {data['trust'].get('overall_trend')}")
            pdf.ln(5)
            if "30_days" in data["trust"]:
                pdf.add_key_value("30-Day Acceptance Rate", f"{data['trust']['30_days']['acceptance_rate']:.1f}%")
                pdf.add_key_value("30-Day False Action Rate", f"{data['trust']['30_days']['false_action_rate']:.1f}%")
                
        # 3. Playbook Quality
        pdf.add_page()
        pdf.chapter_title("Playbook Quality Rankings")
        if "quality" in data:
            pdf.chapter_body("Best Performing:")
            for p in data["quality"].get("best_performing", []):
                pdf.chapter_body(f"- {p}")
            pdf.ln(5)
            pdf.chapter_body("Needs Review:")
            for p in data["quality"].get("needs_review", []):
                pdf.chapter_body(f"- {p}")
                
        # 4. Governance & Copilot Status
        pdf.add_page()
        pdf.chapter_title("Governance & Copilot Status")
        if "governance" in data:
            pdf.add_key_value("Governance Audit", "PASSED" if data["governance"].get("passed") else "FAILED")
        if "copilot" in data:
            pdf.add_key_value("Copilot Readiness", "PASSED" if data["copilot"].get("passed") else "FAILED")
            
        pdf_path = os.path.join(self.reports_dir, f"ar_readiness_{file_id}.pdf")
        pdf.output(pdf_path)
        
        json_path = os.path.join(self.reports_dir, f"ar_readiness_{file_id}.json")
        import json
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
            
        return {"pdf_path": pdf_path, "json_path": json_path, "data": data}
