import csv
import logging

from busbidder.models import Offer, FareConditions
from busbidder.validation import InvalidOfferError, validate_offer_row, parse_bool, OFFER_FIELDS


# Load rows from a CSV file
def _load_offers(file_path: str, expected_fields=None) -> list[dict]:
    """
    Load rows from a CSV file and return a list of dictionaries.
    """

    offers = []

    # Turn the CSV file into a list of dictionaries
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise InvalidOfferError(f"Missing or duplicate CSV header: {file_path}")

        if expected_fields is not None and set(reader.fieldnames) != set(expected_fields):
            raise InvalidOfferError(f"Missing or unexpected CSV columns: {file_path}")

        for row in reader:
            offers.append(row)

    return offers


# Load valid company IDs
def _load_companies(file_path: str) -> set:
    """Load valid company IDs from a CSV file."""

    company_ids = set()

    for row in _load_offers(file_path, ("company_id", "company_name", "service_profile")):
        company_id = row.get('company_id')
        company_name = row.get('company_name')

        if not company_id or not company_name or not company_id.strip() or not company_name.strip():
            raise InvalidOfferError("Invalid company data")

        if company_id in company_ids:
            raise InvalidOfferError(f"Duplicate company ID: {company_id}")

        company_ids.add(company_id)

    if not company_ids:
        raise InvalidOfferError("No companies found")

    return company_ids


# Load valid destinations
def _load_destinations(file_path: str) -> set:
    """Load valid routes from a CSV file."""

    valid_routes = set()
    destination_ids = set()

    for row in _load_offers(file_path, (
        "destination_id", "origin", "destination", "approx_road_km",
        "base_duration_minutes", "coastal"
    )):
        destination_id = row.get('destination_id')
        origin = row.get('origin')
        destination = row.get('destination')

        if not destination_id or not origin or not destination:
            raise InvalidOfferError("Invalid destination data")

        if origin != "Madrid":
            raise InvalidOfferError("Invalid origin in destinations")

        route = (origin, destination)

        if route in valid_routes or destination_id in destination_ids:
            raise InvalidOfferError(f"Duplicate destination: {destination}")

        # Check that the supporting reference data is sensible
        try:
            if int(row['approx_road_km']) <= 0 or int(row['base_duration_minutes']) <= 0:
                raise ValueError("Distance and duration must be positive")
            parse_bool(row['coastal'])
        except (ValueError, TypeError, KeyError) as error:
            raise InvalidOfferError(f"Invalid destination data: {error}") from error

        valid_routes.add(route)
        destination_ids.add(destination_id)

    if not valid_routes:
        raise InvalidOfferError("No destinations found")

    return valid_routes


# Parse the loaded offers into Offer and FareConditions objects
def _parse_offers(loaded_offers: list[dict], company_ids: set, valid_routes: set) -> list[Offer]:
    """Parse the loaded offers into Offer and FareConditions objects."""

    parsed_offers = []
    seen_offer_ids = set()
    logger = logging.getLogger(__name__)

    # Transform each valid dictionary into an Offer object
    for line_number, offer in enumerate(loaded_offers, start=2):
        try:
            offer = validate_offer_row(offer, company_ids, valid_routes)

            if offer['offer_id'] in seen_offer_ids:
                raise InvalidOfferError(f"Duplicate offer ID: {offer['offer_id']}")

        except InvalidOfferError as error:
            logger.warning("CSV line %s: %s", line_number, error)
            continue

        # Create a FareConditions object for each offer
        fare_condition = FareConditions(
            luggage_kg=offer['luggage_kg'],
            changeable=offer['changeable'],
            refundable=offer['refundable']
        )

        # Create an Offer object, including its FareConditions
        parsed_offers.append(Offer(
            offer_id=offer['offer_id'],
            company_id=offer['company_id'],
            origin=offer['origin'],
            destination=offer['destination'],
            travel_date=offer['travel_date'],
            departure_time=offer['departure_time'],
            arrival_date=offer['arrival_date'],
            arrival_time=offer['arrival_time'],
            duration_minutes=offer['duration_minutes'],
            price_eur=offer['price_eur'],
            transfers=offer['transfers'],
            seats_available=offer['seats_available'],
            rating=offer['rating'],
            fare_conditions=fare_condition
        ))

        seen_offer_ids.add(offer['offer_id'])

    rejected = len(loaded_offers) - len(parsed_offers)
    logger.info("Loaded %s offers, rejected %s", len(parsed_offers), rejected)

    if rejected:
        logger.warning("Rejected %s of %s offers", rejected, len(loaded_offers))

    return parsed_offers


# Load and parse offers from a CSV file
def load_and_parse_offers(
    file_path: str,
    companies_path: str = "data/companies.csv",
    destinations_path: str = "data/destinations.csv"
) -> list[Offer]:
    """Load companies, destinations and offers, and return valid Offer objects."""

    company_ids = _load_companies(companies_path)
    valid_routes = _load_destinations(destinations_path)

    offers = _load_offers(file_path, OFFER_FIELDS)
    parsed_offers = _parse_offers(offers, company_ids, valid_routes)

    return parsed_offers
