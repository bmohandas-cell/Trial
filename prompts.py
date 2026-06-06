"""CLI prompts to collect TREC contract data from the user."""


def ask(label: str, required: bool = True, default: str = "") -> str:
    suffix = f" [{default}]" if default else (" (required)" if required else " (optional)")
    while True:
        value = input(f"  {label}{suffix}: ").strip()
        if not value and default:
            return default
        if not value and required:
            print("    This field is required.")
            continue
        return value


def ask_choice(label: str, choices: list[str]) -> str:
    print(f"  {label}:")
    for i, c in enumerate(choices, 1):
        print(f"    {i}. {c}")
    while True:
        raw = input("  Enter number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        print("  Invalid choice.")


def collect_contract_data() -> dict:
    print("\n=== TREC One-to-Four Family Residential Contract ===\n")

    print("-- Transaction Name (internal label) --")
    transaction_name = ask("Transaction name", default="New TREC Contract")

    print("\n-- Property --")
    data = {
        "transaction_name": transaction_name,
        "property_address": ask("Street address"),
        "property_city": ask("City"),
        "property_county": ask("County"),
        "property_zip": ask("ZIP code"),
        "legal_description": ask("Legal description", required=False),
    }

    print("\n-- Sales Price & Terms --")
    data["sales_price"] = ask("Sales price (e.g. 350000)")
    data["earnest_money"] = ask("Earnest money amount")
    data["down_payment"] = ask("Down payment amount")

    print("\n-- Financing --")
    data["financing_type"] = ask_choice(
        "Financing type",
        ["Conventional", "FHA", "VA", "Cash", "Texas Veterans", "Other"],
    )
    if data["financing_type"] != "Cash":
        data["loan_amount"] = ask("Loan amount")
        data["loan_years"] = ask("Loan term (years)", default="30")
        data["interest_rate"] = ask("Max interest rate (%)", default="8")

    print("\n-- Option Period --")
    data["option_days"] = ask("Option period (days)", default="7")
    data["option_fee"] = ask("Option fee amount")

    print("\n-- Closing --")
    data["closing_date"] = ask("Closing date (MM/DD/YYYY)")
    data["possession"] = ask_choice(
        "Possession",
        ["Closing & Funding", "Closing", "Other"],
    )

    print("\n-- Buyer --")
    data["buyer_name"] = ask("Buyer full name(s)")
    data["buyer_phone"] = ask("Buyer phone", required=False)
    data["buyer_email"] = ask("Buyer email", required=False)

    print("\n-- Seller --")
    data["seller_name"] = ask("Seller full name(s)")
    data["seller_phone"] = ask("Seller phone", required=False)
    data["seller_email"] = ask("Seller email", required=False)

    print("\n-- Agents --")
    data["listing_agent"] = ask("Listing agent name", required=False)
    data["listing_brokerage"] = ask("Listing brokerage", required=False)
    data["buyers_agent"] = ask("Buyer's agent name", required=False)
    data["buyers_brokerage"] = ask("Buyer's brokerage", required=False)

    print("\n-- Additional --")
    data["title_company"] = ask("Title company name", required=False)
    data["hoa"] = ask_choice("HOA?", ["Yes", "No"])
    data["survey"] = ask_choice("Existing survey?", ["Yes - Acceptable", "Yes - New required", "No"])

    return data


def collect_addendum_choices(data: dict) -> list[str]:
    """Ask which addendums to include based on deal data and user preference."""
    print("\n-- Addendums --")
    addendums: list[str] = []

    # Third Party Financing — suggest if not cash
    if data.get("financing_type", "Cash") != "Cash":
        include = input("  Include Third Party Financing Addendum (TREC 40-9)? [Y/n]: ").strip().lower()
        if include != "n":
            addendums.append("third_party_financing")

    # HOA — suggest if HOA flagged yes
    if data.get("hoa", "No") == "Yes":
        include = input("  Include HOA Addendum (TREC 36-9)? [Y/n]: ").strip().lower()
        if include != "n":
            addendums.append("hoa")
    else:
        include = input("  Include HOA Addendum (TREC 36-9)? [y/N]: ").strip().lower()
        if include == "y":
            addendums.append("hoa")

    return addendums
