"""
TREC Addendum for Property Subject to Mandatory Membership in HOA (Form 36-9)
Automates filling the HOA addendum inside zipForm Plus.
"""

from playwright.sync_api import Page, TimeoutError as PWTimeout


FORM_NAME = "Addendum for Property Subject to Mandatory Membership in a Property Owners Association"


def collect_data() -> dict:
    print("\n-- HOA Addendum (TREC 36-9) --")
    from prompts import ask, ask_choice

    data: dict = {}

    data["hoa_name"] = ask("HOA / Property Owners Association name")
    data["management_company"] = ask("Management company name", required=False)
    data["management_phone"] = ask("Management company phone", required=False)

    data["transfer_fee"] = ask("Transfer fee amount", required=False)
    data["other_fees"] = ask("Other fees description", required=False)

    data["dues_frequency"] = ask_choice(
        "Dues payment frequency",
        ["Monthly", "Quarterly", "Annually", "Other"],
    )
    data["dues_amount"] = ask("Dues amount")

    data["resale_cert"] = ask_choice(
        "Resale certificate — who orders?",
        ["Seller", "Buyer"],
    )
    data["resale_cert_days"] = ask("Days for seller to deliver resale certificate", default="7")

    data["subdivision_info"] = ask_choice(
        "Subdivision information — who orders?",
        ["Seller", "Buyer"],
    )

    data["hoa_approval"] = ask_choice(
        "Does HOA have right to approve buyer?",
        ["Yes", "No"],
    )

    if data["hoa_approval"] == "Yes":
        data["hoa_approval_days"] = ask("HOA approval deadline (days)", default="10")

    data["special_provisions"] = ask("Special provisions / notes", required=False)

    return data


def fill(page: Page, data: dict, **_) -> None:
    """Fill the HOA Addendum already open in the page."""
    print("[*] Filling HOA Addendum...")

    from zipform_bot import _fill_field, DEBUG_MODE

    fields = [
        ("hoa_name",            ['input[name*="hoaName" i]',          '#hoaName',          'input[placeholder*="Association Name" i]']),
        ("hoa_management_co",   ['input[name*="managementCo" i]',     '#managementCompany','input[placeholder*="Management" i]']),
        ("hoa_mgmt_phone",      ['input[name*="managementPhone" i]',  '#managementPhone']),
        ("hoa_transfer_fee",    ['input[name*="transferFee" i]',      '#transferFee',      'input[placeholder*="Transfer Fee" i]']),
        ("hoa_other_fees",      ['input[name*="otherFees" i]',        'textarea[name*="otherFees" i]']),
        ("hoa_dues_amount",     ['input[name*="duesAmount" i]',       '#duesAmount',       'input[placeholder*="Dues" i]']),
        ("hoa_resale_cert_days",['input[name*="resaleCertDays" i]',   '#resaleCertDays']),
        ("hoa_approval_days",   ['input[name*="hoaApprovalDays" i]',  '#hoaApprovalDays']),
        ("hoa_special_prov",    ['textarea[name*="specialProv" i]',   '#specialProvisions']),
    ]

    key_map = {
        "hoa_name": "hoa_name",
        "hoa_management_co": "management_company",
        "hoa_mgmt_phone": "management_phone",
        "hoa_transfer_fee": "transfer_fee",
        "hoa_other_fees": "other_fees",
        "hoa_dues_amount": "dues_amount",
        "hoa_resale_cert_days": "resale_cert_days",
        "hoa_approval_days": "hoa_approval_days",
        "hoa_special_prov": "special_provisions",
    }

    for cache_key, selectors in fields:
        data_key = key_map[cache_key]
        _fill_field(page, cache_key, selectors, data.get(data_key, ""))

    # Radios — try click, fall back to debug
    radio_fields = [
        ("dues_frequency",  f'label:has-text("{data.get("dues_frequency","")}")'),
        ("resale_cert",     f'label:has-text("{data.get("resale_cert","")}")'),
        ("subdivision_info",f'label:has-text("{data.get("subdivision_info","")}")'),
        ("hoa_approval",    f'label:has-text("{data.get("hoa_approval","")}")'),
    ]

    for field_key, sel in radio_fields:
        value = data.get(field_key, "")
        if not value:
            continue
        try:
            page.click(sel, timeout=3000)
        except PWTimeout:
            if DEBUG_MODE:
                from zipform_bot import _debug_pause
                _debug_pause(page, f"hoa_{field_key}", value)

    print("[+] HOA Addendum filled.")
