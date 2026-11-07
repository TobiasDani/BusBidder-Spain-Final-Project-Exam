class FareConditions:
    def __init__(self, luggage_kg: int, changeable: str, refundable: str):
        self.luggage_kg = luggage_kg
        self.changeable = changeable
        self.refundable = refundable

class Offer:
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

class TravelRequests:
    def __init__(self):
        pass

class TravellerProfile:
    def __init__(self):
        pass

class Booking:
    def __init__(self):
        pass
