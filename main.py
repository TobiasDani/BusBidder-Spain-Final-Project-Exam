from pathlib import Path
from busbidder.data import load_and_parse_offers

# Main function
def main():
    offers = load_and_parse_offers(Path("data/offers.csv"))

    print("Loaded", len(offers), "offers")

    print(offers[0].offer_id)
    print(offers[0].fare_conditions.changeable)

if __name__ == "__main__":
    main()
