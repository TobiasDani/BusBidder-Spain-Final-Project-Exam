import math
from datetime import datetime

from busbidder.models import TravelRequest, TravellerProfile
from busbidder.booking import get_available_seats


# Ask for a valid number
def ask_number(question, integer=False, minimum=0, maximum=None):
    """
    Ask for a number until valid input is given.
    """

    while True:
        try:
            value = input(question).strip()
            number = int(value) if integer else float(value)

            if not math.isfinite(number) or number < minimum:
                raise ValueError()

            if maximum is not None and number > maximum:
                raise ValueError()

            return number

        except ValueError:
            print("Invalid number. Please try again.")


# Ask for a valid date
def ask_date(question):
    """
    Ask for a date in YYYY-MM-DD format.
    """

    while True:
        try:
            value = input(question).strip()
            date = datetime.strptime(value, "%Y-%m-%d")
            return date.strftime("%Y-%m-%d")

        except ValueError:
            print("Invalid date. Use YYYY-MM-DD.")


# Ask a yes/no question
def ask_yes_no(question):
    """
    Return True for yes and False for no.
    """

    while True:
        answer = input(question).strip().lower()

        if answer in ("y", "yes"):
            return True

        if answer in ("n", "no"):
            return False

        print("Please enter y or n.")


# Ask for travel requirements
def ask_travel_request(offers):
    """
    Ask the user for hard constraints.
    Return a TravelRequest object.
    """

    print("\n--- Travel Requirements ---")

    # Show available destinations
    destinations = sorted(set(offer.destination for offer in offers))

    for i, destination in enumerate(destinations, start=1):
        print(f"{i}. {destination}")

    choice = ask_number(
        "Choose destination: ",
        integer=True,
        minimum=1,
        maximum=len(destinations)
    )

    destination = destinations[choice - 1]

    # Show available travel dates
    dates = sorted(
        set(offer.travel_date for offer in offers
            if offer.destination == destination)
    )

    print(f"Available dates: {dates[0]} to {dates[-1]}")

    # Ask for travel dates
    while True:
        start_date = ask_date("Start date (YYYY-MM-DD): ")
        end_date = ask_date("End date (YYYY-MM-DD): ")

        if start_date <= end_date:
            break

        print("End date cannot be before start date.")

    # Ask for other hard constraints
    max_budget = ask_number("Maximum budget (€): ")
    max_transfers = ask_number("Maximum transfers: ", integer=True)
    min_luggage = ask_number("Required luggage (kg): ", integer=True)
    max_duration = ask_number(
        "Maximum duration (minutes): ",
        integer=True,
        minimum=1
    )
    require_changeable = ask_yes_no("Require changeable ticket? (y/n): ")

    return TravelRequest(
        destination, start_date, end_date,
        max_budget, max_transfers, min_luggage,
        max_duration, require_changeable
    )


# Ask for traveller preferences
def ask_traveller_profile():
    """
    Let the user choose a preset or custom profile.
    Return a TravellerProfile object.
    """

    print("\n--- Traveller Profile ---")
    print("1. Budget traveller")
    print("2. Business traveller")
    print("3. Flexible tourist")
    print("4. Custom preferences")

    choice = ask_number(
        "Choose profile: ",
        integer=True,
        minimum=1,
        maximum=4
    )

    # Preset weights: price, duration, time, flexibility
    profiles = {
        1: [60, 15, 10, 15],
        2: [15, 50, 25, 10],
        3: [20, 15, 15, 50]
    }

    if choice == 4:
        print("\nEnter weights as percentages (total must be 100).")

        while True:
            weights = [
                ask_number("Price (%): ", maximum=100),
                ask_number("Duration (%): ", maximum=100),
                ask_number("Departure time (%): ", maximum=100),
                ask_number("Flexibility (%): ", maximum=100)
            ]

            if abs(sum(weights) - 100) < 0.000001:
                break

            print("Weights must add up to 100%. Try again.")

    else:
        weights = profiles[choice]

    # Ask for preferred departure time
    while True:
        try:
            value = input("Preferred departure (HH:MM) [09:00]: ").strip()
            preferred = datetime.strptime(value or "09:00", "%H:%M")
            preferred_departure = preferred.strftime("%H:%M")
            break

        except ValueError:
            print("Invalid time. Use HH:MM.")

    return TravellerProfile(
        preferred_departure,
        weights[0] / 100,
        weights[1] / 100,
        weights[2] / 100,
        weights[3] / 100
    )


# Display ranked offers
def display_offers(ranked_offers, bookings):
    """
    Display offers with their values and scores.
    """

    print(f"\n--- Found {len(ranked_offers)} Matching Offers ---")

    for i, result in enumerate(ranked_offers, start=1):
        offer = result["offer"]
        conditions = offer.fare_conditions

        print(f"\n{i}. {offer.company_id} | €{offer.price_eur:.2f}")
        print(f"   {offer.travel_date} {offer.departure_time}"
              f" -> {offer.arrival_date} {offer.arrival_time}")

        print(f"   Duration: {offer.duration_minutes} min"
              f" | Transfers: {offer.transfers}"
              f" | Luggage: {conditions.luggage_kg} kg")

        print(f"   Changeable: {conditions.changeable}"
              f" | Refundable: {conditions.refundable}"
              f" | Rating: {offer.rating}")

        print(f"   Available seats: {get_available_seats(offer, bookings)}")

        print(
            f"   Scores: Price {result['price_score']:.1f}"
            f" | Duration {result['duration_score']:.1f}"
            f" | Time {result['time_score']:.1f}"
            f" | Flexibility {result['flexibility_score']:.1f}"
        )

        print(f"   TOTAL SCORE: {result['total_score']:.2f}/100")


# Let the user choose an offer
def choose_offer(ranked_offers):
    """
    Return the selected Offer object, or None to cancel.
    """

    print("\n0. Back to menu")

    choice = ask_number(
        "Choose offer to book: ",
        integer=True,
        minimum=0,
        maximum=len(ranked_offers)
    )

    if choice == 0:
        return None

    return ranked_offers[choice - 1]["offer"]