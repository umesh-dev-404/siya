"""
Audit Module

Audit logging system for complete auditability.
Per DIP Phase 3: Memory & Observability.

Enforces:
- LAW 13 — COMPLETE AUDITABILITY
- LAW 14 — LOG RETENTION DISCIPLINE
"""

from audit.audit_logger import AuditLogger

__all__ = ["AuditLogger"]
