# BusBidder Spain - Final Project

## Project information

- Course: ACIT4420 - Problem-Solving with Scripting
- Student name: Tobias Danielsen
- Student number: s385486
- Repository: [BusBidder Spain](https://github.com/TobiasDani/BusBidder-Spain-Final-Project-Exam)

## Short description

BusBidder Spain is a Python program that compares bus offers from Madrid to different destinations in Spain.

The program reads offers from CSV files, checks the data and removes offers that do not meet the traveller's requirements. The remaining offers are ranked based on price, travel time, departure time and ticket flexibility.

The user can choose a traveller profile, set their own preferences and make a simulated booking. No real tickets or payments are involved.

## Project structure

The main application code is stored in the `busbidder` package.

- `models.py`: contains the Offer, FareConditions, TravelRequest, TravellerProfile and Booking classes
- `data.py`: loads the CSV files and creates Offer objects
- `validation.py`: validates offers, travel requests and traveller profiles
- `ranking.py`: filters, scores and ranks offers
- `booking.py`: checks available seats and saves bookings
- `cli.py`: handles user input and displays the results
- `main.py`: runs the application and connects the different parts

The `data` folder contains the CSV files, and `tests` contains the automated tests.

## Data and validation

The dataset is simulated and contains five fictional bus companies, 15 destinations and 90 offers. The departure dates are July 12 to 14, 2027.

The program checks required fields, number ranges, dates, journey durations, offer IDs, duplicate IDs and whether companies and destinations exist. Invalid offer rows are skipped and logged in `logs/busbidder.log`.

An offer with no available seats is still valid data, but it cannot be recommended or booked.

## Filtering and ranking

The program first filters offers using the traveller's requirements, including destination, dates, budget, transfers, luggage allowance, maximum duration, changeability and available seats.

The remaining offers are scored using four criteria:

- Price
- Journey duration
- Difference from the preferred departure time
- Ticket flexibility

Min-Max normalization converts the first three criteria to scores between 0 and 100. Flexibility receives 0, 50 or 100 points depending on the ticket conditions. The scores are then combined using the traveller's chosen weights.

There are three preset profiles (Budget, Business and Flexible Tourist), or the user can enter custom weights.

To reduce the effect of unusually expensive tickets, price normalization uses an optional IQR-based limit by default when at least five offers remain. This only affects ranking scores, not ticket prices.

## Booking

The user can select an offer and confirm a simulated booking.

Bookings are saved in `data/bookings.csv` with a unique reference, the original price and ticket conditions. Available seats are calculated from the initial capacity minus existing bookings, and checked again before a new booking is saved.

## Running the program

The project uses Python 3.10 or later and only the standard library. No additional packages are required.

From the project root, run:

```bash
python main.py
```

If your system uses `python3`, use `python3 main.py` instead.

The program uses the CSV files in `data/`. Keep the header in `bookings.csv` even if there are no bookings yet.

## Tests

Run the automated tests with:

```bash
python -m unittest discover -s tests -v
```

The 11 tests cover validation, hard constraints, equal values, outliers, traveller profiles, booking capacity, saved booking details and the full workflow from CSV to booking.

The tests use temporary booking files so they do not change `data/bookings.csv`.

## Known limitations

- All companies, prices and timetables are simulated.
- Ranking depends on the user's weights and the available offers. The highest score is not necessarily the best choice for everyone.
- The IQR-based price limit can reduce the influence of outliers, but may also hide meaningful price differences.
- CSV booking is intended for a single-user prototype and does not protect against simultaneous bookings.
- Company ratings are displayed but are not included in the ranking score.

## AI use

Generative AI was used to assist with parts of the code, synthetic data generation, review and test preparation. Its use and verification will also be described in the final report.