"""Lightweight asyncio background scheduler for PlantBrain maintenance jobs."""

import asyncio
import logging


logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """Run periodic background jobs without Celery for hackathon deployment."""

    def __init__(self) -> None:
        """Create an idle scheduler."""

        self._tasks: list[asyncio.Task] = []
        self._running = False

    def start(self) -> None:
        """Start all scheduled background jobs."""

        if self._running:
            logger.info("Background scheduler already running")
            return

        self._running = True
        self._tasks.append(asyncio.create_task(self._compliance_scan_job()))
        self._tasks.append(asyncio.create_task(self._pattern_scan_job()))
        self._tasks.append(asyncio.create_task(self._health_log_job()))
        logger.info("Background scheduler started")

    def stop(self) -> None:
        """Stop all scheduled background jobs."""

        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()
        logger.info("Background scheduler stopped")

    async def _compliance_scan_job(self) -> None:
        """Runs every 6 hours. Checks completed documents against active rules."""

        await asyncio.sleep(30)
        while self._running:
            try:
                from sqlalchemy import select

                from app.database import AsyncSessionLocal
                from app.models.compliance import ComplianceCheck, ComplianceRule
                from app.models.document import Document
                from app.services.llm_service import llm_service
                from app.services.vector_store import vector_store

                logger.info("Starting scheduled compliance scan...")
                async with AsyncSessionLocal() as db:
                    documents_result = await db.execute(
                        select(Document).where(Document.status == "completed")
                    )
                    documents = documents_result.scalars().all()

                    rules_result = await db.execute(
                        select(ComplianceRule).where(ComplianceRule.is_active.is_(True))
                    )
                    rules = rules_result.scalars().all()

                    if not documents or not rules:
                        logger.info("No documents or rules to check. Skipping.")
                    else:
                        for document in documents[:5]:
                            chunks = await vector_store.search(
                                "safety procedure compliance",
                                top_k=3,
                                filter_document_id=document.id,
                            )
                            procedure_text = " ".join(chunk["text"] for chunk in chunks)
                            if not procedure_text.strip():
                                continue

                            for rule in rules[:3]:
                                result = await llm_service.check_compliance(
                                    procedure_text,
                                    rule.full_text or "",
                                    rule.rule_code,
                                )
                                db.add(
                                    ComplianceCheck(
                                        rule_id=rule.id,
                                        document_id=document.id,
                                        status=result.get("status", "unknown").lower(),
                                        findings=result.get("findings", ""),
                                    )
                                )
                        await db.commit()
                        logger.info("Compliance scan complete: %s documents checked", len(documents))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Compliance scan job failed: %s", exc)
            await asyncio.sleep(6 * 3600)

    async def _pattern_scan_job(self) -> None:
        """Runs every 12 hours. Computes risk summary and logs it."""

        await asyncio.sleep(60)
        while self._running:
            try:
                from app.database import AsyncSessionLocal
                from app.services.pattern_service import pattern_service

                logger.info("Starting scheduled pattern scan...")
                async with AsyncSessionLocal() as db:
                    summary = await pattern_service.get_risk_summary(db)
                    risk_level = summary.get("overall_risk_level", "Unknown")
                    logger.info("Pattern scan complete. Overall risk: %s", risk_level)
                    if risk_level in ["High", "Critical"]:
                        logger.warning("HIGH RISK DETECTED: %s", summary.get("critical_overdue", []))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("Pattern scan job failed: %s", exc)
            await asyncio.sleep(12 * 3600)

    async def _health_log_job(self) -> None:
        """Runs every 30 minutes. Logs system health stats."""

        await asyncio.sleep(10)
        while self._running:
            try:
                from app.services.graph_service import graph_service
                from app.services.vector_store import vector_store

                stats = await vector_store.get_stats()
                graph_stats = graph_service.get_graph_stats()
                logger.info(
                    "Health: ChromaDB chunks=%s, Graph nodes=%s, edges=%s",
                    stats["total_chunks"],
                    graph_stats["nodes"],
                    graph_stats["edges"],
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.debug("Health log failed: %s", exc)
            await asyncio.sleep(1800)


scheduler = BackgroundScheduler()
