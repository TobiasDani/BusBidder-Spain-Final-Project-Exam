import logging
from pathlib import Path

from busbidder.data import load_and_parse_offers
from busbidder.validation import InvalidOfferError
from busbidder.ranking import filter_offers, rank_offers, explain_recommendation
from busbidder.booking import load_bookings, book_offer, BookingError
from busbidder.cli import (
    ask_travel_request,
    ask_traveller_profile,
    ask_yes_no,
    display_offers,
    choose_offer
)

# Find the data and log folders relative to main.py
project_folder = Path(__file__).resolve().parent
data_folder = project_folder / "data"
log_folder = project_folder / "logs"
log_folder.mkdir(exist_ok=True)

logging.basicConfig(
    filename=log_folder / "busbidder.log",
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


# Main function
def main():
    # Load offers
    try:
        offers = load_and_parse_offers(
            data_folder / "offers.csv",
            data_folder / "companies.csv",
            data_folder / "destinations.csv"
        )

    except (OSError, InvalidOfferError) as error:
        logging.error("Could not load offers: %s", error)
        print(f"Could not load offers: {error}")
        return

    if not offers:
        print("No valid offers available.")
        return

    print("Welcome to BusBidder Spain!")
    print("Loaded", len(offers), "offers")

    while True:
        print("\n--- Main Menu ---")
        print("1. Search for buses")
        print("2. Exit")

        choice = input("Choose option: ").strip()

        if choice == "2":
            print("Goodbye!")
            break

        if choice != "1":
            print("Invalid option.")
            continue

        # Load existing bookings
        try:
            bookings = load_bookings(
                data_folder / "bookings.csv",
                {offer.offer_id for offer in offers}
            )

        except (OSError, BookingError) as error:
            print(f"Could not load bookings: {error}")
            logging.error("Could not load bookings: %s", error)
            return

        # Get user requirements and preferences
        request = ask_travel_request(offers)

        if request is None:
            continue

        profile = ask_traveller_profile()

        # Filter and rank offers
        filtered = filter_offers(offers, request, bookings)
        ranked = rank_offers(filtered, profile)
        logging.info("Search for %s: %s matching offers", request.destination, len(ranked))

        if not ranked:
            print("\nNo offers match your requirements.")
            continue

        # Display ranked offers
        display_offers(ranked, bookings)

        # Explain the top recommendation
        print("\n" + explain_recommendation(ranked[0], profile))

        # Let the user select an offer
        offer = choose_offer(ranked)

        if offer is None:
            continue

        print(f"Selected: {offer.company_id} | {offer.offer_id} | €{offer.price_eur:.2f}")

        # Confirm booking
        if ask_yes_no("Confirm booking? (y/n): "):
            try:
                booking = book_offer(offer, data_folder / "bookings.csv")
                print("Booking confirmed:", booking.booking_reference)
                print(f"Price: €{booking.price_paid_eur:.2f}")

            except (BookingError, OSError) as error:
                print("Booking failed:", error)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
