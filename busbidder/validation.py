import re
import math
from datetime import datetime


OFFER_FIELDS = (
    "offer_id", "company_id", "origin", "destination",
    "travel_date", "departure_time", "arrival_date",
    "arrival_time", "duration_minutes", "price_eur",
    "transfers", "luggage_kg", "changeable",
    "refundable", "seats_available", "rating"
)


# Custom exception for invalid offers
class InvalidOfferError(ValueError):
    """Exception raised when an offer is invalid."""
    pass


# Parse a string to a boolean
def parse_bool(value: str) -> bool:
    """Convert a string to a boolean and reject unknown values."""

    if not isinstance(value, str):
        raise InvalidOfferError("Invalid boolean value")

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
    for field in OFFER_FIELDS:
        if field not in row or not isinstance(row[field], str) or not row[field].strip():
            raise InvalidOfferError(f"Missing value: {field}")

    if set(row) != set(OFFER_FIELDS):
        raise InvalidOfferError("Unexpected CSV columns")

    # Create a copy so the original row is not changed
    offer = row.copy()

    # Validate identifiers and references
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

    # Keep a consistent date format for filtering and sorting
    if departure.strftime("%Y-%m-%d %H:%M") != offer["travel_date"] + " " + offer["departure_time"]:
        raise InvalidOfferError("Invalid departure format")

    if arrival.strftime("%Y-%m-%d %H:%M") != offer["arrival_date"] + " " + offer["arrival_time"]:
        raise InvalidOfferError("Invalid arrival format")

    if arrival <= departure:
        raise InvalidOfferError("Arrival must be after departure")

    # Overnight trips are valid if the arrival date is the next day
    duration = (arrival - departure).total_seconds() / 60

    if duration != offer["duration_minutes"]:
        raise InvalidOfferError("Journey duration does not match timestamps")

    return offer


# Validate the user's hard constraints
def validate_travel_request(request):
    """Check that a travel request contains possible values."""

    if not isinstance(request.destination, str) or not request.destination.strip():
        raise ValueError("Destination is required")

    try:
        start = datetime.strptime(request.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(request.end_date, "%Y-%m-%d").date()
    except (ValueError, TypeError) as error:
        raise ValueError("Invalid travel date") from error

    if (start.isoformat(), end.isoformat()) != (request.start_date, request.end_date):
        raise ValueError("Travel dates must use YYYY-MM-DD")

    if end < start:
        raise ValueError("End date cannot be before start date")

    if (not isinstance(request.max_budget, (int, float))
            or not math.isfinite(request.max_budget) or request.max_budget < 0):
        raise ValueError("Invalid maximum budget")

    for field in ("max_transfers", "min_luggage", "max_duration"):
        value = getattr(request, field)
        if type(value) is not int or value < 0:
            raise ValueError(f"Invalid {field}")

    if request.max_duration == 0:
        raise ValueError("Maximum duration must be positive")

    if type(request.require_changeable) is not bool:
        raise ValueError("Changeability requirement must be true or false")


# Validate the user's soft preferences
def validate_traveller_profile(profile):
    """Check the departure time and that weights add up to 1.0."""

    try:
        preferred = datetime.strptime(profile.preferred_departure, "%H:%M")
    except (TypeError, ValueError) as error:
        raise ValueError("Preferred departure must use HH:MM") from error

    if preferred.strftime("%H:%M") != profile.preferred_departure:
        raise ValueError("Preferred departure must use HH:MM")

    weights = (
        profile.price_weight, profile.duration_weight,
        profile.time_weight, profile.flexibility_weight
    )

    if any(not isinstance(weight, (int, float)) or
           not math.isfinite(weight) or weight < 0 or weight > 1
           for weight in weights):
        raise ValueError("Weights must be between 0 and 1")

    if not math.isclose(sum(weights), 1.0, abs_tol=0.000001):
        raise ValueError("Weights must add up to 1.0")
