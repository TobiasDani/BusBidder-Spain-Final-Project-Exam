class Offer:
    def __init__(
        self, offer_id, company_id, origin, destination, travel_date, departure_time, arrival_date, 
        arrival_time, duration_minutes, price_eur, transfers, seats_available, rating, fare_conditions):
        
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

class FareConditions:
    def __init__(self, luggage_kg, changeable, refundable):
        self.luggage_kg = luggage_kg
        self.changeable = changeable
        self.refundable = refundable

class TravelRequests:
    def __init__(self):
        pass

class TravellerProfile:
    def __init__(self):
        pass

class Booking:
    def __init__(self):
        pass
