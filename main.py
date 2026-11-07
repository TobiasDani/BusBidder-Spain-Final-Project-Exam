import logging
from pathlib import Path
from busbidder.data import load_and_parse_offers
from busbidder.validation import InvalidOfferError
from busbidder.models import TravelRequest, TravellerProfile
from busbidder.ranking import filter_offers, rank_offers, explain_recommendation
from busbidder.booking import load_bookings, book_offer, BookingError

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    filename="logs/validation.log",
    level=logging.WARNING,
    format="%(levelname)s: %(message)s"
)

# Main function
def main():
    # Load offers and existing bookings
    try:
        offers = load_and_parse_offers(Path("data/offers.csv"))
        bookings = load_bookings()
    except (OSError, InvalidOfferError, BookingError) as error:
        logging.error("Could not load data: %s", error)
        print(f"Could not load data: {error}")
        return

    print("Loaded", len(offers), "offers")

    # Temporary travel request
    request = TravelRequest(
        "Malaga", "2027-07-12", "2027-07-14",
        600, 3, 0, 2000, False
    )

    # Temporary traveller profile
    profile = TravellerProfile(
        "09:00", 0.60, 0.15, 0.10, 0.15
    )

    # Filter and rank offers
    filtered = filter_offers(offers, request, bookings)
    ranked = rank_offers(filtered, profile)

    # Display the top 3 offers
    print("Found", len(ranked), "matching offers")

    for result in ranked[:3]:
        offer = result["offer"]
        print(
            offer.company_id,
            offer.price_eur,
            round(result["total_score"], 2)
        )

    if not ranked:
        print("No offers match your requirements.")
        return

    # Explain the top recommendation
    print("\n" + explain_recommendation(ranked[0], profile))

    # Book the top offer if the user wants to
    if input("\nBook the top offer? (y/n): ").strip().lower() == "y":
        try:
            booking = book_offer(ranked[0]["offer"])
            print("Booking confirmed:", booking.booking_reference)

        except (BookingError, OSError) as error:
            print("Booking failed:", error)


if __name__ == "__main__":
    main()