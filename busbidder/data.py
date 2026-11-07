import csv
from busbidder.models import Offer
from busbidder.models import FareConditions

def load_offers(file_path):
    offers = []

    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            offers.append(row)

    return offers

def parse_offers(loaded_offers):
    parsed_offers = []

    for offer in loaded_offers:
        fare_condition = FareConditions(
            luggage_kg=int(offer['luggage_kg']),
            changeable=offer['changeable'].lower(),
            refundable=offer['refundable'].lower()
        )

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

def load_and_parse_offers(file_path):
    offers = load_offers(file_path)
    parsed_offers = parse_offers(offers)
    return parsed_offers
