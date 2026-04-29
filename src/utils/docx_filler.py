"""Fill the Vietcombank LC application DOCX template with extracted LC data."""
from __future__ import annotations
import re
import shutil
from pathlib import Path
from typing import Optional
from docx import Document
from docx.oxml.ns import qn


# ─── Low-level paragraph helpers ────────────────────────────────────────────

def _full_text(para) -> str:
    return "".join(r.text for r in para.runs)


def _set_para_text(para, new_text: str) -> None:
    """Replace paragraph text preserving formatting of the first non-empty run."""
    runs = para.runs
    if not runs:
        para.add_run(new_text)
        return
    # Put full new text in first run; clear remaining runs
    runs[0].text = new_text
    for r in runs[1:]:
        r.text = ""


def _replace_in_para(para, old: str, new: str) -> bool:
    """Replace first occurrence of `old` in paragraph (handles multi-run text)."""
    full = _full_text(para)
    if old not in full:
        return False
    _set_para_text(para, full.replace(old, new, 1))
    return True


def _replace_in_cell(cell, old: str, new: str) -> bool:
    """Replace first occurrence of `old` anywhere in a table cell."""
    for para in cell.paragraphs:
        if _replace_in_para(para, old, new):
            return True
    return False


def _replace_in_doc(doc: Document, old: str, new: str) -> bool:
    """Replace `old` anywhere in document paragraphs and all table cells."""
    changed = False
    for para in doc.paragraphs:
        if _replace_in_para(para, old, new):
            changed = True
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    if _replace_in_para(para, old, new):
                        changed = True
    return changed


# The template uses Wingdings font with  (open square) for unchecked boxes.
# We also handle plain Unicode □ (U+25A1) as a fallback.
_UNCHECKED = frozenset(['', '□', '◻'])
_CHECKED = '■'  # U+25A0 Black Square — universally supported


def _select_checkbox(para, option_text: str) -> bool:
    """Mark the checkbox immediately before `option_text` as selected.

    The template stores checkboxes as Wingdings \\uf06f in separate runs:
      Run i  = '\\uf06f'  (unchecked box)
      Run i+1 = ' '
      Run i+2 = 'Irrevocable'   ← option_text

    We find the run whose stripped text matches option_text, then look
    back up to 3 runs for the checkbox character and replace it.
    """
    runs = para.runs
    for i, run in enumerate(runs):
        if run.text.strip() == option_text:
            for j in range(max(0, i - 3), i):
                if any(c in runs[j].text for c in _UNCHECKED):
                    for c in _UNCHECKED:
                        if c in runs[j].text:
                            runs[j].text = runs[j].text.replace(c, _CHECKED, 1)
                            return True
    return False


def _select_checkbox_in_cell(cell, option_text: str) -> bool:
    for para in cell.paragraphs:
        if _select_checkbox(para, option_text):
            return True
    return False


# ─── Field-specific fill functions ──────────────────────────────────────────

def _fill_header(doc: Document, data: dict) -> None:
    """Table 0: Bank branch, applicant name, CIF."""
    t0 = doc.tables[0]
    # Row 0: Bank branch
    _replace_in_cell(t0.rows[0].cells[0], "………………………", data.get("vcb_branch", "Ha Noi Branch"))
    # Row 1: Applicant company name
    applicant = data.get("applicant_name", "")
    if applicant:
        cell_name = t0.rows[1].cells[0]
        _replace_in_cell(cell_name, "Tên công ty/Name of the company:",
                         f"Tên công ty/Name of the company: {applicant}")


def _fill_lc_type(doc: Document, data: dict) -> None:
    """Table 1 Row 0: LC type checkboxes and issuance method."""
    t1 = doc.tables[1]
    cell = t1.rows[0].cells[0]
    lc_type = (data.get("lc_type") or "Irrevocable").lower()
    method = (data.get("issuance_method") or "SWIFT").upper()

    if "transferable" in lc_type:
        _select_checkbox_in_cell(cell, "Irrevocable")
        _select_checkbox_in_cell(cell, "Transferable")
    elif "confirmed" in lc_type:
        _select_checkbox_in_cell(cell, "Irrevocable")
        _select_checkbox_in_cell(cell, "Confirmed")
    else:
        _select_checkbox_in_cell(cell, "Irrevocable")

    if method == "SWIFT":
        _select_checkbox_in_cell(cell, "Telex/SWIFT")
    else:
        _select_checkbox_in_cell(cell, "Mail")


