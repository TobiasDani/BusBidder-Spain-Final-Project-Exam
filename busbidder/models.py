class FareConditions:
    """
    Represents the fare conditions for a travel offer.

    Attributes:
        luggage_kg (int): The maximum luggage weight allowed in kilograms.
        changeable (str): Indicates if the fare is changeable.
        refundable (str): Indicates if the fare is refundable.
    """
    def __init__(self, luggage_kg: int, changeable: str, refundable: str):
        self.luggage_kg = luggage_kg
        self.changeable = changeable
        self.refundable = refundable

class Offer:
    """
    Represents a travel offer.

    Attributes:
        offer_id (str): The unique identifier for the offer.
        company_id (str): The identifier for the company offering the travel.
        origin (str): The starting location of the travel.
        destination (str): The final destination of the travel.
        travel_date (str): The date of the travel.
        departure_time (str): The time of departure.
        arrival_date (str): The date of arrival.
        arrival_time (str): The time of arrival.
        duration_minutes (int): The duration of the travel in minutes.
        price_eur (float): The price of the travel in euros.
        transfers (int): The number of transfers required for the travel.
        seats_available (int): The number of seats available for the travel.
        rating (float): The rating of the travel offer.
        fare_conditions (FareConditions): The fare conditions for the travel offer.
    """
    def __init__(
        self, offer_id: str, company_id: str, origin: str, destination: str, travel_date: str, departure_time: str, arrival_date: str, 
        arrival_time: str, duration_minutes: int, price_eur: float, transfers: int, seats_available: int, rating: float, fare_conditions: FareConditions):
        
        self.offer_id = offer_id
        self.company_id = company_id
        self.origin = origin
        self.destination = destination
        self.travel_date = travel_date
        self.departure_time = departure_time
        self.arrival_date = arrival_date
        self.arrival_time = arrival_time
        self.duration_minutes = duration_minutes
        self.price_eur = price_eur
        self.transfers = transfers
        self.seats_available = seats_available
        self.rating = rating

        self.fare_conditions = fare_conditions

class TravelRequest:
    """
    Represents a travel request made by a user. 
    Offers that don't meet the criteria of the travel request will be rejected completely.

    Attributes:
        destination (str): The desired destination for the travel.
        start_date (str): The start date of the travel.
        end_date (str): The end date of the travel.
        max_budget (float): The maximum budget for the travel.
        max_transfers (int): The maximum number of transfers allowed for the travel.
        min_luggage (int): The minimum luggage weight required for the travel.
        max_duration (int): The maximum duration allowed for the travel in minutes.
        require_changeable (bool): Indicates if changeable fare is required for the travel.
    """
    def __init__(
        self, destination: str, start_date: str, end_date: str, max_budget: float, max_transfers: int, min_luggage: int, max_duration: int, require_changeable: bool):
        self.destination = destination
        self.start_date = start_date
        self.end_date = end_date
        self.max_budget = max_budget
        self.max_transfers = max_transfers
        self.min_luggage = min_luggage
        self.max_duration = max_duration
        self.require_changeable = require_changeable

class TravellerProfile:
    def __init__(self):
        pass

class Booking:
    def __init__(self):
        pass
