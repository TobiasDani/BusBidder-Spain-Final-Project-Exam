import csv
import logging
import math
import re
from datetime import datetime
from functools import wraps

from busbidder.models import Booking, FareConditions
from busbidder.validation import parse_bool


# Custom exception for booking errors
class BookingError(ValueError):
    pass


# Decorator: log each booking without repeating logging code inside book_offer
# A decorator wraps a function with additional behavior. This is our metaprogramming example.
def log_booking(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            booking = function(*args, **kwargs)
            logging.info("Booking created: %s", booking.booking_reference)
            return booking

        except (BookingError, OSError) as error:
            logging.error("Booking failed: %s", error)
            raise

    return wrapper


# Load existing bookings from CSV
def load_bookings(file_path="data/bookings.csv", valid_offer_ids=None) -> list[Booking]:
    """Load and validate existing bookings."""

    bookings = []
    references = set()
    required_fields = (
        "booking_reference", "offer_id", "booked_at", "price_paid_eur",
        "changeable", "refundable", "luggage_kg"
    )

    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        if reader.fieldnames is None or (len(reader.fieldnames) != len(required_fields)
                                        or set(reader.fieldnames) != set(required_fields)):
            raise BookingError("Invalid bookings CSV header")

        for line_number, row in enumerate(reader, start=2):
            try:
                if any(not isinstance(row.get(field), str) or not row[field].strip()
                       for field in required_fields) or set(row) != set(required_fields):
                    raise ValueError("Missing or unexpected booking fields")

                reference = row['booking_reference']

                if not re.fullmatch(r"BUS-[0-9]{4}[A-Z]", reference):
                    raise ValueError("Invalid booking reference")

                if reference in references:
                    raise ValueError("Duplicate booking reference")

                if not re.fullmatch(r"OFF-[0-9]{4}-[0-9]{4}", row['offer_id']):
                    raise ValueError("Invalid offer ID")

                if valid_offer_ids is not None and row['offer_id'] not in valid_offer_ids:
                    raise ValueError("Booking references an unknown offer")

                datetime.fromisoformat(row['booked_at'])

                price = float(row['price_paid_eur'])
                luggage = int(row['luggage_kg'])

                if not math.isfinite(price) or price < 0 or luggage < 0:
                    raise ValueError("Invalid booking values")

                conditions = FareConditions(
                    luggage_kg=luggage,
                    changeable=parse_bool(row['changeable']),
                    refundable=parse_bool(row['refundable'])
                )

                bookings.append(Booking(
                    booking_reference=reference,
                    offer_id=row['offer_id'],
                    booked_at=row['booked_at'],
                    price_paid_eur=price,
                    fare_conditions=conditions
                ))

                references.add(reference)

            except (ValueError, KeyError, TypeError, AttributeError) as error:
                raise BookingError(
                    f"Invalid booking on CSV line {line_number}: {error}"
                ) from error

    return bookings


# Calculate remaining seats
def get_available_seats(offer, bookings: list[Booking]) -> int:
    """Calculate available seats after existing bookings."""

    reserved = sum(
        1 for booking in bookings
        if booking.offer_id == offer.offer_id
    )

    return offer.seats_available - reserved


# Book an offer and save it to CSV
@log_booking
def book_offer(offer, file_path="data/bookings.csv") -> Booking:
    """Create and save a booking if seats are available."""

    # Reload at booking time to avoid relying on an old seat count
    bookings = load_bookings(file_path)

    if get_available_seats(offer, bookings) <= 0:
        raise BookingError("No available seats")

    # Generate a unique booking reference
    references = {booking.booking_reference for booking in bookings}

    for number in range(1, 10000):
        reference = f"BUS-{number:04d}A"
        if reference not in references:
            break
    else:
        raise BookingError("No booking references available")

    # Save a copy of the original fare conditions
    conditions = FareConditions(
        luggage_kg=offer.fare_conditions.luggage_kg,
        changeable=offer.fare_conditions.changeable,
        refundable=offer.fare_conditions.refundable
    )

    booking = Booking(
        booking_reference=reference,
        offer_id=offer.offer_id,
        booked_at=datetime.now().isoformat(timespec="seconds"),
        price_paid_eur=offer.price_eur,
        fare_conditions=conditions
    )

    # Append the booking without changing the original offers
    with open(file_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        writer.writerow([
            booking.booking_reference,
            booking.offer_id,
            booking.booked_at,
            booking.price_paid_eur,
            booking.fare_conditions.changeable,
            booking.fare_conditions.refundable,
            booking.fare_conditions.luggage_kg
        ])

    return booking