def _fill_dates(doc: Document, data: dict) -> None:
    """Table 1 Rows 1-2: Expiry date, expiry place, latest shipment date."""
    t1 = doc.tables[1]
    # Row 1: Expiry Date
    if data.get("expiry_date"):
        _replace_in_cell(t1.rows[1].cells[0], "--/--/--", data["expiry_date"])
    if data.get("expiry_place"):
        cell = t1.rows[1].cells[0]
        full = _full_text(cell.paragraphs[0]) if cell.paragraphs else ""
        if "Expiry Date" in full and data.get("expiry_place"):
            # Append expiry place after the date
            for para in cell.paragraphs:
                ft = _full_text(para)
                if "Expiry Date" in ft:
                    _set_para_text(para, ft + f"  Place: {data['expiry_place']}")
                    break
    # Row 1, Col 2: Latest shipment date
    if data.get("latest_shipment_date"):
        _replace_in_cell(t1.rows[1].cells[2], "--/--/--", data["latest_shipment_date"])


def _fill_beneficiary_bank(doc: Document, data: dict) -> None:
    """Table 1 Row 2: Beneficiary's bank — add name/address as new paragraphs."""
    t1 = doc.tables[1]
    row = t1.rows[2]
    bank_name = data.get("beneficiary_bank_name", "")
    bank_addr = data.get("beneficiary_bank_address", "")
    bic = data.get("beneficiary_bank_bic", "")
    if bank_name or bank_addr:
        cell0 = row.cells[0]
        if bank_name:
            cell0.add_paragraph(bank_name)
        if bank_addr:
            cell0.add_paragraph(bank_addr)
    if bic:
        cell2 = row.cells[2]
        replaced = _replace_in_cell(cell2, "BIC code (preferably)", f"BIC/SWIFT: {bic}")
        if not replaced:
            cell2.add_paragraph(f"BIC/SWIFT: {bic}")


def _fill_applicant(doc: Document, data: dict) -> None:
    """Table 1 Row 3: Applicant full name and address."""
    t1 = doc.tables[1]
    row = t1.rows[3]
    name = data.get("applicant_name", "")
    addr = data.get("applicant_address", "")
    cell0 = row.cells[0]
    if name:
        cell0.add_paragraph(f"Full name: {name}")
    if addr:
        cell0.add_paragraph(f"Address: {addr}")


def _fill_beneficiary(doc: Document, data: dict) -> None:
    """Table 1 Row 4: Beneficiary full name, address, account."""
    t1 = doc.tables[1]
    row = t1.rows[4]
    name = data.get("beneficiary_name", "")
    addr = data.get("beneficiary_address", "")
    acct = data.get("beneficiary_account_no", "")
    cell0 = row.cells[0]
    if name:
        cell0.add_paragraph(f"Full name: {name}")
    if addr:
        cell0.add_paragraph(f"Address: {addr}")
    if acct:
        replaced = _replace_in_cell(row.cells[2], "Account No.", f"Account No. {acct}")
        if not replaced:
            row.cells[2].add_paragraph(f"Account No.: {acct}")


def _fill_amount(doc: Document, data: dict) -> None:
    """Table 1 Rows 5-6: Currency, amount, tolerance, amount in words."""
    t1 = doc.tables[1]
    row5 = t1.rows[5]
    currency = data.get("currency", "")
    amount = data.get("amount", "")
    tolerance = data.get("amount_tolerance", "0")
    if currency:
        _replace_in_cell(row5.cells[0], "Currency (ISO)", f"Currency (ISO): {currency}")
    if amount:
        _replace_in_cell(row5.cells[1], "Amount", f"Amount: {amount}")
    if tolerance:
        _replace_in_cell(row5.cells[2], "% More or Less Allowed",
                         f"% More or Less Allowed: {tolerance}%")
    # Row 6: amount in words
    words = data.get("amount_in_words", "")
    if words:
        _replace_in_cell(t1.rows[6].cells[0], "in words:", f"in words: {words}")


