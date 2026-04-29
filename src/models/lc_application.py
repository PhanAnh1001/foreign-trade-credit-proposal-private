from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, field_validator


class DocumentRequirements(BaseModel):
    """Documents required for LC presentation per ISBP 821."""
    commercial_invoice: str = "3 originals"
    bill_of_lading: str = "Full set of 3/3 original clean shipped on board ocean bills of lading"
    packing_list: str = "1 original + 2 copies"
    certificate_of_origin: Optional[str] = None
    insurance_certificate: Optional[str] = None  # Required for CIF/CIP
    inspection_certificate: Optional[str] = None
    other_documents: list[str] = []


class LCApplicationData(BaseModel):
    """Structured LC application data extracted from a foreign trade contract."""

    # ── Contract reference ──────────────────────────────────────────────────
    contract_number: Optional[str] = None
    contract_date: Optional[str] = None  # dd/mm/yyyy

    # ── Parties ────────────────────────────────────────────────────────────
    applicant_name: Optional[str] = None
    applicant_address: Optional[str] = None
    beneficiary_name: Optional[str] = None
    beneficiary_address: Optional[str] = None
    beneficiary_account_no: Optional[str] = None
    beneficiary_bank_name: Optional[str] = None
    beneficiary_bank_address: Optional[str] = None
    beneficiary_bank_bic: Optional[str] = None

    # ── LC Terms ───────────────────────────────────────────────────────────
    lc_type: str = "Irrevocable"           # Irrevocable | Irrevocable Transferable | Irrevocable Confirmed
    issuance_method: str = "SWIFT"         # SWIFT | Mail
    currency: Optional[str] = None         # ISO 4217, e.g. "USD"
    amount: Optional[str] = None           # e.g. "450000.00"
    amount_in_words: Optional[str] = None  # e.g. "SAY US DOLLARS FOUR HUNDRED FIFTY THOUSAND ONLY"
    amount_tolerance: str = "0"            # percentage, e.g. "0", "5", "10"

    # ── Dates ──────────────────────────────────────────────────────────────
    expiry_date: Optional[str] = None       # yy/mm/dd per UCP600
    expiry_place: Optional[str] = None      # e.g. "At Vietcombank, Ha Noi, Vietnam"
    latest_shipment_date: Optional[str] = None  # yy/mm/dd

    # ── Shipping ───────────────────────────────────────────────────────────
    incoterms: Optional[str] = None         # FOB | CIF | CFR | EXW | FCA | CPT | CIP
    incoterms_version: Optional[str] = None # "2000" | "2010" | "2020"
    named_port: Optional[str] = None        # Named port/place per Incoterms
    port_of_loading: Optional[str] = None
    port_of_discharge: Optional[str] = None
    partial_shipment: str = "Not allowed"   # "Allowed" | "Not allowed"
    transhipment: str = "Not allowed"       # "Allowed" | "Not allowed"

    # ── Payment / Drafts ───────────────────────────────────────────────────
    draft_type: str = "Sight"               # "Sight" | "Usance" | "No draft required"
    draft_days: Optional[int] = None        # for Usance: days after B/L date
    presentation_period: str = "21"         # days; UCP600 Art.14(c) default = 21

    # ── Goods ──────────────────────────────────────────────────────────────
    description_of_goods: Optional[str] = None

    # ── Documents ──────────────────────────────────────────────────────────
    documents: DocumentRequirements = DocumentRequirements()
    additional_conditions: str = (
        "Documents must be issued in English\n"
        "The amount utilized must be endorsed on the reverse of the original L/C."
    )

    # ── Charges ────────────────────────────────────────────────────────────
    issuing_bank_charges_for: str = "Applicant"    # "Applicant" | "Beneficiary"
    other_bank_charges_for: str = "Beneficiary"    # "Applicant" | "Beneficiary"

    # ── Quality notes (populated by validator) ─────────────────────────────
    validation_warnings: list[str] = []
    compliance_notes: list[str] = []

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v

    @field_validator("incoterms")
    @classmethod
    def uppercase_incoterms(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v

    def model_dump_for_filling(self) -> dict:
        """Return a flat dict suitable for DOCX template filling."""
        d = self.model_dump()
        if self.documents:
            d["documents"] = self.documents.model_dump()
        return d
