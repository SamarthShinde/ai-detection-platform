"""Export service — serialises detection and batch results to JSON, CSV, or PDF."""
import csv
import io
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ExportService:
    """Convert Detection / Batch ORM objects into exportable formats."""

    # ── Single detection ──────────────────────────────────────────────────────

    def export_detection_as_json(self, detection) -> dict:
        """Return a fully-serialised dict for a single Detection record."""
        return {
            "detection_id": detection.id,
            "user_id": detection.user_id,
            "batch_id": detection.batch_id,
            "file_hash": detection.file_hash,
            "file_type": detection.file_type,
            "original_filename": detection.original_filename,
            "file_size_bytes": detection.file_size_bytes,
            "processing_status": detection.processing_status,
            "ai_probability": detection.ai_probability,
            "confidence_score": detection.confidence_score,
            "detection_methods": detection.detection_methods,
            "artifacts_found": (
                detection.result_json.get("artifacts_found") if detection.result_json else []
            ),
            "processing_time_ms": detection.processing_time_ms,
            "served_from_cache": getattr(detection, "served_from_cache", False),
            "error_message": detection.error_message,
            "uploaded_at": detection.uploaded_at.isoformat() if detection.uploaded_at else None,
            "completed_at": detection.completed_at.isoformat() if detection.completed_at else None,
            "result_json": detection.result_json,
            "exported_at": datetime.utcnow().isoformat(),
        }

    # ── Batch ─────────────────────────────────────────────────────────────────

    def export_batch_as_csv(self, batch, detections: list) -> str:
        """
        Generate CSV content for all detections in a batch.

        Columns: detection_id, filename, upload_time, ai_probability,
                 confidence_score, processing_time_ms, status, served_from_cache
        """
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "detection_id",
                "filename",
                "file_type",
                "upload_time",
                "ai_probability",
                "confidence_score",
                "processing_time_ms",
                "status",
                "served_from_cache",
                "error_message",
            ],
        )
        writer.writeheader()
        for d in detections:
            writer.writerow(
                {
                    "detection_id": d.id,
                    "filename": d.original_filename or "",
                    "file_type": d.file_type,
                    "upload_time": d.uploaded_at.isoformat() if d.uploaded_at else "",
                    "ai_probability": d.ai_probability if d.ai_probability is not None else "",
                    "confidence_score": d.confidence_score if d.confidence_score is not None else "",
                    "processing_time_ms": d.processing_time_ms if d.processing_time_ms is not None else "",
                    "status": d.processing_status,
                    "served_from_cache": getattr(d, "served_from_cache", False),
                    "error_message": d.error_message or "",
                }
            )
        return output.getvalue()

    def export_batch_as_json(self, batch, detections: list) -> dict:
        """Return a full batch export with nested detection details and summary stats."""
        completed = [d for d in detections if d.processing_status == "completed"]
        ai_probs = [d.ai_probability for d in completed if d.ai_probability is not None]
        ai_count = sum(1 for p in ai_probs if p >= 0.5)
        avg_conf = (
            round(
                sum(d.confidence_score for d in completed if d.confidence_score is not None)
                / len(completed),
                4,
            )
            if completed
            else 0.0
        )
        return {
            "batch_id": batch.id,
            "batch_name": batch.batch_name,
            "status": batch.status,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "summary": {
                "total_files": len(detections),
                "completed_files": len(completed),
                "failed_files": len(detections) - len(completed),
                "ai_detections": ai_count,
                "human_detections": len(completed) - ai_count,
                "confidence_avg": avg_conf,
            },
            "detections": [self.export_detection_as_json(d) for d in detections],
            "exported_at": datetime.utcnow().isoformat(),
        }

    def generate_pdf_report(self, batch, detections: list) -> bytes:
        """
        Generate a simple text-based PDF report.
        Requires the `reportlab` package; returns None if unavailable.
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
            from reportlab.lib import colors
        except ImportError:
            logger.warning("reportlab not installed — PDF export unavailable")
            return None

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # Title
        story.append(Paragraph(f"Batch Report: {batch.batch_name}", styles["Title"]))
        story.append(Spacer(1, 12))

        # Metadata
        meta = [
            ["Batch ID", str(batch.id)],
            ["Status", batch.status],
            ["Created", batch.created_at.isoformat() if batch.created_at else ""],
            ["Completed", batch.completed_at.isoformat() if batch.completed_at else "—"],
        ]
        t = Table(meta, colWidths=[140, 300])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
        story.append(t)
        story.append(Spacer(1, 20))

        # Detections table
        story.append(Paragraph("Detection Results", styles["Heading2"]))
        headers = ["ID", "Filename", "AI Prob", "Confidence", "Status"]
        rows = [headers]
        for d in detections:
            rows.append([
                str(d.id),
                (d.original_filename or "")[:40],
                f"{d.ai_probability:.2f}" if d.ai_probability is not None else "—",
                f"{d.confidence_score:.2f}" if d.confidence_score is not None else "—",
                d.processing_status,
            ])
        tbl = Table(rows, colWidths=[40, 180, 70, 70, 80])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        story.append(tbl)

        doc.build(story)
        return buffer.getvalue()


export_service = ExportService()