def _fill_draft(doc: Document, data: dict) -> None:
    """Table 1 Row 7: Draft type."""
    t1 = doc.tables[1]
    cell = t1.rows[7].cells[0]
    draft = (data.get("draft_type") or "Sight").lower()
    if "sight" in draft:
        _select_checkbox_in_cell(cell, "Sight")
    elif "usance" in draft or "days" in draft:
        days = data.get("draft_days", "")
        if days:
            ft = _full_text(cell.paragraphs[0]) if cell.paragraphs else ""
            # Fill in the days field
            _replace_in_para(cell.paragraphs[0], "days after Bill of Lading Date",
                             f"{days} days after Bill of Lading Date")
    elif "not required" in draft or "no draft" in draft:
        _select_checkbox_in_cell(cell, "Drafts not required")


def _fill_shipment_options(doc: Document, data: dict) -> None:
    """Table 1 Row 8: Partial shipment and transhipment."""
    t1 = doc.tables[1]
    row = t1.rows[8]
    partial = (data.get("partial_shipment") or "Not allowed").lower()
    trans = (data.get("transhipment") or "Not allowed").lower()
    cell0 = row.cells[0]
    cell2 = row.cells[2]
    if "allowed" in partial and "not" not in partial:
        _select_checkbox_in_cell(cell0, "Allowed")
    else:
        _select_checkbox_in_cell(cell0, "Not allowed")
    if "allowed" in trans and "not" not in trans:
        _select_checkbox_in_cell(cell2, "Allowed")
    else:
        _select_checkbox_in_cell(cell2, "Not allowed")


def _fill_ports(doc: Document, data: dict) -> None:
    """Table 1 Row 9: Ports."""
    t1 = doc.tables[1]
    cell = t1.rows[9].cells[0]
    loading = data.get("port_of_loading", "")
    discharge = data.get("port_of_discharge", "")
    if loading or discharge:
        port_text = (
            "(10) Shipment\n"
            f"Port of loading: {loading}\n"
            f"Port of discharge: {discharge}"
        )
        for para in cell.paragraphs:
            if "Shipment" in _full_text(para):
                _set_para_text(para, port_text)
                break


def _fill_incoterms(doc: Document, data: dict) -> None:
    """Table 1 Row 10: Incoterms."""
    t1 = doc.tables[1]
    cell = t1.rows[10].cells[0]
    inco = (data.get("incoterms") or "").upper()
    version = data.get("incoterms_version") or "2020"
    named_port = data.get("named_port") or data.get("port_of_discharge", "")
    if inco:
        _select_checkbox_in_cell(cell, inco)
    # Add version and named port
    for para in cell.paragraphs:
        ft = _full_text(para)
        if "INCOTERMS" in ft.upper() or "Shipping Terms" in ft:
            new_text = ft.rstrip()
            if inco:
                new_text += f"\nSelected: {inco} {named_port} (INCOTERMS {version})"
            _set_para_text(para, new_text)
            break


def _fill_goods(doc: Document, data: dict) -> None:
    """Table 1 Row 11: Description of goods."""
    t1 = doc.tables[1]
    cell = t1.rows[11].cells[0]
    goods = data.get("description_of_goods", "")
    if goods:
        for para in cell.paragraphs:
            if "Description of goods" in _full_text(para):
                _set_para_text(para, f"(12) Description of goods and/or Services\n{goods}")
                break


