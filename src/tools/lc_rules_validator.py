"""Apply UCP600, ISBP821, and Incoterms rules to validate and enhance LC application data."""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("tools.lc_rules_validator")


def _warn(data: dict, msg: str) -> None:
    data.setdefault("validation_warnings", [])
    data["validation_warnings"].append(msg)
    logger.warning(f"Validation warning: {msg}")


def _note(data: dict, msg: str) -> None:
    data.setdefault("compliance_notes", [])
    data["compliance_notes"].append(msg)
    logger.info(f"Compliance note: {msg}")


def apply_ucp600_defaults(data: dict) -> dict:
    """Apply UCP600 defaults and validate required fields.

    Key rules applied:
    - Art. 3: All LCs are irrevocable by default
    - Art. 6(d): Expiry date must be stated
    - Art. 14(c): Presentation period = 21 calendar days after shipment
    - Art. 27: B/L must be 'clean'
    - SWIFT is the standard issuance method
    """
    from ..knowledge.loader import get_presentation_period_default

    # Art. 3: LC must be irrevocable
    if not data.get("lc_type"):
        data["lc_type"] = "Irrevocable"
        _note(data, "UCP600 Art.3: LC type defaulted to 'Irrevocable' (all credits are irrevocable).")

    # Art. 14(c): Presentation period — store as "21 days after date of shipment" for clarity
    if not data.get("presentation_period"):
        days = get_presentation_period_default()
        data["presentation_period"] = f"{days} days after date of shipment"
        _note(data, f"UCP600 Art.14(c): Presentation period set to '{data['presentation_period']}'.")
    elif data.get("presentation_period") in ("21", "21 days"):
        data["presentation_period"] = "21 days after date of shipment"
        _note(data, "UCP600 Art.14(c): Presentation period is '21 days after date of shipment' (standard).")

    # Default issuance method
    if not data.get("issuance_method"):
        data["issuance_method"] = "SWIFT"
        _note(data, "Issuance method defaulted to SWIFT (standard for international LCs).")

    # Check expiry date is present
    if not data.get("expiry_date"):
        _warn(data, "UCP600 Art.6: Expiry date is required but not found in contract.")

    # Check expiry place
    if not data.get("expiry_place"):
        _note(data, "UCP600 Art.6: Expiry place not specified; should state the bank's counter.")

    # Check latest shipment date vs expiry date (both dd/mm/yyyy)
    exp = data.get("expiry_date")
    ship = data.get("latest_shipment_date")
    if exp and ship:
        try:
            exp_dt = datetime.strptime(exp, "%d/%m/%Y")
            ship_dt = datetime.strptime(ship, "%d/%m/%Y")
            if ship_dt >= exp_dt:
                _warn(data, f"Date check: Latest shipment date ({ship}) should be before expiry date ({exp}).")
            else:
                _note(data, f"Date check: Latest shipment ({ship}) is before expiry ({exp}). ✓")
        except ValueError:
            _warn(data, f"Date format error: could not parse expiry='{exp}' or shipment='{ship}' as dd/mm/yyyy.")

    # Check B/L cleanliness wording
    docs = data.get("documents") or {}
    bol = docs.get("bill_of_lading") or ""
    if bol and "clean" not in bol.lower():
        _note(data, "UCP600 Art.27: Consider specifying 'clean' bill of lading.")
    if bol and "on board" not in bol.lower():
        _note(data, "UCP600 Art.20: Consider specifying 'shipped on board' bill of lading.")

    # Amount tolerance defaults
    if not data.get("amount_tolerance"):
        data["amount_tolerance"] = "0"

    return data


