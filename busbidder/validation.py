import re
import math
from datetime import datetime

# Custom exception for invalid offers
class InvalidOfferError(ValueError):
    """
    Exception raised when an offer is invalid.
    """
    pass


# Parse a string to a boolean
def parse_bool(value: str) -> bool:
    """
    Convert a string to a boolean.
    """
    value = value.strip().lower()

    if value not in ("true", "false"):
        raise InvalidOfferError(f"Invalid boolean: {value}")

    return value == "true"


# Validate and convert one CSV row
def validate_offer_row(row: dict, company_ids: set, valid_routes: set) -> dict:
    """
    Validate and convert one CSV row.
    Return a dictionary with the correct data types.
    """

    # Check required fields
    required_fields = (
        "offer_id", "company_id", "origin", "destination",
        "travel_date", "departure_time", "arrival_date",
        "arrival_time", "duration_minutes", "price_eur",
        "transfers", "luggage_kg", "changeable",
        "refundable", "seats_available", "rating"
    )

    for field in required_fields:
        if field not in row or row[field] is None or not row[field].strip():
            raise InvalidOfferError(f"Missing value: {field}")

    if set(row) != set(required_fields):
        raise InvalidOfferError("Unexpected CSV columns")

    # Create a copy so the original row is not changed
    offer = row.copy()

    # Validate identifiers
    if not re.fullmatch(r"OFF-[0-9]{4}-[0-9]{4}", offer["offer_id"]):
        raise InvalidOfferError("Invalid offer ID")

    if offer["company_id"] not in company_ids:
        raise InvalidOfferError("Unknown company ID")

    if offer["origin"] != "Madrid":
        raise InvalidOfferError("Origin must be Madrid")

    if (offer["origin"], offer["destination"]) not in valid_routes:
        raise InvalidOfferError("Unknown route")

    # Convert numerical values
    try:
        for field in ("duration_minutes", "transfers", "luggage_kg", "seats_available"):
            offer[field] = int(offer[field])

        for field in ("price_eur", "rating"):
            offer[field] = float(offer[field])

    except ValueError as error:
        raise InvalidOfferError(f"Invalid number: {error}") from error

    # Validate numerical ranges
    if offer["duration_minutes"] <= 0:
        raise InvalidOfferError("Duration must be positive")

    for field in ("transfers", "luggage_kg", "seats_available"):
        if offer[field] < 0:
            raise InvalidOfferError(f"{field} cannot be negative")

    if not math.isfinite(offer["price_eur"]) or offer["price_eur"] < 0:
        raise InvalidOfferError("Invalid price")

    if not math.isfinite(offer["rating"]) or not 1 <= offer["rating"] <= 5:
        raise InvalidOfferError("Rating must be between 1 and 5")

    # Convert booleans
    offer["changeable"] = parse_bool(offer["changeable"])
    offer["refundable"] = parse_bool(offer["refundable"])

    # Validate dates and times
    try:
        departure = datetime.strptime(
            offer["travel_date"] + " " + offer["departure_time"],
            "%Y-%m-%d %H:%M"
        )

        arrival = datetime.strptime(
            offer["arrival_date"] + " " + offer["arrival_time"],
            "%Y-%m-%d %H:%M"
        )

    except ValueError as error:
        raise InvalidOfferError(f"Invalid date or time: {error}") from error

    if arrival <= departure:
        raise InvalidOfferError("Arrival must be after departure")

    # Check that journey duration matches the timestamps
    duration = (arrival - departure).total_seconds() / 60

    if duration != offer["duration_minutes"]:
        raise InvalidOfferError("Journey duration does not match timestamps")

    return offer