def _fill_documents(doc: Document, data: dict) -> None:
    """Table 1 Row 12: Documents required."""
    t1 = doc.tables[1]
    cell = t1.rows[12].cells[0]
    docs_data = data.get("documents") or {}
    lines = ["Document required", "This documentary credit is available against presentation of the following documents:"]
    if docs_data.get("commercial_invoice"):
        lines.append(f"✓ Signed commercial invoice: {docs_data['commercial_invoice']}")
    if docs_data.get("bill_of_lading"):
        lines.append(f"✓ {docs_data['bill_of_lading']}")
    if docs_data.get("packing_list"):
        lines.append(f"✓ Packing list: {docs_data['packing_list']}")
    if docs_data.get("certificate_of_origin"):
        lines.append(f"✓ Certificate of origin: {docs_data['certificate_of_origin']}")
    if docs_data.get("insurance_certificate"):
        lines.append(f"✓ Insurance certificate/policy: {docs_data['insurance_certificate']}")
    if docs_data.get("inspection_certificate"):
        lines.append(f"✓ Inspection certificate: {docs_data['inspection_certificate']}")
    for other in (docs_data.get("other_documents") or []):
        lines.append(f"✓ {other}")
    if len(lines) > 2:
        for para in cell.paragraphs:
            if "Document required" in _full_text(para) or "documentary" in _full_text(para).lower():
                _set_para_text(para, "\n".join(lines))
                break


def _fill_additional_conditions(doc: Document, data: dict) -> None:
    """Table 1 Row 13: Additional conditions."""
    t1 = doc.tables[1]
    cell = t1.rows[13].cells[0]
    conditions = data.get("additional_conditions", "")
    if conditions:
        for para in cell.paragraphs:
            if "Additional conditions" in _full_text(para):
                _set_para_text(para, f"Additional conditions:\n{conditions}")
                break


def _fill_charges(doc: Document, data: dict) -> None:
    """Table 1 Row 14: Charges."""
    t1 = doc.tables[1]
    cell = t1.rows[14].cells[0]
    issuing_for = (data.get("issuing_bank_charges_for") or "Applicant")
    other_for = (data.get("other_bank_charges_for") or "Beneficiary")
    for para in cell.paragraphs:
        ft = _full_text(para)
        if "Issuing bank" in ft or "Charges" in ft:
            new = (
                f"(15) Charges:\n"
                f"Issuing bank's charges for the account of: {issuing_for}\n"
                f"Other banks' charges for the account of: {other_for}"
            )
            _set_para_text(para, new)
            break


def _fill_presentation_period(doc: Document, data: dict) -> None:
    """Table 2: Presentation period."""
    period = data.get("presentation_period", "21")
    t2 = doc.tables[2]
    cell = t2.rows[0].cells[0]
    if period == "21":
        _select_checkbox_in_cell(cell, "21 days after shipment date")
    else:
        _replace_in_cell(t2.rows[0].cells[1], "Other:", f"Other: {period} days after shipment date")


def _fill_contract_reference(doc: Document, data: dict) -> None:
    """Commitment paragraph: fill contract number and date."""
    contract_no = data.get("contract_number", "")
    contract_date = data.get("contract_date", "")
    if contract_no:
        _replace_in_doc(doc, "..........……", contract_no)
        _replace_in_doc(doc, "số .......…… ngày", f"số {contract_no} ngày {contract_date}")


# ─── Main public function ───────────────────────────────────────────────────

def fill_lc_template(
    data: dict,
    template_path: str,
    output_path: str,
) -> str:
    """Fill the Vietcombank LC application DOCX template.

    Args:
        data: LCApplicationData.model_dump() dict.
        template_path: Path to the blank DOCX template.
        output_path: Where to save the filled DOCX.

    Returns:
        output_path (str) on success.
    """
    shutil.copy2(template_path, output_path)
    doc = Document(output_path)

    _fill_header(doc, data)
    _fill_lc_type(doc, data)
    _fill_dates(doc, data)
    _fill_beneficiary_bank(doc, data)
    _fill_applicant(doc, data)
    _fill_beneficiary(doc, data)
    _fill_amount(doc, data)
    _fill_draft(doc, data)
    _fill_shipment_options(doc, data)
    _fill_ports(doc, data)
    _fill_incoterms(doc, data)
    _fill_goods(doc, data)
    _fill_documents(doc, data)
    _fill_additional_conditions(doc, data)
    _fill_charges(doc, data)
    _fill_presentation_period(doc, data)
    _fill_contract_reference(doc, data)

    doc.save(output_path)
    return output_path
