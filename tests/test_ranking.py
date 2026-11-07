import unittest
from datetime import datetime, timedelta

from busbidder.models import Offer, FareConditions, TravelRequest, TravellerProfile, Booking
from busbidder.ranking import filter_offers, normalize_scores, rank_offers


class TestRanking(unittest.TestCase):

    def make_offer(self, number, company, price, duration, departure,
                   changeable=False, refundable=False, luggage=20, transfers=0):
        """
        Create a test offer without needing a CSV file.
        """

        start = datetime.strptime("2027-07-12 " + departure, "%Y-%m-%d %H:%M")
        end = start + timedelta(minutes=duration)

        return Offer(
            f"OFF-2027-{number:04d}", company, "Madrid", "Malaga",
            start.strftime("%Y-%m-%d"), start.strftime("%H:%M"),
            end.strftime("%Y-%m-%d"), end.strftime("%H:%M"),
            duration, price, transfers, 6, 4.5,
            FareConditions(luggage, changeable, refundable)
        )

    def setUp(self):
        # Five offers with different advantages and disadvantages
        self.offers = [
            self.make_offer(16, "SOL", 29.90, 535, "07:20", luggage=15, transfers=1),
            self.make_offer(17, "CAM", 69.90, 385, "09:00", changeable=True),
            self.make_offer(18, "COS", 50.00, 470, "10:00", changeable=True),
            self.make_offer(19, "VER", 63.50, 460, "12:15", True, True, 25),
            self.make_offer(20, "NOC", 39.50, 490, "22:15")
        ]

        self.budget = TravellerProfile("09:00", 0.60, 0.15, 0.10, 0.15)

    def test_hard_constraints_and_full_buses(self):
        # Offers exactly on the limits should be accepted
        request = TravelRequest(
            "Malaga", "2027-07-12", "2027-07-12",
            29.90, 1, 15, 535, False
        )

        filtered = filter_offers(self.offers, request, [])
        self.assertEqual([offer.company_id for offer in filtered], ["SOL"])

        # A slightly lower budget should reject the same offer
        request.max_budget = 29.89
        self.assertEqual(filter_offers(self.offers, request, []), [])

        # Check transfers, luggage and changeability together
        strict_request = TravelRequest(
            "Malaga", "2027-07-12", "2027-07-12",
            600, 0, 25, 2000, True
        )

        filtered = filter_offers(self.offers, strict_request, [])
        self.assertEqual([offer.company_id for offer in filtered], ["VER"])

        # An existing booking can make an offer unavailable
        request.max_budget = 29.90
        self.offers[0].seats_available = 1

        existing = Booking(
            "BUS-0001A", self.offers[0].offer_id,
            "2026-11-07T12:00:00", 29.90,
            self.offers[0].fare_conditions
        )

        self.assertEqual(filter_offers(self.offers, request, [existing]), [])

    def test_normalization_and_ties(self):
        # Empty and identical values
        self.assertEqual(normalize_scores([]), [])
        self.assertEqual(normalize_scores([40, 40]), [100.0, 100.0])
        self.assertEqual(normalize_scores([20, 40, 60]), [100.0, 50.0, 0.0])

        with self.assertRaises(ValueError):
            normalize_scores([float("nan"), 40])

        # One offer should not cause division by zero
        result = rank_offers(self.offers[:1], self.budget)

        self.assertEqual(result[0]["price_score"], 100)
        self.assertEqual(result[0]["duration_score"], 100)

        # Identical offers should be sorted by ID
        first = self.make_offer(30, "CAM", 50, 400, "09:00")
        second = self.make_offer(29, "CAM", 50, 400, "09:00")

        ranked = rank_offers([first, second], self.budget)

        self.assertEqual(ranked[0]["offer"].offer_id, second.offer_id)

    def test_expensive_outlier(self):
        # Add one unusually expensive offer
        expensive = self.make_offer(9001, "CAM", 500, 385, "09:00")

        original = rank_offers(
            self.offers, self.budget, limit_price_outliers=False
        )

        without_protection = rank_offers(
            self.offers + [expensive],
            self.budget,
            limit_price_outliers=False
        )

        with_protection = rank_offers(
            self.offers + [expensive], self.budget
        )

        self.assertEqual(original[0]["offer"].company_id, "SOL")
        self.assertEqual(without_protection[0]["offer"].company_id, "CAM")
        self.assertEqual(with_protection[0]["offer"].company_id, "SOL")

    def test_three_traveller_profiles(self):
        # Same offers, different preferences
        profiles = [
            (self.budget, "SOL"),
            (TravellerProfile("09:00", 0.15, 0.50, 0.25, 0.10), "CAM"),
            (TravellerProfile("09:00", 0.20, 0.15, 0.15, 0.50), "VER")
        ]

        for profile, expected_company in profiles:
            with self.subTest(expected=expected_company):
                ranked = rank_offers(self.offers, profile)

                self.assertEqual(
                    ranked[0]["offer"].company_id,
                    expected_company
                )


if __name__ == "__main__":
    unittest.main()