def apply_incoterms_rules(data: dict) -> dict:
    """Apply Incoterms-specific document requirements.

    Key rules:
    - CIF/CIP: Seller must provide insurance certificate (min 110% of invoice)
    - FOB/CFR: No insurance from seller
    - CIF/CFR/FOB: Requires ocean B/L
    - FCA/CPT/CIP: Accepts multimodal transport document
    """
    from ..knowledge.loader import get_required_documents_for_incoterms

    inco = (data.get("incoterms") or "").upper()
    version = data.get("incoterms_version") or "2020"

    if not inco:
        _warn(data, "Incoterms term not found in contract. Cannot validate document requirements.")
        return data

    term_rules = get_required_documents_for_incoterms(inco)
    insurance_required = term_rules.get("insurance_required_from_seller", False)
    docs = data.get("documents") or {}

    if insurance_required:
        if not docs.get("insurance_certificate"):
            # Set default insurance certificate requirement per UCP600 Art.28
            coverage = term_rules.get("insurance_minimum_coverage", 110)
            # CIP 2020 requires ICC(A) all risks; CIF requires minimum ICC(C) per Incoterms
            # However UCP600 Art.28(f)(ii) mandates ICC(A/B/C) terms be specified explicitly
            if inco == "CIP" and version == "2020":
                ins_clause = "Institute Cargo Clauses (A) — All Risks"
            else:
                ins_clause = "Institute Cargo Clauses (A) — All Risks"  # CIF: use ICC(A) as best practice
            docs["insurance_certificate"] = (
                f"1 original insurance certificate/policy in negotiable form, "
                f"covering {ins_clause}, for {coverage}% of invoice value, "
                f"in {data.get('currency', 'USD')}, blank endorsed"
            )
            data["documents"] = docs
            _note(data, f"UCP600 Art.28 / ISBP 821 K14: Insurance certificate added for {inco} ({version}) — {coverage}% minimum coverage.")
        else:
            # Ensure ICC clause is explicit even if already extracted
            cert = docs.get("insurance_certificate", "")
            if "Institute Cargo Clauses" not in cert:
                docs["insurance_certificate"] = cert + ", Institute Cargo Clauses (A) — All Risks"
                data["documents"] = docs
                _note(data, f"Insurance certificate enhanced: ICC(A) clause added for {inco}. ✓")
            else:
                _note(data, f"Insurance certificate provided for {inco}. ✓")
    else:
        if docs.get("insurance_certificate"):
            _note(data, f"Insurance certificate listed but {inco} does not require seller to provide insurance. Verify with buyer.")
        else:
            _note(data, f"{inco}: Insurance not required from seller (buyer arranges). ✓")

    # Named port consistency
    named_port = data.get("named_port") or data.get("port_of_discharge")
    if inco in ("CIF", "CFR") and not named_port:
        _warn(data, f"{inco} requires a named port of destination. Please specify.")
    elif inco in ("FOB",) and not data.get("port_of_loading"):
        _warn(data, "FOB requires a named port of loading.")

    # B/L requirements for sea terms
    sea_terms = {"FOB", "CIF", "CFR"}
    if inco in sea_terms:
        bol = docs.get("bill_of_lading") or ""
        if not bol:
            docs["bill_of_lading"] = (
                "Full set of 3/3 original clean on board ocean bills of lading evidencing "
                "'Shipped on Board' notation per UCP600 Art.20, "
                "made out to order, notify applicant, "
                f"marked 'Freight {'Prepaid' if inco in ('CIF', 'CFR') else 'Collect'}'"
            )
            data["documents"] = docs
            _note(data, f"Standard ocean B/L requirement added for {inco} term.")

    _note(data, f"Incoterms {version} {inco} rules applied successfully.")
    return data


def apply_isbp821_defaults(data: dict) -> dict:
    """Apply ISBP 821 document preparation standards.

    Key rules:
    - A1: All documents must be dated
    - B4: Invoice description must match LC description
    - E1: Full set of B/L required
    - Documents must be in English (standard for VCB)
    """
    docs = data.get("documents") or {}

    # Ensure other_documents is a list, never None
    if docs.get("other_documents") is None:
        docs["other_documents"] = []

    # Issuing bank: always Vietcombank for this template
    if not data.get("issuing_bank_name"):
        data["issuing_bank_name"] = "Joint Stock Commercial Bank for Foreign Trade of Vietnam (Vietcombank)"
        data["issuing_bank_bic"] = "BFTVVNVX"
        _note(data, "Issuing bank set to Vietcombank (BFTVVNVX) — standard for this LC application template.")

    # Ensure standard documents have descriptions
    if not docs.get("commercial_invoice"):
        docs["commercial_invoice"] = "3 originals, signed"
        _note(data, "ISBP 821 B1: Commercial invoice default set to '3 originals, signed'.")

    if not docs.get("packing_list"):
        docs["packing_list"] = "1 original + 2 copies"
        _note(data, "ISBP 821: Packing list default set.")

    # Certificate of Origin — common requirement for customs
    if not docs.get("certificate_of_origin"):
        _note(data, "Certificate of Origin not specified; consider adding for customs clearance.")

    data["documents"] = docs

    # Additional conditions: English language requirement
    conditions = data.get("additional_conditions") or ""
    if "English" not in conditions:
        if conditions:
            conditions = conditions + "\nDocuments must be issued in English."
        else:
            conditions = "Documents must be issued in English.\nThe amount utilized must be endorsed on the reverse of the original L/C."
        data["additional_conditions"] = conditions
        _note(data, "ISBP 821 A3: 'Documents in English' condition added.")

    return data


def validate_completeness(data: dict) -> dict:
    """Check that all required LC fields are populated."""
    required_fields = [
        ("applicant_name", "Applicant name"),
        ("beneficiary_name", "Beneficiary name"),
        ("currency", "Currency (ISO)"),
        ("amount", "LC Amount"),
        ("expiry_date", "Expiry date"),
        ("latest_shipment_date", "Latest shipment date"),
        ("incoterms", "Incoterms term"),
        ("port_of_loading", "Port of loading"),
        ("port_of_discharge", "Port of discharge"),
        ("description_of_goods", "Description of goods"),
        ("beneficiary_bank_name", "Beneficiary bank name"),
    ]
    missing = []
    for field, label in required_fields:
        if not data.get(field):
            missing.append(label)
            _warn(data, f"Required field missing: {label}")
    if not missing:
        _note(data, "Completeness check: All required fields are present. ✓")
    return data


def validate_and_enhance(data: dict) -> dict:
    """Run all validation and enhancement rules in sequence.

    Pipeline:
    1. UCP600 defaults and validation
    2. Incoterms-specific document requirements
    3. ISBP 821 document standards
    4. Completeness check
    """
    data = apply_ucp600_defaults(data)
    data = apply_incoterms_rules(data)
    data = apply_isbp821_defaults(data)
    data = validate_completeness(data)
    warnings = data.get("validation_warnings", [])
    notes = data.get("compliance_notes", [])
    logger.info(
        f"Validation complete — {len(warnings)} warnings, {len(notes)} compliance notes"
    )
    return data
