import csv
import tempfile
import unittest
from pathlib import Path

from busbidder.models import Offer, FareConditions
from busbidder.booking import book_offer, load_bookings, get_available_seats, BookingError


class TestBooking(unittest.TestCase):

    def setUp(self):
        # Use a temporary file so real bookings are not changed
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)

        self.file_path = Path(folder.name) / "bookings.csv"
        self.file_path.write_text(
            "booking_reference,offer_id,booked_at,price_paid_eur,"
            "changeable,refundable,luggage_kg\n",
            encoding="utf-8"
        )

        self.offer = Offer(
            "OFF-2027-0016", "SOL", "Madrid", "Malaga",
            "2027-07-12", "09:00", "2027-07-12", "15:00",
            360, 45.0, 0, 2, 4.5,
            FareConditions(20, False, False)
        )

    def test_capacity_after_reload(self):
        self.offer.seats_available = 1

        first = book_offer(self.offer, self.file_path)
        bookings = load_bookings(self.file_path)

        self.assertEqual(first.offer_id, self.offer.offer_id)
        self.assertEqual(len(bookings), 1)
        self.assertEqual(get_available_seats(self.offer, bookings), 0)

        # The next booking must be rejected
        with self.assertLogs(level="ERROR") as log:
            with self.assertRaises(BookingError):
                book_offer(self.offer, self.file_path)

        self.assertIn("Booking failed", log.output[0])
        self.assertEqual(len(load_bookings(self.file_path)), 1)

    def test_unique_references_and_saved_conditions(self):
        first = book_offer(self.offer, self.file_path)

        # Later changes must not affect the original booking
        self.offer.price_eur = 100.0
        self.offer.fare_conditions.changeable = True

        second = book_offer(self.offer, self.file_path)

        bookings = load_bookings(self.file_path)

        self.assertNotEqual(first.booking_reference, second.booking_reference)
        self.assertEqual(bookings[0].price_paid_eur, 45.0)
        self.assertFalse(bookings[0].fare_conditions.changeable)
        self.assertEqual(bookings[1].price_paid_eur, 100.0)
        self.assertTrue(bookings[1].fare_conditions.changeable)

        # Check that duplicate booking references are rejected
        with open(self.file_path, newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))

        with open(self.file_path, "a", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(rows[1])

        with self.assertRaises(BookingError):
            load_bookings(self.file_path)


if __name__ == "__main__":
    unittest.main()
