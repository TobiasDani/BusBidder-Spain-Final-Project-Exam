import tempfile
import unittest
from pathlib import Path

from busbidder.data import load_and_parse_offers
from busbidder.models import TravelRequest, TravellerProfile
from busbidder.ranking import filter_offers, rank_offers, explain_recommendation
from busbidder.booking import load_bookings, book_offer, get_available_seats

DATA = Path(__file__).resolve().parents[1] / "data"


class TestIntegration(unittest.TestCase):

    def test_search_rank_book_and_reload(self):
        # Start with the real CSV data
        offers = load_and_parse_offers(
            DATA / "offers.csv",
            DATA / "companies.csv",
            DATA / "destinations.csv"
        )

        self.assertGreaterEqual(len(offers), 75)

        request = TravelRequest(
            "Malaga", "2027-07-12", "2027-07-12",
            90, 3, 0, 2000, False
        )

        profile = TravellerProfile("09:00", 0.60, 0.15, 0.10, 0.15)

        # Store test bookings in a temporary file
        with tempfile.TemporaryDirectory() as folder:
            file_path = Path(folder) / "bookings.csv"

            file_path.write_text(
                "booking_reference,offer_id,booked_at,price_paid_eur,"
                "changeable,refundable,luggage_kg\n",
                encoding="utf-8"
            )

            # Filter and rank offers
            bookings = load_bookings(file_path)
            filtered = filter_offers(offers, request, bookings)
            ranked = rank_offers(filtered, profile)

            self.assertTrue(ranked)
            self.assertIn(
                "Recommended:",
                explain_recommendation(ranked[0], profile)
            )

            # Book the best offer
            chosen = ranked[0]["offer"]
            original_seats = get_available_seats(chosen, bookings)

            booking = book_offer(chosen, file_path)

            # Reload and verify the saved booking
            saved = load_bookings(
                file_path,
                {offer.offer_id for offer in offers}
            )

            self.assertEqual(
                saved[0].booking_reference,
                booking.booking_reference
            )

            self.assertEqual(
                get_available_seats(chosen, saved),
                original_seats - 1
            )


if __name__ == "__main__":
    unittest.main()
