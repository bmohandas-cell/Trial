"""
TREC Third Party Financing Addendum (Form 40-9)
Automates filling the addendum inside zipForm Plus after the main contract.
"""

from playwright.sync_api import Page, TimeoutError as PWTimeout


FORM_NAME = "Third Party Financing Addendum"


def collect_data() -> dict:
    print("\n-- Third Party Financing Addendum (TREC 40-9) --")
    from prompts import ask, ask_choice

    data: dict = {}

    data["financing_type"] = ask_choice(
        "Financing type",
        ["Conventional", "FHA", "VA", "USDA/RHS", "Texas Veterans"],
    )

    data["loan_amount"] = ask("Loan amount")
    data["loan_years"] = ask("Loan term (years)", default="30")
    data["interest_rate"] = ask("Maximum interest rate (%)", default="8")
    data["origination_charges"] = ask("Max origination charges (%)", default="1")

    if data["financing_type"] in ("FHA", "VA"):
        data["discount_points"] = ask("Max discount points (%)", default="0")

    if data["financing_type"] == "FHA":
        data["mip"] = ask("MIP amount (leave blank to use max allowed)", required=False)

    if data["financing_type"] == "VA":
        data["va_funding_fee"] = ask("VA funding fee amount (leave blank to use max allowed)", required=False)

    data["approval_days"] = ask("Financing approval deadline (days from effective date)", default="21")

    return data


def fill(page: Page, data: dict) -> None:
    """Fill the Third Party Financing Addendum already open in the page."""
    print("[*] Filling Third Party Financing Addendum...")

    from zipform_bot import _fill, _select, _click

    financing = data.get("financing_type", "")
    if financing:
        # Click the matching financing type checkbox / radio
        try:
            page.click(f'label:has-text("{financing}"), input[value*="{financing}" i]', timeout=4000)
        except PWTimeout:
            pass

    pairs = [
        ("loan_amount",         ['input[name*="loanAmount" i]',         '#loanAmount']),
        ("loan_years",          ['input[name*="loanYears" i]',          '#loanYears']),
        ("interest_rate",       ['input[name*="interestRate" i]',       '#interestRate']),
        ("origination_charges", ['input[name*="originationCharge" i]',  '#originationCharges']),
        ("discount_points",     ['input[name*="discountPoints" i]',     '#discountPoints']),
        ("mip",                 ['input[name*="mip" i]',                '#mip']),
        ("va_funding_fee",      ['input[name*="vaFundingFee" i]',       '#vaFundingFee']),
        ("approval_days",       ['input[name*="approvalDays" i]',       '#approvalDays', 'input[placeholder*="approval" i]']),
    ]

    for key, selectors in pairs:
        value = data.get(key, "")
        if not value:
            continue
        for sel in selectors:
            try:
                _fill(page, sel, value, timeout=3000)
                break
            except PWTimeout:
                continue

    print("[+] Third Party Financing Addendum filled.")
