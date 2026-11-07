import csv
from busbidder.models import Offer, FareConditions

# Load offers from a CSV file
def load_offers(file_path):
    offers = []

    # Turn the CSV file into a list of dictionaries
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            offers.append(row)

    return offers

# Parse the loaded offers into Offer and FareConditions objects
def parse_offers(loaded_offers):
    parsed_offers = []

    # Transform the list of dictionaries into a list of Offer objects
    for offer in loaded_offers:
        # Create a FareConditions object for each offer
        fare_condition = FareConditions(
            luggage_kg=int(offer['luggage_kg']),
            changeable=offer['changeable'].lower(),
            refundable=offer['refundable'].lower()
        )

        # Create an Offer object for each offer, including the FareConditions object
        parsed_offers.append(Offer(
            offer_id=offer['offer_id'],
            company_id=offer['company_id'],
            origin=offer['origin'],
            destination=offer['destination'],
            travel_date=offer['travel_date'],
            departure_time=offer['departure_time'],
            arrival_date=offer['arrival_date'],
            arrival_time=offer['arrival_time'],
            duration_minutes=int(offer['duration_minutes']),
            price_eur=float(offer['price_eur']),
            transfers=int(offer['transfers']),
            seats_available=int(offer['seats_available']),
            rating=float(offer['rating']),
            fare_conditions=fare_condition
        ))

    return parsed_offers

# Load and parse offers from a CSV file and return a list of Offer objects
def load_and_parse_offers(file_path):
    offers = load_offers(file_path)
    parsed_offers = parse_offers(offers)
    return parsed_offers
