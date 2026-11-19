"""Multi-tab Excel workpaper generator using Oat & Obsidian theme."""

import io
from datetime import UTC, date, datetime
from typing import Any, Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, NamedStyle, PatternFill, Side
from openpyxl.worksheet.worksheet import Worksheet

from security_utils import log_secure_operation
from shared.document_properties import save_workbook
from shared.excel_cells import as_date, put, put_ref
from shared.excel_exact import approximate_note, money
from shared.materiality_resolver import NOT_AVAILABLE, materiality_basis_label
from shared.monetary import quantize_monetary


class ExcelColors:
    """Oat & Obsidian theme colors for Excel workpapers."""

    # Core palette (RGB format for openpyxl)
    OBSIDIAN = "212121"
    OBSIDIAN_700 = "303030"
    OBSIDIAN_600 = "424242"
    OBSIDIAN_500 = "616161"

    OATMEAL = "EBE9E4"
    OATMEAL_300 = "DDD9D1"
    OATMEAL_400 = "C9C3B8"
    OATMEAL_500 = "B5AD9F"

    CLAY = "BC4749"
    CLAY_400 = "D16C6E"
    CLAY_600 = "A33D3F"

    SAGE = "4A7C59"
    SAGE_400 = "6FA882"
    SAGE_600 = "3D6649"

    WHITE = "FFFFFF"
    LIGHT_GRAY = "F5F4F2"


# Sprint 813: per-row styles hoisted out of the TB / anomaly loops — one object
# each instead of one per cell. openpyxl copies a style into the workbook's
# style table on assignment, so sharing the instances is safe.
_MATERIAL_ROW_FILL = PatternFill("solid", fgColor=ExcelColors.LIGHT_GRAY)
_MATERIAL_ROW_BORDER = Border(left=Side(style="thick", color=ExcelColors.CLAY))
_ANOMALY_REF_FONT = Font(color=ExcelColors.OBSIDIAN_500, size=9)
_MATERIAL_LABEL_FONT = Font(bold=True, color=ExcelColors.CLAY)
_IMMATERIAL_LABEL_FONT = Font(color=ExcelColors.OBSIDIAN_500)


def create_header_style() -> NamedStyle:
    """Create header row style with Obsidian background."""
    style = NamedStyle(name="header_style")
    style.font = Font(bold=True, color=ExcelColors.OATMEAL, size=11)
    style.fill = PatternFill("solid", fgColor=ExcelColors.OBSIDIAN)
    style.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    style.border = Border(bottom=Side(style="thin", color=ExcelColors.OATMEAL_400))
    return style


def create_title_style() -> NamedStyle:
    """Create title style for section headers."""
    style = NamedStyle(name="title_style")
    style.font = Font(bold=True, color=ExcelColors.OBSIDIAN, size=14)
    style.alignment = Alignment(horizontal="left", vertical="center")
    return style


def create_subtitle_style() -> NamedStyle:
    """Create subtitle style."""
    style = NamedStyle(name="subtitle_style")
    style.font = Font(color=ExcelColors.OBSIDIAN_500, size=10, italic=True)
    style.alignment = Alignment(horizontal="left", vertical="center")
    return style


def create_currency_style() -> NamedStyle:
    """Create currency format style."""
    style = NamedStyle(name="currency_style")
    style.number_format = '"$"#,##0.00'
    style.font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
    style.alignment = Alignment(horizontal="right")
    return style


def create_percent_style() -> NamedStyle:
    """Create percentage format style."""
    style = NamedStyle(name="percent_style")
    style.number_format = "0.00%"
    style.font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
    style.alignment = Alignment(horizontal="right")
    return style


def create_material_style() -> NamedStyle:
    """Create style for material anomalies (Clay accent)."""
    style = NamedStyle(name="material_style")
    style.font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
    style.fill = PatternFill("solid", fgColor=ExcelColors.LIGHT_GRAY)
    style.border = Border(left=Side(style="thick", color=ExcelColors.CLAY))
    return style


def create_immaterial_style() -> NamedStyle:
    """Create style for immaterial anomalies."""
    style = NamedStyle(name="immaterial_style")
    style.font = Font(color=ExcelColors.OBSIDIAN_500, size=10)
    style.fill = PatternFill("solid", fgColor=ExcelColors.LIGHT_GRAY)
    return style


def create_balanced_style() -> NamedStyle:
    """Create style for balanced status (Sage)."""
    style = NamedStyle(name="balanced_style")
    style.font = Font(bold=True, color=ExcelColors.SAGE, size=12)
    style.alignment = Alignment(horizontal="center")
    return style


def create_unbalanced_style() -> NamedStyle:
    """Create style for unbalanced status (Clay)."""
    style = NamedStyle(name="unbalanced_style")
    style.font = Font(bold=True, color=ExcelColors.CLAY, size=12)
    style.alignment = Alignment(horizontal="center")
    return style


