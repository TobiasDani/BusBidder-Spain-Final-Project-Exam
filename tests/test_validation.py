import csv
import unittest
from pathlib import Path

from busbidder.data import _parse_offers, load_and_parse_offers
from busbidder.models import TravelRequest, TravellerProfile
from busbidder.validation import (
    InvalidOfferError, validate_offer_row,
    validate_travel_request, validate_traveller_profile
)

DATA = Path(__file__).resolve().parents[1] / "data"


class TestValidation(unittest.TestCase):

    def setUp(self):
        # Use one real CSV row as a starting point
        with open(DATA / "offers.csv", newline="", encoding="utf-8") as file:
            self.row = next(csv.DictReader(file))

        with open(DATA / "companies.csv", newline="", encoding="utf-8") as file:
            self.company_ids = {row["company_id"] for row in csv.DictReader(file)}

        with open(DATA / "destinations.csv", newline="", encoding="utf-8") as file:
            self.routes = {(row["origin"], row["destination"])
                           for row in csv.DictReader(file)}

    def test_invalid_offers_are_rejected(self):
        # Each change should make the otherwise valid row invalid
        cases = [
            ("negative price", {"price_eur": "-10"}),
            ("NaN price", {"price_eur": "NaN"}),
            ("unknown company", {"company_id": "UNKNOWN"}),
            ("unknown destination", {"destination": "Atlantis"}),
            ("invalid date", {"arrival_date": "not-a-date"}),
            ("missing price", {"price_eur": ""})
        ]

        for name, changes in cases:
            with self.subTest(case=name):
                row = self.row.copy()
                row.update(changes)

                with self.assertRaises(InvalidOfferError):
                    validate_offer_row(row, self.company_ids, self.routes)

        # Check that loading skips bad rows and logs the reason
        bad_row = self.row.copy()
        bad_row["price_eur"] = "-10"

        with self.assertLogs("busbidder.data", level="WARNING") as log:
            offers = _parse_offers([self.row, bad_row], self.company_ids, self.routes)

        self.assertEqual(len(offers), 1)
        self.assertIn("CSV line 3", log.output[0])

    def test_unusual_but_valid_offers(self):
        # Expensive or full buses are still valid data
        row = self.row.copy()
        row.update({"price_eur": "500", "seats_available": "0"})
        offer = validate_offer_row(row, self.company_ids, self.routes)

        self.assertEqual(offer["price_eur"], 500.0)
        self.assertEqual(offer["seats_available"], 0)

        # An overnight journey is valid when dates and duration match
        row = self.row.copy()
        row.update({
            "travel_date": "2027-07-12",
            "departure_time": "23:00",
            "arrival_date": "2027-07-13",
            "arrival_time": "02:00",
            "duration_minutes": "180"
        })

        offer = validate_offer_row(row, self.company_ids, self.routes)
        self.assertEqual(offer["duration_minutes"], 180)

    def test_invalid_user_requirements(self):
        request = TravelRequest(
            "Malaga", "2027-07-14", "2027-07-12",
            100, 2, 20, 900, False
        )

        with self.assertRaises(ValueError):
            validate_travel_request(request)

        request.start_date = "2027-07-12"
        request.max_budget = -10

        with self.assertRaises(ValueError):
            validate_travel_request(request)

        profile = TravellerProfile("09:00", 0.5, 0.5, 0.5, 0.5)

        with self.assertRaises(ValueError):
            validate_traveller_profile(profile)

        profile = TravellerProfile("25:00", 0.6, 0.15, 0.1, 0.15)

        with self.assertRaises(ValueError):
            validate_traveller_profile(profile)

    def test_missing_csv_file(self):
        # Missing files should raise an error instead of returning empty data
        with self.assertRaises(FileNotFoundError):
            load_and_parse_offers(
                DATA / "missing_offers.csv",
                DATA / "companies.csv",
                DATA / "destinations.csv"
            )


if __name__ == "__main__":
    unittest.main()
