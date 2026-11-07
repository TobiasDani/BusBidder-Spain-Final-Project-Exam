import math
from datetime import datetime

from busbidder.models import TravelRequest, TravellerProfile
from busbidder.booking import get_available_seats
from busbidder.validation import validate_travel_request, validate_traveller_profile


# Ask for a valid number
def ask_number(question, integer=False, minimum=0, maximum=None, default=None):
    """Ask for a number until valid input is given."""

    while True:
        try:
            value = input(question).strip()

            # Press Enter to use the suggested value
            if not value and default is not None:
                value = str(default)

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
    """Ask for a date in YYYY-MM-DD format."""

    while True:
        try:
            value = input(question).strip()
            date = datetime.strptime(value, "%Y-%m-%d")

            if date.strftime("%Y-%m-%d") != value:
                raise ValueError()

            return value

        except ValueError:
            print("Invalid date. Use YYYY-MM-DD.")


# Ask a yes/no question
def ask_yes_no(question):
    """Return True for yes and False for no."""

    while True:
        answer = input(question).strip().lower()

        if answer in ("y", "yes"):
            return True

        if answer in ("n", "no"):
            return False

        print("Please enter y or n.")


# Ask for travel requirements
def ask_travel_request(offers):
    """Ask the user for hard constraints and return a TravelRequest."""

    print("\n--- Travel Requirements (must be satisfied) ---")

    # Show available destinations
    destinations = sorted(set(offer.destination for offer in offers))

    for i, destination in enumerate(destinations, start=1):
        print(f"{i}. {destination}")

    choice = ask_number(
        "Choose destination: ", integer=True,
        minimum=1, maximum=len(destinations)
    )
    destination = destinations[choice - 1]

    # Show available dates for that destination
    destination_offers = [offer for offer in offers if offer.destination == destination]
    dates = sorted(set(offer.travel_date for offer in destination_offers))

    print("Available departure dates:", ", ".join(dates))

    while True:
        start_date = ask_date("Start date (YYYY-MM-DD): ")
        end_date = ask_date("End date (YYYY-MM-DD): ")

        if start_date > end_date:
            print("End date cannot be before start date.")
            continue

        if start_date < dates[0] or end_date > dates[-1]:
            print(f"Choose dates between {dates[0]} and {dates[-1]}.")
            continue

        break

    # Only use offers in the selected date window for helpful examples
    relevant_offers = [
        offer for offer in destination_offers
        if start_date <= offer.travel_date <= end_date
    ]

    if not relevant_offers:
        print("No departures on these dates. Please search again.")
        return None

    lowest_price = min(offer.price_eur for offer in relevant_offers)
    highest_price = max(offer.price_eur for offer in relevant_offers)
    longest_duration = max(offer.duration_minutes for offer in relevant_offers)
    highest_transfers = max(offer.transfers for offer in relevant_offers)

    print(f"Offer prices range from €{lowest_price:.2f} to €{highest_price:.2f}.")
    print("Press Enter to use a suggested value in brackets.")

    max_budget = ask_number(
        f"Maximum budget (€) [{highest_price:.2f}]: ",
        default=highest_price
    )
    max_transfers = ask_number(
        f"Maximum transfers [{highest_transfers}]: ",
        integer=True, default=highest_transfers
    )
    min_luggage = ask_number(
        "Required luggage (kg) [0]: ", integer=True, default=0
    )
    max_duration = ask_number(
        f"Maximum duration (minutes) [{longest_duration}]: ",
        integer=True, minimum=1, default=longest_duration
    )
    require_changeable = ask_yes_no("Require changeable ticket? (y/n): ")

    request = TravelRequest(
        destination, start_date, end_date,
        max_budget, max_transfers, min_luggage,
        max_duration, require_changeable
    )

    validate_travel_request(request)
    return request


# Ask for traveller preferences
def ask_traveller_profile():
    """Let the user choose a preset or custom TravellerProfile."""

    print("\n--- Traveller Profile (preferences) ---")
    print("1. Budget traveller      60% price, 15% duration, 10% time, 15% flexibility")
    print("2. Business traveller    15% price, 50% duration, 25% time, 10% flexibility")
    print("3. Flexible tourist      20% price, 15% duration, 15% time, 50% flexibility")
    print("4. Custom preferences")

    choice = ask_number("Choose profile: ", integer=True, minimum=1, maximum=4)

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

            if math.isclose(sum(weights), 100, abs_tol=0.000001):
                break

            print("Weights must add up to 100%. Try again.")

    else:
        weights = profiles[choice]

    # Ask for preferred departure time
    while True:
        try:
            value = input("Preferred departure (HH:MM) [09:00]: ").strip()
            value = value or "09:00"
            preferred = datetime.strptime(value, "%H:%M")

            if preferred.strftime("%H:%M") != value:
                raise ValueError()

            break

        except ValueError:
            print("Invalid time. Use HH:MM.")

    profile = TravellerProfile(
        value,
        weights[0] / 100,
        weights[1] / 100,
        weights[2] / 100,
        weights[3] / 100
    )

    validate_traveller_profile(profile)
    return profile


# Display ranked offers
def display_offers(ranked_offers, bookings):
    """Display offers with their original values and their scores."""

    print(f"\n--- Found {len(ranked_offers)} Matching Offers ---")
    print("Scores are relative to these offers; extreme prices are limited for scoring only.")

    for i, result in enumerate(ranked_offers, start=1):
        offer = result["offer"]
        conditions = offer.fare_conditions

        print(f"\n{i}. {offer.company_id} | €{offer.price_eur:.2f} | {offer.offer_id}")
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
    """Return the selected Offer object, or None to cancel."""

    print("\n0. Back to menu")

    choice = ask_number(
        "Choose offer to book: ", integer=True,
        minimum=0, maximum=len(ranked_offers)
    )

    if choice == 0:
        return None

    return ranked_offers[choice - 1]["offer"]