class PaciolusWorkpaperGenerator:
    """Generates multi-tab Excel workpapers using BytesIO buffer."""

    def __init__(
        self,
        audit_result: dict[str, Any],
        filename: str = "workpaper",
        prepared_by: Optional[str] = None,
        reviewed_by: Optional[str] = None,
        workpaper_date: Optional[str | date] = None,
        include_signoff: bool = False,
    ):
        self.audit_result = audit_result
        self.filename = filename
        self.wb = Workbook()
        self.buffer = io.BytesIO()
        # Sprint 53: Workpaper fields (deprecated Sprint 7 — gated by include_signoff)
        self.prepared_by = prepared_by
        self.reviewed_by = reviewed_by
        # Sprint 885 (OUT-02): a real date (written as a date cell), never free text.
        self.workpaper_date = as_date(workpaper_date) or datetime.now().date()
        self.include_signoff = include_signoff

        # Remove default sheet (will create named sheets)
        self.wb.remove(self.wb.active)

        # Register styles
        self._register_styles()

        log_secure_operation("excel_generator_init", f"Initializing Excel workpaper for: {filename}")

    def _register_styles(self) -> None:
        """Register all named styles with the workbook."""
        styles = [
            create_header_style(),
            create_title_style(),
            create_subtitle_style(),
            create_currency_style(),
            create_percent_style(),
            create_material_style(),
            create_immaterial_style(),
            create_balanced_style(),
            create_unbalanced_style(),
        ]

        for style in styles:
            try:
                self.wb.add_named_style(style)
            except ValueError:
                # Style already exists
                pass

    def generate(self) -> bytes:
        """Generate the Excel workpaper. Returns bytes that can be streamed directly."""
        log_secure_operation("excel_generate_start", "Starting Excel generation")

        # Build all tabs
        self._build_summary_tab()
        self._build_standardized_tb_tab()
        self._build_anomalies_tab()
        self._build_ratios_tab()

        # Save to buffer
        author = self.prepared_by if self.include_signoff else None
        excel_bytes = save_workbook(self.wb, title="Trial Balance Diagnostic Workpaper", author=author)
        self.buffer.close()

        log_secure_operation("excel_generate_complete", f"Excel generated: {len(excel_bytes)} bytes")

        return excel_bytes

    def _build_summary_tab(self) -> None:
        """Build the Summary tab with executive overview."""
        ws = self.wb.create_sheet("Summary", 0)

        # Title
        put_ref(ws, "A1", "Paciolus Diagnostic Summary")
        ws["A1"].style = "title_style"
        ws.merge_cells("A1:D1")

        # Subtitle
        put_ref(ws, "A2", f"Analysis Intelligence Report for {self.filename}")
        ws["A2"].style = "subtitle_style"
        ws.merge_cells("A2:D2")

        # Timestamp
        put_ref(ws, "A3", f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        ws["A3"].font = Font(color=ExcelColors.OBSIDIAN_500, size=9, italic=True)

        # Balance Status
        is_balanced = self.audit_result.get("balanced", False)
        put_ref(ws, "A5", "Balance Status:")
        put_ref(ws, "B5", "BALANCED" if is_balanced else "OUT OF BALANCE")
        ws["B5"].style = "balanced_style" if is_balanced else "unbalanced_style"

        # Key Metrics Section
        put_ref(ws, "A7", "Key Metrics")
        ws["A7"].style = "title_style"
        ws.merge_cells("A7:B7")

        metrics = [
            ("Total Debits", self.audit_result.get("total_debits", 0), True),
            ("Total Credits", self.audit_result.get("total_credits", 0), True),
            ("Difference", self.audit_result.get("difference", 0), True),
            ("Rows Analyzed", self.audit_result.get("row_count", 0), False),
            ("Materiality Threshold", self.audit_result.get("materiality_threshold", 0), True),
            ("Material Anomalies", self.audit_result.get("material_count", 0), False),
            ("Immaterial Anomalies", self.audit_result.get("immaterial_count", 0), False),
        ]

        for i, (label, value, is_currency) in enumerate(metrics, start=9):
            put_ref(ws, f"A{i}", label)
            ws[f"A{i}"].font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
            put_ref(ws, f"B{i}", value)
            if is_currency:
                ws[f"B{i}"].style = "currency_style"
            else:
                ws[f"B{i}"].alignment = Alignment(horizontal="right")
            if label == "Materiality Threshold":
                # Sprint 886 (OUT-09): where the threshold came from, beside it.
                put_ref(ws, f"C{i}", self._materiality_label())
                ws[f"C{i}"].font = Font(color=ExcelColors.OBSIDIAN_500, size=9, italic=True)

        # Consolidated info if applicable
        if self.audit_result.get("is_consolidated"):
            row = len(metrics) + 10
            put_ref(ws, f"A{row}", "Sheets Consolidated")
            put_ref(ws, f"B{row}", self.audit_result.get("sheet_count", 0))

        # Sprint 53: Workpaper signoff section (deprecated Sprint 7 — gated by include_signoff)
        signoff_start = 17
        if self.include_signoff and (self.prepared_by or self.reviewed_by):
            put_ref(ws, f"A{signoff_start}", "Workpaper Sign-Off")
            ws[f"A{signoff_start}"].style = "title_style"
            ws.merge_cells(f"A{signoff_start}:B{signoff_start}")

            row = signoff_start + 1
            if self.prepared_by:
                put_ref(ws, f"A{row}", "Prepared By:")
                ws[f"A{row}"].font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
                put_ref(ws, f"B{row}", self.prepared_by)
                put_ref(ws, f"C{row}", self.workpaper_date)
                row += 1

            if self.reviewed_by:
                put_ref(ws, f"A{row}", "Reviewed By:")
                ws[f"A{row}"].font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
                put_ref(ws, f"B{row}", self.reviewed_by)
                put_ref(ws, f"C{row}", self.workpaper_date)
                row += 1

            disclaimer_start = row + 2
        else:
            disclaimer_start = 20

        # Legal disclaimer
        put_ref(
            ws,
            f"A{disclaimer_start}",
            "DISCLAIMER: This output is generated by an automated analytical system and supports",
        )
        put_ref(
            ws,
            f"A{disclaimer_start + 1}",
            "internal evaluation and professional judgment. It does not constitute an audit, review,",
        )
        put_ref(ws, f"A{disclaimer_start + 2}", "or attestation engagement and provides no assurance.")
        for row in [disclaimer_start, disclaimer_start + 1, disclaimer_start + 2]:
            ws[f"A{row}"].font = Font(color=ExcelColors.OBSIDIAN_500, size=8, italic=True)

        # Column widths
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 20
        ws.column_dimensions["C"].width = 15
        ws.column_dimensions["D"].width = 15

    def _build_standardized_tb_tab(self) -> None:
        """Build the Trial Balance tab: every account once, totals from its rows.

        Sprint 884 (OUT-04): this tab ("Standardized TB") used to list only the
        flagged accounts — one row per flag — above the full ledger's debit and
        credit totals. It now lists every account in ``all_accounts`` once,
        marks the flagged ones, and totals the rows as shown (half-up to cents).
        The flags themselves are on the "Flagged Accounts" tab.
        """
        ws = self.wb.create_sheet("Trial Balance", 1)

        # Title
        put_ref(ws, "A1", "Trial Balance")
        ws["A1"].style = "title_style"
        ws.merge_cells("A1:F1")

        all_accounts = [a for a in (self.audit_result.get("all_accounts") or []) if isinstance(a, dict)]
        if not all_accounts:
            put_ref(
                ws,
                "A3",
                "The full account list was not supplied with this export, so the trial balance is not shown. "
                "Re-export from the analysis to include it. Flagged accounts are on the Flagged Accounts tab.",
            )
            ws["A3"].alignment = Alignment(wrap_text=True)
            ws.merge_cells("A3:F3")
            ws.column_dimensions["A"].width = 35
            return

        # Headers
        headers = ["Account", "Category", "Debit", "Credit", "Net", "Flagged"]
        for col, header in enumerate(headers, start=1):
            cell = put(ws, 3, col, header)
            cell.style = "header_style"

        flag_counts: dict[str, int] = {}
        material_accounts: set[str] = set()
        for ab in self.audit_result.get("abnormal_balances", []) or []:
            if isinstance(ab, dict):
                name = ab.get("account", "Unknown")
                flag_counts[name] = flag_counts.get(name, 0) + 1
                if ab.get("materiality") == "material":
                    material_accounts.add(name)

        total_debit = total_credit = total_net = quantize_monetary(0)
        row = 4
        for acct in all_accounts:
            name = acct.get("account", "Unknown")
            debit = quantize_monetary(acct.get("debit"))
            credit = quantize_monetary(acct.get("credit"))
            net = debit - credit
            total_debit += debit
            total_credit += credit
            total_net += net

            put(ws, row, 1, name)
            put(ws, row, 2, acct.get("type", "Unknown"))
            for col, value in ((3, debit), (4, credit), (5, net)):
                put(ws, row, col, float(value)).style = "currency_style"
            count = flag_counts.get(name, 0)
            if count:
                put(ws, row, 6, f"Yes ({count})")

            # Material flags keep their row highlight.
            if name in material_accounts:
                for col in range(1, 7):
                    ws.cell(row=row, column=col).fill = _MATERIAL_ROW_FILL
                ws.cell(row=row, column=1).border = _MATERIAL_ROW_BORDER

            row += 1

        # Totals row — the sum of the rows above it.
        row += 1
        put(ws, row, 1, "TOTALS")
        ws.cell(row=row, column=1).font = Font(bold=True)
        for col, value in ((3, total_debit), (4, total_credit), (5, total_net)):
            cell = put(ws, row, col, float(value))
            cell.style = "currency_style"
            cell.font = Font(bold=True)

        # Column widths
        ws.column_dimensions["A"].width = 35
        ws.column_dimensions["B"].width = 15
        ws.column_dimensions["C"].width = 15
        ws.column_dimensions["D"].width = 15
        ws.column_dimensions["E"].width = 15
        ws.column_dimensions["F"].width = 15

    def _write_flag_subtotal(self, ws: Worksheet, row: int, label: str, amount: Any) -> None:
        """Sprint 884 (OUT-04): a labelled subtotal under the Amount column."""
        put(ws, row, 1, label).font = Font(bold=True)
        cell = put(ws, row, 5, float(amount))
        cell.style = "currency_style"
        cell.font = Font(bold=True)

    def _build_anomalies_tab(self) -> None:
        """Build the Flagged Accounts tab: one row per flag, with subtotals.

        Sprint 884 (OUT-04): renamed from "Flagged Anomalies"; each section
        ends with a subtotal of its rows as shown, and a total of both
        sections follows. An account flagged twice appears twice here — once
        per flag — and once on the Trial Balance tab.
        """
        ws = self.wb.create_sheet("Flagged Accounts", 2)

        # Title
        put_ref(ws, "A1", "Flagged Accounts")
        ws["A1"].style = "title_style"
        ws.merge_cells("A1:G1")  # Sprint 53: Extended for Ref column

        # Subtitle
        put_ref(
            ws,
            "A2",
            f"Materiality Threshold: ${self.audit_result.get('materiality_threshold', 0):,.2f}"
            f" ({self._materiality_label()})",
        )
        ws["A2"].style = "subtitle_style"

        # Headers - Sprint 53: Added Ref column
        headers = ["Ref", "Account", "Type", "Issue", "Amount", "Severity", "Classification"]
        for col, header in enumerate(headers, start=1):
            cell = put(ws, 4, col, header)
            cell.style = "header_style"

        abnormal_balances = self.audit_result.get("abnormal_balances", [])

        # Separate material and immaterial
        material = [ab for ab in abnormal_balances if ab.get("materiality") == "material"]
        immaterial = [ab for ab in abnormal_balances if ab.get("materiality") == "immaterial"]

        row = 5
        material_subtotal = immaterial_subtotal = quantize_monetary(0)

        # Material anomalies section
        if material:
            put(ws, row, 1, f"MATERIAL RISKS ({len(material)})")
            ws.cell(row=row, column=1).font = Font(bold=True, color=ExcelColors.CLAY, size=11)
            ws.merge_cells(f"A{row}:G{row}")  # Sprint 53: Extended
            row += 1

            for idx, ab in enumerate(material, start=1):
                # Sprint 53: Reference number
                ref_num = f"TB-M{idx:03d}"
                put(ws, row, 1, ref_num)
                ws.cell(row=row, column=1).font = _ANOMALY_REF_FONT
                put(ws, row, 2, ab.get("account", "Unknown"))
                put(ws, row, 3, ab.get("type", "Unknown"))
                put(ws, row, 4, ab.get("issue", ""))
                ws.cell(row=row, column=4).alignment = Alignment(wrap_text=True)
                amount = quantize_monetary(ab.get("amount"))
                material_subtotal += amount
                put(ws, row, 5, float(amount))
                ws.cell(row=row, column=5).style = "currency_style"
                put(ws, row, 6, ab.get("severity", "unknown").upper())
                put(ws, row, 7, "MATERIAL")
                ws.cell(row=row, column=7).font = _MATERIAL_LABEL_FONT

                # Apply material styling
                ws.cell(row=row, column=2).border = _MATERIAL_ROW_BORDER
                for col in range(1, 8):
                    ws.cell(row=row, column=col).fill = _MATERIAL_ROW_FILL

                row += 1

            self._write_flag_subtotal(ws, row, "Subtotal — material", material_subtotal)
            row += 2  # Subtotal + spacer

        # Immaterial anomalies section
        if immaterial:
            put(ws, row, 1, f"IMMATERIAL ITEMS ({len(immaterial)})")
            ws.cell(row=row, column=1).font = Font(bold=True, color=ExcelColors.OBSIDIAN_500, size=11)
            ws.merge_cells(f"A{row}:G{row}")  # Sprint 53: Extended
            row += 1

            for idx, ab in enumerate(immaterial, start=1):
                # Sprint 53: Reference number
                ref_num = f"TB-I{idx:03d}"
                put(ws, row, 1, ref_num)
                ws.cell(row=row, column=1).font = _ANOMALY_REF_FONT
                put(ws, row, 2, ab.get("account", "Unknown"))
                put(ws, row, 3, ab.get("type", "Unknown"))
                put(ws, row, 4, ab.get("issue", ""))
                ws.cell(row=row, column=4).alignment = Alignment(wrap_text=True)
                amount = quantize_monetary(ab.get("amount"))
                immaterial_subtotal += amount
                put(ws, row, 5, float(amount))
                ws.cell(row=row, column=5).style = "currency_style"
                put(ws, row, 6, ab.get("severity", "unknown").upper())
                put(ws, row, 7, "IMMATERIAL")
                ws.cell(row=row, column=7).font = _IMMATERIAL_LABEL_FONT

                row += 1

            self._write_flag_subtotal(ws, row, "Subtotal — immaterial", immaterial_subtotal)
            row += 2

        if material or immaterial:
            self._write_flag_subtotal(ws, row, "Total — all flags", material_subtotal + immaterial_subtotal)

        # If no anomalies
        if not material and not immaterial:
            put(ws, row, 1, "No anomalies detected. Trial balance appears healthy.")
            ws.cell(row=row, column=1).font = Font(color=ExcelColors.SAGE, size=11, italic=True)
            ws.merge_cells(f"A{row}:F{row}")

        # Column widths
        ws.column_dimensions["A"].width = 35
        ws.column_dimensions["B"].width = 15
        ws.column_dimensions["C"].width = 45
        ws.column_dimensions["D"].width = 15
        ws.column_dimensions["E"].width = 12
        ws.column_dimensions["F"].width = 15

    def _materiality_label(self) -> str:
        """Sprint 886 (OUT-09/16): the threshold's purpose and origin, as the PDF prints them."""
        return materiality_basis_label(
            self.audit_result.get("materiality_basis"), self.audit_result.get("materiality_source")
        )

    def _build_ratios_tab(self) -> None:
        """Build the Key Ratios tab with financial ratio analysis."""
        ws = self.wb.create_sheet("Key Ratios", 3)

        # Title
        put_ref(ws, "A1", "Key Financial Ratios")
        ws["A1"].style = "title_style"
        ws.merge_cells("A1:D1")

        # Subtitle
        put_ref(ws, "A2", "Based on standardized trial balance categories")
        ws["A2"].style = "subtitle_style"

        # Headers
        headers = ["Ratio", "Value", "Health Status", "Interpretation"]
        for col, header in enumerate(headers, start=1):
            cell = put(ws, 4, col, header)
            cell.style = "header_style"

        # Sprint 886 (OUT-09): analytics absent from the request is "Not available",
        # never "insufficient data" or $0.
        analytics = self.audit_result.get("analytics")
        supplied = analytics is not None
        analytics = analytics or {}
        ratios = analytics.get("ratios", {})

        row = 5

        # Define ratio display info
        ratio_definitions = [
            ("current_ratio", "Current Ratio", "Current Assets / Current Liabilities"),
            ("quick_ratio", "Quick Ratio", "(Current Assets - Inventory) / Current Liabilities"),
            ("debt_to_equity", "Debt-to-Equity", "Total Liabilities / Total Equity"),
            ("gross_margin", "Gross Margin", "(Revenue - COGS) / Revenue"),
        ]

        for ratio_key, ratio_name, formula in ratio_definitions:
            ratio_data = ratios.get(ratio_key, {})

            put(ws, row, 1, ratio_name)
            ws.cell(row=row, column=1).font = Font(bold=True, color=ExcelColors.OBSIDIAN)

            value = ratio_data.get("value")
            if value is not None:
                # Sprint 886 (OUT-09): format by the ratio's declared unit, so the cell
                # reads as the screen's display value. No unit (an analysis from before
                # units existed): the screen's text, never a guess from the value's size.
                unit = ratio_data.get("unit")
                if unit in _RATIO_NUMBER_FORMATS:
                    put(ws, row, 2, value / 100 if unit == "percent" else value)
                    ws.cell(row=row, column=2).number_format = _RATIO_NUMBER_FORMATS[unit]
                else:
                    put(ws, row, 2, ratio_data.get("display_value") or NOT_AVAILABLE)
                ws.cell(row=row, column=2).alignment = Alignment(horizontal="right")

                # Threshold status with color
                threshold = ratio_data.get("threshold_status", "neutral")
                put(ws, row, 3, threshold.upper().replace("_", " "))
                if threshold == "above_threshold":
                    ws.cell(row=row, column=3).font = Font(bold=True, color=ExcelColors.SAGE)
                elif threshold == "at_threshold":
                    ws.cell(row=row, column=3).font = Font(bold=True, color=ExcelColors.OATMEAL_500)
                elif threshold == "below_threshold":
                    ws.cell(row=row, column=3).font = Font(bold=True, color=ExcelColors.CLAY)

                # Interpretation
                put(ws, row, 4, ratio_data.get("interpretation", ""))
                ws.cell(row=row, column=4).alignment = Alignment(wrap_text=True)
            elif not supplied:
                put(ws, row, 2, NOT_AVAILABLE)
                ws.cell(row=row, column=2).font = Font(color=ExcelColors.OBSIDIAN_500, italic=True)
                put(ws, row, 3, "-")
                put(ws, row, 4, "Ratios were not included in the analysis results this export was made from")
                ws.cell(row=row, column=4).font = Font(color=ExcelColors.OBSIDIAN_500, italic=True)
            else:
                put(ws, row, 2, "N/A")
                ws.cell(row=row, column=2).font = Font(color=ExcelColors.OBSIDIAN_500, italic=True)
                put(ws, row, 3, "-")
                put(ws, row, 4, "Insufficient data to calculate")
                ws.cell(row=row, column=4).font = Font(color=ExcelColors.OBSIDIAN_500, italic=True)

            # Add formula note below
            row += 1
            put(ws, row, 1, f"  Formula: {formula}")
            ws.cell(row=row, column=1).font = Font(color=ExcelColors.OBSIDIAN_500, size=9, italic=True)
            ws.merge_cells(f"A{row}:D{row}")

            row += 2  # Spacer

        # Sprint 832: equity-basis disclosure beside the ratios that use equity.
        equity_note = analytics.get("equity_basis_note")
        if equity_note:
            put(ws, row, 1, equity_note)
            ws.cell(row=row, column=1).font = Font(color=ExcelColors.OBSIDIAN_500, size=9, italic=True)
            ws.cell(row=row, column=1).alignment = Alignment(wrap_text=True)
            ws.merge_cells(f"A{row}:D{row}")
            row += 1

        # Category totals section
        row += 2
        put(ws, row, 1, "Category Totals (Used in Calculations)")
        ws.cell(row=row, column=1).style = "title_style"
        ws.merge_cells(f"A{row}:D{row}")

        row += 2
        category_totals = analytics.get("category_totals", {})
        categories = [
            ("total_assets", "Total Assets"),
            ("current_assets", "Current Assets"),
            ("inventory", "Inventory"),
            ("total_liabilities", "Total Liabilities"),
            ("current_liabilities", "Current Liabilities"),
            ("total_equity", "Total Equity"),
            ("total_revenue", "Total Revenue"),
            ("cost_of_goods_sold", "Cost of Goods Sold"),
            ("total_expenses", "Total Expenses"),
        ]

        for key, label in categories:
            put(ws, row, 1, label)
            ws.cell(row=row, column=1).font = Font(color=ExcelColors.OBSIDIAN_600)
            total = category_totals.get(key)
            if total is None:
                put(ws, row, 2, NOT_AVAILABLE)
                ws.cell(row=row, column=2).font = Font(color=ExcelColors.OBSIDIAN_500, italic=True)
            else:
                put(ws, row, 2, total)
                ws.cell(row=row, column=2).style = "currency_style"
            row += 1

        # Column widths
        ws.column_dimensions["A"].width = 25
        ws.column_dimensions["B"].width = 15
        ws.column_dimensions["C"].width = 15
        ws.column_dimensions["D"].width = 50


# Sprint 886 (OUT-09): Excel number format per ratio unit (ratio_engine.RATIO_UNITS),
# each matching the screen's display_value ("2.25", "40.0%", "3.10x", "45 days").
_RATIO_NUMBER_FORMATS = {
    "ratio": "0.00",
    "percent": "0.0%",
    "times": '0.00"x"',
    "days": '0" days"',
}


def _fs_amount(ws: Worksheet, row: int, value: Any, label: str) -> None:
    """Write a statement amount in column B, exactly.

    Sprint 884 (TQ-12, OUT-19): the amount is a Decimal at cents (written digit
    for digit, see shared/excel_exact.py). Where it has more than the 15
    significant digits Excel keeps, column D carries an exact text copy and
    says the number in column B is approximate.
    """
    amount = money(value)
    put(ws, row, 2, amount)
    note = approximate_note([(str(label).strip(), amount)]) if amount is not None else None
    if note:
        put(ws, row, 4, note)


def generate_financial_statements_excel(
    statements: Any,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str | date] = None,
    include_signoff: bool = False,
) -> bytes:
    """
    Generate an Excel workbook with Balance Sheet and Income Statement tabs.

    Sprint 71: Financial Statements Excel using Oat & Obsidian theme.

    Args:
        statements: FinancialStatements dataclass from FinancialStatementBuilder
        prepared_by: Name of preparer (deprecated — ignored unless include_signoff=True)
        reviewed_by: Name of reviewer (deprecated — ignored unless include_signoff=True)
        workpaper_date: Date for workpaper signoff (deprecated — ignored unless include_signoff=True)
        include_signoff: If True, render signoff section (default False since Sprint 7)
    """
    wb = Workbook()
    wb.remove(wb.active)

    # Register styles
    for style_fn in [
        create_header_style,
        create_title_style,
        create_subtitle_style,
        create_currency_style,
        create_balanced_style,
        create_unbalanced_style,
    ]:
        try:
            wb.add_named_style(style_fn())
        except ValueError:
            pass

    def _write_statement_sheet(ws: Worksheet, title: str, line_items: Any, sheet_index: int) -> int:
        """Write a financial statement to a worksheet."""
        # Title
        put_ref(ws, "A1", title)
        ws["A1"].style = "title_style"
        ws.merge_cells("A1:C1")

        # Entity name
        entity = statements.entity_name or ""
        if entity:
            put_ref(ws, "A2", entity)
            ws["A2"].style = "subtitle_style"
            ws.merge_cells("A2:C2")

        # Period
        if statements.period_end:
            put_ref(ws, "A3", f"Period Ending: {statements.period_end}")
            ws["A3"].font = Font(color=ExcelColors.OBSIDIAN_500, size=9, italic=True)

        # Timestamp
        put_ref(ws, "A4", f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
        ws["A4"].font = Font(color=ExcelColors.OBSIDIAN_500, size=9, italic=True)

        row = 6
        for item in line_items:
            # Column A: label (with indentation, sanitized for formula injection)
            indent = "    " * item.indent_level
            label = f"{indent}{item.label}"

            put(ws, row, 1, label)

            # Style based on line type
            if item.is_total:
                ws.cell(row=row, column=1).font = Font(bold=True, color=ExcelColors.OBSIDIAN, size=11)
                ws.cell(row=row, column=2).font = Font(bold=True, color=ExcelColors.OBSIDIAN, size=11)
                ws.cell(row=row, column=2).number_format = '"$"#,##0.00'
                ws.cell(row=row, column=2).border = Border(bottom=Side(style="double", color=ExcelColors.OBSIDIAN))
                _fs_amount(ws, row, item.amount, item.label)
            elif item.is_subtotal:
                ws.cell(row=row, column=1).font = Font(bold=True, color=ExcelColors.OBSIDIAN_600, size=10)
                ws.cell(row=row, column=2).font = Font(bold=True, color=ExcelColors.OBSIDIAN_600, size=10)
                ws.cell(row=row, column=2).number_format = '"$"#,##0.00'
                ws.cell(row=row, column=2).border = Border(top=Side(style="thin", color=ExcelColors.OBSIDIAN_500))
                _fs_amount(ws, row, item.amount, item.label)
            elif item.indent_level == 0 and not item.lead_sheet_ref:
                # Section header — no amount
                ws.cell(row=row, column=1).font = Font(bold=True, color=ExcelColors.OBSIDIAN, size=10)
                ws.cell(row=row, column=1).fill = PatternFill("solid", fgColor=ExcelColors.OATMEAL)
            else:
                # Regular line item
                ws.cell(row=row, column=1).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
                _fs_amount(ws, row, item.amount, item.label)
                ws.cell(row=row, column=2).number_format = '"$"#,##0.00'
                ws.cell(row=row, column=2).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)

            # Column C: lead sheet reference
            if item.lead_sheet_ref:
                put(ws, row, 3, item.lead_sheet_ref)
                ws.cell(row=row, column=3).font = Font(color=ExcelColors.OBSIDIAN_500, size=8, italic=True)
                ws.cell(row=row, column=3).alignment = Alignment(horizontal="center")

            row += 1

        return row

    # ── Balance Sheet tab ──
    bs_ws = wb.create_sheet("Balance Sheet", 0)
    end_row = _write_statement_sheet(bs_ws, "Balance Sheet", statements.balance_sheet, 0)

    # Balance verification row
    end_row += 1
    if statements.is_balanced:
        put(bs_ws, end_row, 1, "✓ BALANCED")
        bs_ws.cell(row=end_row, column=1).style = "balanced_style"
    else:
        put(bs_ws, end_row, 1, f"⚠ OUT OF BALANCE (${statements.balance_difference:,.2f})")
        bs_ws.cell(row=end_row, column=1).style = "unbalanced_style"
    bs_ws.merge_cells(f"A{end_row}:C{end_row}")

    # Workpaper signoff (deprecated Sprint 7 — gated by include_signoff)
    if include_signoff and (prepared_by or reviewed_by):
        end_row += 2
        wp_date = as_date(workpaper_date) or datetime.now().date()
        put(bs_ws, end_row, 1, "Workpaper Sign-Off")
        bs_ws.cell(row=end_row, column=1).style = "title_style"
        end_row += 1
        if prepared_by:
            put(bs_ws, end_row, 1, "Prepared By:")
            bs_ws.cell(row=end_row, column=1).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
            put(bs_ws, end_row, 2, prepared_by)
            put(bs_ws, end_row, 3, wp_date)
            end_row += 1
        if reviewed_by:
            put(bs_ws, end_row, 1, "Reviewed By:")
            bs_ws.cell(row=end_row, column=1).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
            put(bs_ws, end_row, 2, reviewed_by)
            put(bs_ws, end_row, 3, wp_date)

    bs_ws.column_dimensions["A"].width = 40
    bs_ws.column_dimensions["B"].width = 18
    bs_ws.column_dimensions["C"].width = 8

    # ── Income Statement tab ──
    is_ws = wb.create_sheet("Income Statement", 1)
    _write_statement_sheet(is_ws, "Income Statement", statements.income_statement, 1)

    is_ws.column_dimensions["A"].width = 40
    is_ws.column_dimensions["B"].width = 18
    is_ws.column_dimensions["C"].width = 8

    # ── Cash Flow Statement tab (Sprint 84) ──
    if statements.cash_flow_statement is not None:
        cf = statements.cash_flow_statement
        cf_ws = wb.create_sheet("Cash Flow Statement", 2)

        # Title
        put_ref(cf_ws, "A1", "Cash Flow Statement (Indirect Method)")
        cf_ws["A1"].style = "title_style"
        cf_ws.merge_cells("A1:C1")

        entity_cf = statements.entity_name or ""
        if entity_cf:
            put_ref(cf_ws, "A2", entity_cf)
            cf_ws["A2"].style = "subtitle_style"
            cf_ws.merge_cells("A2:C2")

        if statements.period_end:
            put_ref(cf_ws, "A3", f"Period Ending: {statements.period_end}")
            cf_ws["A3"].font = Font(color=ExcelColors.OBSIDIAN_500, size=9, italic=True)

        put_ref(cf_ws, "A4", f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
        cf_ws["A4"].font = Font(color=ExcelColors.OBSIDIAN_500, size=9, italic=True)

        row = 6
        for section in [cf.operating, cf.investing, cf.financing]:
            # Section header
            put(cf_ws, row, 1, section.label)
            cf_ws.cell(row=row, column=1).font = Font(bold=True, color=ExcelColors.OBSIDIAN, size=10)
            cf_ws.cell(row=row, column=1).fill = PatternFill("solid", fgColor=ExcelColors.OATMEAL)
            row += 1

            # Line items
            for item in section.items:
                indent = "    " * item.indent_level
                put(cf_ws, row, 1, f"{indent}{item.label}")
                cf_ws.cell(row=row, column=1).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
                _fs_amount(cf_ws, row, item.amount, item.label)
                cf_ws.cell(row=row, column=2).number_format = '"$"#,##0.00'
                cf_ws.cell(row=row, column=2).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
                if item.source:
                    put(cf_ws, row, 3, item.source)
                    cf_ws.cell(row=row, column=3).font = Font(color=ExcelColors.OBSIDIAN_500, size=8, italic=True)
                    cf_ws.cell(row=row, column=3).alignment = Alignment(horizontal="center")
                row += 1

            # Section subtotal
            put(cf_ws, row, 1, f"    Net {section.label}")
            cf_ws.cell(row=row, column=1).font = Font(bold=True, color=ExcelColors.OBSIDIAN_600, size=10)
            _fs_amount(cf_ws, row, section.subtotal, f"Net {section.label}")
            cf_ws.cell(row=row, column=2).font = Font(bold=True, color=ExcelColors.OBSIDIAN_600, size=10)
            cf_ws.cell(row=row, column=2).number_format = '"$"#,##0.00'
            cf_ws.cell(row=row, column=2).border = Border(top=Side(style="thin", color=ExcelColors.OBSIDIAN_500))
            row += 2

        # Net Change in Cash
        put(cf_ws, row, 1, "NET CHANGE IN CASH")
        cf_ws.cell(row=row, column=1).font = Font(bold=True, color=ExcelColors.OBSIDIAN, size=11)
        _fs_amount(cf_ws, row, cf.net_change, "Net change in cash")
        cf_ws.cell(row=row, column=2).font = Font(bold=True, color=ExcelColors.OBSIDIAN, size=11)
        cf_ws.cell(row=row, column=2).number_format = '"$"#,##0.00'
        cf_ws.cell(row=row, column=2).border = Border(bottom=Side(style="double", color=ExcelColors.OBSIDIAN))
        row += 2

        # Reconciliation
        if cf.has_prior_period:
            put(cf_ws, row, 1, "Reconciliation")
            cf_ws.cell(row=row, column=1).font = Font(bold=True, color=ExcelColors.OBSIDIAN, size=10)
            cf_ws.cell(row=row, column=1).fill = PatternFill("solid", fgColor=ExcelColors.OATMEAL)
            row += 1

            put(cf_ws, row, 1, "    Beginning Cash")
            cf_ws.cell(row=row, column=1).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
            _fs_amount(cf_ws, row, cf.beginning_cash, "Beginning cash")
            cf_ws.cell(row=row, column=2).number_format = '"$"#,##0.00'
            cf_ws.cell(row=row, column=2).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
            row += 1

            put(cf_ws, row, 1, "    Net Change in Cash")
            cf_ws.cell(row=row, column=1).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
            _fs_amount(cf_ws, row, cf.net_change, "Net change in cash")
            cf_ws.cell(row=row, column=2).number_format = '"$"#,##0.00'
            cf_ws.cell(row=row, column=2).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
            row += 1

            put(cf_ws, row, 1, "ENDING CASH")
            cf_ws.cell(row=row, column=1).font = Font(bold=True, color=ExcelColors.OBSIDIAN, size=11)
            _fs_amount(cf_ws, row, cf.ending_cash, "Ending cash")
            cf_ws.cell(row=row, column=2).font = Font(bold=True, color=ExcelColors.OBSIDIAN, size=11)
            cf_ws.cell(row=row, column=2).number_format = '"$"#,##0.00'
            cf_ws.cell(row=row, column=2).border = Border(bottom=Side(style="double", color=ExcelColors.OBSIDIAN))
            row += 2

            # Reconciliation status
            if cf.is_reconciled:
                put(cf_ws, row, 1, "✓ RECONCILED")
                cf_ws.cell(row=row, column=1).style = "balanced_style"
            else:
                put(cf_ws, row, 1, f"⚠ UNRECONCILED (${cf.reconciliation_difference:,.2f})")
                cf_ws.cell(row=row, column=1).style = "unbalanced_style"
            cf_ws.merge_cells(f"A{row}:C{row}")
            row += 1

        # Notes
        if cf.notes:
            row += 1
            for note in cf.notes:
                put(cf_ws, row, 1, f"Note: {note}")
                cf_ws.cell(row=row, column=1).font = Font(color=ExcelColors.OBSIDIAN_500, size=9, italic=True)
                row += 1

        cf_ws.column_dimensions["A"].width = 40
        cf_ws.column_dimensions["B"].width = 18
        cf_ws.column_dimensions["C"].width = 8

    # ── Mapping Trace tab (Sprint 284) ──
    if statements.mapping_trace:
        mt_ws = wb.create_sheet("Mapping Trace", 3)

        # Title
        put_ref(mt_ws, "A1", "Account-to-Statement Mapping Trace")
        mt_ws["A1"].style = "title_style"
        mt_ws.merge_cells("A1:H1")

        entity_mt = statements.entity_name or ""
        if entity_mt:
            put_ref(mt_ws, "A2", entity_mt)
            mt_ws["A2"].style = "subtitle_style"
            mt_ws.merge_cells("A2:H2")

        if statements.period_end:
            put_ref(mt_ws, "A3", f"Period Ending: {statements.period_end}")
            mt_ws["A3"].font = Font(color=ExcelColors.OBSIDIAN_500, size=9, italic=True)

        put_ref(mt_ws, "A4", f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
        mt_ws["A4"].font = Font(color=ExcelColors.OBSIDIAN_500, size=9, italic=True)

        # Header row
        row = 6
        headers = ["Statement", "Line Item", "Ref", "Account", "Debit", "Credit", "Net", "Tied"]
        for col_idx, header in enumerate(headers, 1):
            cell = put(mt_ws, row, col_idx, header)
            cell.font = Font(bold=True, color=ExcelColors.OATMEAL, size=10)
            cell.fill = PatternFill("solid", fgColor=ExcelColors.OBSIDIAN)
            cell.alignment = Alignment(horizontal="center", vertical="center")
        row += 1

        for entry in statements.mapping_trace:
            first_row = True
            if entry.account_count > 0 and entry.accounts:
                for acct in entry.accounts:
                    if first_row:
                        put(mt_ws, row, 1, entry.statement)
                        mt_ws.cell(row=row, column=1).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
                        put(mt_ws, row, 2, entry.line_label)
                        mt_ws.cell(row=row, column=2).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
                        put(mt_ws, row, 3, entry.lead_sheet_ref)
                        mt_ws.cell(row=row, column=3).font = Font(color=ExcelColors.OBSIDIAN_500, size=9)
                        mt_ws.cell(row=row, column=3).alignment = Alignment(horizontal="center")
                        first_row = False

                    put(mt_ws, row, 4, acct.account_name)
                    mt_ws.cell(row=row, column=4).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
                    put(mt_ws, row, 5, acct.debit)
                    mt_ws.cell(row=row, column=5).number_format = '"$"#,##0.00'
                    mt_ws.cell(row=row, column=5).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
                    put(mt_ws, row, 6, acct.credit)
                    mt_ws.cell(row=row, column=6).number_format = '"$"#,##0.00'
                    mt_ws.cell(row=row, column=6).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
                    put(mt_ws, row, 7, acct.net_balance)
                    mt_ws.cell(row=row, column=7).number_format = '"$"#,##0.00'
                    mt_ws.cell(row=row, column=7).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
                    row += 1

                # Subtotal row
                put(mt_ws, row, 2, f"Subtotal: {entry.line_label}")
                mt_ws.cell(row=row, column=2).font = Font(bold=True, color=ExcelColors.OBSIDIAN_600, size=10)
                put(mt_ws, row, 7, entry.statement_amount)
                mt_ws.cell(row=row, column=7).number_format = '"$"#,##0.00'
                mt_ws.cell(row=row, column=7).font = Font(bold=True, color=ExcelColors.OBSIDIAN_600, size=10)
                mt_ws.cell(row=row, column=7).border = Border(top=Side(style="thin", color=ExcelColors.OBSIDIAN_500))

                # Tied indicator
                if entry.is_tied:
                    put(mt_ws, row, 8, "✓")
                    mt_ws.cell(row=row, column=8).font = Font(color=ExcelColors.SAGE, size=10, bold=True)
                else:
                    put(mt_ws, row, 8, "⚠")
                    mt_ws.cell(row=row, column=8).font = Font(color=ExcelColors.CLAY, size=10, bold=True)
                mt_ws.cell(row=row, column=8).alignment = Alignment(horizontal="center")
                row += 1
            else:
                # Empty lead sheet — single row
                put(mt_ws, row, 1, entry.statement)
                mt_ws.cell(row=row, column=1).font = Font(color=ExcelColors.OBSIDIAN_600, size=10)
                put(mt_ws, row, 2, entry.line_label)
                mt_ws.cell(row=row, column=2).font = Font(color=ExcelColors.OBSIDIAN_500, size=10, italic=True)
                put(mt_ws, row, 3, entry.lead_sheet_ref)
                mt_ws.cell(row=row, column=3).font = Font(color=ExcelColors.OBSIDIAN_500, size=9)
                mt_ws.cell(row=row, column=3).alignment = Alignment(horizontal="center")
                put(mt_ws, row, 7, 0.0)
                mt_ws.cell(row=row, column=7).number_format = '"$"#,##0.00'
                put(mt_ws, row, 8, "✓")
                mt_ws.cell(row=row, column=8).font = Font(color=ExcelColors.SAGE, size=10, bold=True)
                mt_ws.cell(row=row, column=8).alignment = Alignment(horizontal="center")
                row += 1

        mt_ws.column_dimensions["A"].width = 16
        mt_ws.column_dimensions["B"].width = 30
        mt_ws.column_dimensions["C"].width = 6
        mt_ws.column_dimensions["D"].width = 35
        mt_ws.column_dimensions["E"].width = 15
        mt_ws.column_dimensions["F"].width = 15
        mt_ws.column_dimensions["G"].width = 15
        mt_ws.column_dimensions["H"].width = 8

    # Save
    excel_bytes = save_workbook(wb, title="Financial Statements", author=prepared_by if include_signoff else None)

    log_secure_operation(
        "financial_statements_excel_complete", f"Financial statements Excel generated: {len(excel_bytes)} bytes"
    )

    return excel_bytes


def generate_workpaper(
    audit_result: dict[str, Any],
    filename: str = "workpaper",
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str | date] = None,
    include_signoff: bool = False,
) -> bytes:
    """
    Generate an Excel workpaper from audit results.

    Sprint 53: Added workpaper fields for professional documentation.
    Sprint 7: Signoff deprecated — gated by include_signoff (default False).

    Args:
        audit_result: The audit result dictionary
        filename: Base filename for the workpaper
        prepared_by: Name of preparer (deprecated — ignored unless include_signoff=True)
        reviewed_by: Name of reviewer (deprecated — ignored unless include_signoff=True)
        workpaper_date: Date for workpaper signoff (deprecated — ignored unless include_signoff=True)
        include_signoff: If True, render signoff section (default False since Sprint 7)
    """
    generator = PaciolusWorkpaperGenerator(
        audit_result,
        filename,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        include_signoff=include_signoff,
    )
    return generator.generate()
