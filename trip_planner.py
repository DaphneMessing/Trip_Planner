from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime
import openai
from serpapi.google_search import GoogleSearch
import re

app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from the frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)


# API Keys
openai_api_key = "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"
serpapi_key = "bac33b4ea8bb20045ef2bf2de0b101b0cae36c44ae6e7e9a25425b4830748462"

# Models for API request and response
class TripRequest(BaseModel):
    start_date: str  # Format: YYYY-MM-DD
    end_date: str  # Format: YYYY-MM-DD
    budget: int
    trip_type: str  # Options: ski, beach, city


# Utility Functions (existing functions are reused with minimal modification)
def parse_destination(destination):
    match = re.match(r"^\d+\.\s*(.+?), (.+?) \((.+?)\)$", destination)
    if match:
        city, country, airport_code = match.groups()
        return {
            "city": city,
            "country": country,
            "airport_code": airport_code.split("/")[0].strip(),
        }
    return None


def get_travel_destinations(start_date, end_date, budget, trip_type):
    openai.api_key = openai_api_key
    month = start_date.strftime("%B")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a travel planner."},
                {
                    "role": "user",
                    "content": f"Given a budget of ${budget} for a {trip_type} trip in the month of {month}, suggest 2 destinations worldwide. Provide the response in this format:\n1. Destination, Country (Airport Code) - Description\n2. Destination, Country (Airport Code) - Description\n",
                },
            ],
        )
        lines = response["choices"][0]["message"]["content"].split("\n")
        destinations = [
            parse_destination(line.split(" - ")[0].strip())
            for line in lines
            if line.strip()
        ]
        return destinations
    except Exception as e:
        print(f"Error: {e}")
        return []


def search_flights(destinations, start_date, end_date):
    flights = {}
    for destination in destinations:
        code = destination["airport_code"]
        params = {
            "engine": "google_flights",
            "departure_id": "TLV",
            "arrival_id": code,
            "outbound_date": start_date.strftime("%Y-%m-%d"),
            "return_date": end_date.strftime("%Y-%m-%d"),
            "currency": "USD",
            "api_key": serpapi_key,
        }
        search = GoogleSearch(params)
        try:
            results = search.get_json()
            if results and "best_flights" in results:
                flights_data = results["best_flights"]
                cheapest_flight = min(flights_data, key=lambda x: x["price"])
                flights[destination["city"]] = {
                    "city": destination["city"],
                    "country": destination["country"],
                    "price": cheapest_flight["price"],
                    "details": cheapest_flight,
                }
        except Exception as e:
            flights[destination["city"]] = {"error": str(e)}
    return flights


def find_hotels(destinations, flights, budget, start_date, end_date):
    hotels = {}
    # print("Starting hotel search for destinations based on flight data and budget constraints.")  # Debug
    for destination in destinations:
        city = destination['city']
        country = destination['country']
        flight_info= flights.get(city)

        # Check if there is a valid flight to the destination
        if flight_info and flight_info['price']:
            remaining_budget = budget - flight_info['price']
            params = {
                "engine": "google_hotels",
                "q": f"hotels in {city}, {country}",
                "check_in_date": start_date.strftime("%Y-%m-%d"),
                "check_out_date": end_date.strftime("%Y-%m-%d"),
                "adults": "1",
                "currency": "USD",
                "sort_by": "3",  # sort by lowest price
                "max_price": remaining_budget,
                "api_key": serpapi_key
            }
            search = GoogleSearch(params)
            try:
                results = search.get_json()
                if results and 'properties' in results:  # Assuming 'properties' contains the hotel listings
                    most_expensive_hotel = max(results['properties'], key=lambda x: x['total_rate']['extracted_lowest'])
                    hotels[city] = {
                        "name": most_expensive_hotel['name'],
                        "total_rate": most_expensive_hotel['total_rate']['extracted_lowest']
                    }
                else:
                    hotels[city] = {"name": "No hotels available within budget", "total_rate": 0}
            except Exception as e:
                print(f"An error occurred while searching for hotels in {city}: {str(e)}")
                hotels[city] = {"name": "Error retrieving hotel data", "total_rate": 0}
        else:
            print(f"No valid flight found for {city}, skipping hotel search.")
            hotels[city] = {"name": "No valid flight data", "total_rate": 0}

    return hotels



def generate_daily_plan(city, country, start_date, end_date):
    openai.api_key = openai_api_key
    prompt = f"Create a daily plan for {city}, {country} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a travel planner."},
                {"role": "user", "content": prompt},
            ],
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error generating plan: {e}"

@app.post("/plan_trip/")
def plan_trip(request: TripRequest):
    try:
        # Parse dates
        start_date = datetime.datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(request.end_date, "%Y-%m-%d")

        if end_date <= start_date:
            raise HTTPException(
                status_code=400, detail="End date must be after start date."
            )

        # Get destinations
        destinations = get_travel_destinations(
            start_date, end_date, request.budget, request.trip_type
        )
        if not destinations:
            raise HTTPException(status_code=400, detail="No destinations found.")

        # Search for flights and hotels
        flights = search_flights(destinations, start_date, end_date)
        hotels = find_hotels(destinations, flights, request.budget, start_date, end_date)

        # Prepare the final response
        results = []
        for destination in destinations:
            city = destination["city"]
            country = destination["country"]
            flight_info = flights.get(city, {"price": 0, "details": "No flights available"})
            hotel_info = hotels.get(city, {"name": "No hotels available", "total_rate": 0})

            results.append({
                "city": city,
                "country": country,
                "flight_price": flight_info["price"],
                "hotel": hotel_info,
            })

        return {"destinations": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
