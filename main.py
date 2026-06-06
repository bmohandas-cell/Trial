#!/usr/bin/env python3
"""Entry point: collect TREC contract data via CLI and automate zipForm Plus."""

import os
from dotenv import load_dotenv
from prompts import collect_contract_data, collect_addendum_choices
from zipform_bot import run, open_addendum, save_contract

load_dotenv()

ADDENDUM_MODULES = {
    "third_party_financing": "addendums.third_party_financing",
    "hoa": "addendums.hoa",
}


def main() -> None:
    print("zipForm Plus — TREC Contract Automation")
    print("=" * 42)
    headless_input = input("Run browser in background (headless)? [y/N]: ").strip().lower()
    headless = headless_input == "y"

    # Collect main contract data
    data = collect_contract_data()

    # Collect addendum choices + their data
    addendum_keys = collect_addendum_choices(data)
    addendum_data: dict[str, dict] = {}
    for key in addendum_keys:
        module = __import__(ADDENDUM_MODULES[key], fromlist=["collect_data"])
        addendum_data[key] = module.collect_data()

    # Run browser automation
    print("\n[*] Starting browser automation...")

    import os
    from playwright.sync_api import sync_playwright
    from zipform_bot import login, create_transaction, fill_property, fill_price_and_terms, fill_option_and_closing, fill_parties

    email = os.environ.get("ZIPFORM_EMAIL", "")
    password = os.environ.get("ZIPFORM_PASSWORD", "")
    if not email or not password:
        raise SystemExit("Set ZIPFORM_EMAIL and ZIPFORM_PASSWORD in your .env file.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=200)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        try:
            login(page, email, password)
            create_transaction(page, data["transaction_name"])
            fill_property(page, data)
            fill_price_and_terms(page, data)
            fill_option_and_closing(page, data)
            fill_parties(page, data)
            save_contract(page)

            # Fill addendums
            for key in addendum_keys:
                module = __import__(ADDENDUM_MODULES[key], fromlist=["fill", "FORM_NAME"])
                open_addendum(page, module.FORM_NAME)
                module.fill(page, addendum_data[key])
                save_contract(page)

            print("\n[+] All forms filled and saved in zipForm Plus.")
            input("Press Enter to close the browser...")

        except Exception as exc:
            print(f"\n[!] Error: {exc}")
            input("Press Enter to close the browser (check the page for clues)...")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
