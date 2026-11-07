from datetime import datetime
from statistics import quantiles
import math

from busbidder.models import Offer, TravelRequest, TravellerProfile
from busbidder.booking import get_available_seats
from busbidder.validation import validate_travel_request, validate_traveller_profile


# Filter offers based on the user's hard constraints
def filter_offers(offers: list[Offer], request: TravelRequest, bookings: list) -> list[Offer]:
    """Return offers that meet all requirements of the travel request."""

    validate_travel_request(request)
    filtered_offers = []

    # Reject offers that do not meet all hard constraints
    for offer in offers:
        if offer.destination != request.destination:
            continue

        if not request.start_date <= offer.travel_date <= request.end_date:
            continue

        if offer.price_eur > request.max_budget:
            continue

        if offer.transfers > request.max_transfers:
            continue

        if offer.fare_conditions.luggage_kg < request.min_luggage:
            continue

        if offer.duration_minutes > request.max_duration:
            continue

        if request.require_changeable and not offer.fare_conditions.changeable:
            continue

        if get_available_seats(offer, bookings) <= 0:
            continue

        filtered_offers.append(offer)

    return filtered_offers


# Normalize values to a scale from 0 to 100
def normalize_scores(
    values: list[float], lower_is_better: bool = True,
    limit_outliers: bool = False
) -> list[float]:
    """
    Normalize values to scores between 0 and 100.
    Optionally limit extreme values before Min-Max normalization.
    """

    if not values:
        return []

    if any(not isinstance(value, (int, float)) or not math.isfinite(value)
           for value in values):
        raise ValueError("Scores must contain finite numbers")

    values = list(values)

    # Limit unusually high or low values using the IQR rule.
    # This prevents a single very expensive ticket from flattening other prices.
    if limit_outliers and len(values) >= 5:
        q1, _, q3 = quantiles(values, n=4, method="inclusive")
        spread = q3 - q1

        if spread > 0:
            lower = q1 - 1.5 * spread
            upper = q3 + 1.5 * spread
            values = [max(lower, min(value, upper)) for value in values]

    minimum = min(values)
    maximum = max(values)

    # All values are equal
    if minimum == maximum:
        return [100.0] * len(values)

    scores = []

    for value in values:
        score = (value - minimum) / (maximum - minimum) * 100

        if lower_is_better:
            score = 100 - score

        scores.append(score)

    return scores


# Calculate weighted scores for all offers
def calculate_scores(
    offers: list[Offer], profile: TravellerProfile,
    limit_price_outliers: bool = True
) -> list[dict]:
    """
    Calculate scores based on the traveller's preferences.
    Return each offer with its individual scores and total score.
    """

    validate_traveller_profile(profile)

    if not offers:
        return []

    # Get prices and durations
    prices = [offer.price_eur for offer in offers]
    durations = [offer.duration_minutes for offer in offers]

    # Calculate departure time differences in minutes
    preferred = datetime.strptime(profile.preferred_departure, "%H:%M")
    preferred_minutes = preferred.hour * 60 + preferred.minute

    time_differences = []
    flexibility_scores = []

    for offer in offers:
        departure = datetime.strptime(offer.departure_time, "%H:%M")
        departure_minutes = departure.hour * 60 + departure.minute

        difference = abs(departure_minutes - preferred_minutes)
        time_differences.append(min(difference, 1440 - difference))

        # 50 points for changeable, 50 for refundable
        flexibility = (
            50 * offer.fare_conditions.changeable
            + 50 * offer.fare_conditions.refundable
        )
        flexibility_scores.append(flexibility)

    # Normalize only the feasible offers, not the entire CSV file
    price_scores = normalize_scores(prices, limit_outliers=limit_price_outliers)
    duration_scores = normalize_scores(durations)
    time_scores = normalize_scores(time_differences)

    # Calculate total scores
    results = []

    for i, offer in enumerate(offers):
        total_score = (
            price_scores[i] * profile.price_weight
            + duration_scores[i] * profile.duration_weight
            + time_scores[i] * profile.time_weight
            + flexibility_scores[i] * profile.flexibility_weight
        )

        results.append({
            "offer": offer,
            "price_score": price_scores[i],
            "duration_score": duration_scores[i],
            "time_score": time_scores[i],
            "flexibility_score": flexibility_scores[i],
            "total_score": total_score
        })

    return results


# Rank offers based on their weighted scores
def rank_offers(
    offers: list[Offer], profile: TravellerProfile,
    limit_price_outliers: bool = True
) -> list[dict]:
    """Rank offers from highest to lowest score."""

    scored_offers = calculate_scores(offers, profile, limit_price_outliers)

    # Sort by total score, then price and offer ID if scores are equal
    ranked_offers = sorted(
        scored_offers,
        key=lambda result: (
            -round(result["total_score"], 8),
            result["offer"].price_eur,
            result["offer"].offer_id
        )
    )

    return ranked_offers


# Explain why an offer was recommended
def explain_recommendation(result: dict, profile: TravellerProfile) -> str:
    """Explain an offer's strengths and weaknesses based on its scores."""

    offer = result["offer"]

    scores = {
        "price": result["price_score"],
        "duration": result["duration_score"],
        "departure time": result["time_score"],
        "flexibility": result["flexibility_score"]
    }

    weights = {
        "price": profile.price_weight,
        "duration": profile.duration_weight,
        "departure time": profile.time_weight,
        "flexibility": profile.flexibility_weight
    }

    # Calculate each criterion's contribution to the total
    contributions = {
        name: score * weights[name]
        for name, score in scores.items()
    }

    strongest = max(contributions, key=contributions.get)

    # A zero-weight criterion should not be presented as a drawback
    relevant = [name for name in scores if weights[name] > 0 and name != strongest]
    if not relevant:
        relevant = [name for name in scores if weights[name] > 0]

    weakest = min(relevant, key=scores.get)

    return (
        f"Recommended: {offer.company_id} (€{offer.price_eur:.2f})\n"
        f"Total score: {result['total_score']:.2f}/100\n"
        f"Strongest weighted contribution: {strongest} "
        f"({contributions[strongest]:.1f} points).\n"
        + (f"Potential drawback: {weakest} (score: {scores[weakest]:.1f}/100)."
           if scores[weakest] < 100
           else "Drawback: these scores only compare the currently available offers.")
    )
