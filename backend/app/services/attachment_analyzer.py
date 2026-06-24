from typing import Dict, Any, List
from app.schemas.scan import EvidenceItem as Evidence
import hashlib

class AttachmentAnalyzer:
    def __init__(self):
        self.executables = [".exe", ".scr", ".pif", ".cmd", ".bat", ".com", ".vbs"]
        self.macro_docs = [".docm", ".xlsm", ".pptm"]
        
    def analyze(self, attachments: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = []
        total_score = 0
        all_evidence = []
        
        for att in attachments:
            filename = att.get("filename", "").lower()
            size = att.get("size", 0)
            
            is_executable = any(filename.endswith(ext) for ext in self.executables)
            has_macros = any(filename.endswith(ext) for ext in self.macro_docs)
            is_double_extension = len(filename.split(".")) > 2
            
            try:
                import magic
            except ImportError:
                magic = None
                
            mime_type = att.get("content_type", "application/octet-stream")
            md5_hash = ""
            sha1_hash = ""
            sha256_hash = ""
            
            if att.get("payload") and isinstance(att["payload"], bytes):
                payload = att["payload"]
                md5_hash = hashlib.md5(payload).hexdigest()
                sha1_hash = hashlib.sha1(payload).hexdigest()
                sha256_hash = hashlib.sha256(payload).hexdigest()
                
                if magic:
                    try:
                        mime_type = magic.from_buffer(payload[:2048], mime=True)
                    except Exception:
                        pass
                        
            # Override is_executable if magic detects it
            if "executable" in mime_type or "x-dosexec" in mime_type or "x-msdownload" in mime_type:
                is_executable = True
            
            score = 0
            evidence = []
            
            if is_executable:
                score += 90
                evidence.append(Evidence(
                    type="executable_attachment",
                    description="Attachment is an executable file",
                    severity="critical",
                    impact_on_score=90
                ))
                
            if has_macros:
                score += 70
                evidence.append(Evidence(
                    type="macro_enabled",
                    description="Attachment is a macro-enabled document",
                    severity="high",
                    impact_on_score=70
                ))
                
            if is_double_extension:
                score += 50
                evidence.append(Evidence(
                    type="double_extension",
                    description="Attachment has a double extension to trick users",
                    severity="medium",
                    impact_on_score=50
                ))
                
            capped_score = min(100, score)
            total_score += capped_score
            all_evidence.extend(evidence)
            
            results.append({
                "filename": filename,
                "content_type": mime_type,
                "file_size": size,
                "md5_hash": md5_hash,
                "sha256_hash": sha256_hash,
                "is_executable": is_executable,
                "has_macros": has_macros,
                "is_double_extension": is_double_extension,
                "file_metadata": {"sha1_hash": sha1_hash, "detected_mime": mime_type},
                "threat_score": capped_score,
                "evidence": [e.model_dump() for e in evidence]
            })
            
        avg_score = total_score / len(attachments) if attachments else 0
        
        return {
            "analyses": results,
            "aggregate_score": avg_score,
            "aggregate_evidence": [e.model_dump() for e in all_evidence]
        }
