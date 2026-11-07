import logging
from pathlib import Path
from busbidder.data import load_and_parse_offers
from busbidder.validation import InvalidOfferError

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    filename="logs/validation.log",
    level=logging.WARNING,
    format="%(levelname)s: %(message)s"
)

# Main function
def main():
    try:
        offers = load_and_parse_offers(Path("data/offers.csv"))
    except (OSError, InvalidOfferError) as error:
        logging.error("Could not load offers: %s", error)
        print(f"Could not load offers: {error}")
        return

    print("Loaded", len(offers), "offers")

    if offers:
        print(offers[0].company_id)

if __name__ == "__main__":
    main()