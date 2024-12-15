import openai
from serpapi.google_search import GoogleSearch
import datetime

openai_api_key = 'sk-proj-5EFH4cZPnydPbqte06PQT3BlbkFJytQlGYnhClqkCuEmqjsI'
serpapi_key = 'bac33b4ea8bb20045ef2bf2de0b101b0cae36c44ae6e7e9a25425b4830748462'

def get_travel_destinations(start_date, end_date, budget, trip_type):
    openai.api_key = openai_api_key
    month = start_date.strftime("%B")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                    {"role": "system", "content": "You are a travel planner."},
                    {"role": "user", "content": f"Given a budget of ${budget} for a {trip_type} trip in the month of {month}, suggest 2 destinations worldwide."}
                ]
        )
        # Assuming the response content is plain text with comma-separated values.
        destinations = [destination.strip() for destination in response.choices[0].message['content'].split(',')]
        return destinations
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []
    

def search_flights(destinations, start_date, end_date):
    flights = {}
    for destination in destinations:
        params = {
            "engine": "google_flights",
            "departure_id": "TLV",
            "arrival_id": destination,
            "outbound_date": start_date.strftime("%Y-%m-%d"),
            "return_date": end_date.strftime("%Y-%m-%d"),
            "currency": "USD",  
            "api_key": serpapi_key
        }
        search = GoogleSearch(params)
        results = search.get_json()  # Assuming get_json() fetches the results as JSON
        if results and 'flights_results' in results:
            cheapest_flight = min(results['flights_results'], key=lambda x: x['price'])
            flights[destination] = cheapest_flight
    return flights


def find_hotels(destinations, budget, start_date, end_date):
    hotels = {}
    for destination in destinations:
        params = {
            "engine": "google_hotels",
            "q": destination,
            "check_in_date": start_date.strftime("%Y-%m-%d"),
            "check_out_date": end_date.strftime("%Y-%m-%d"),
            "currency": "USD",
            "sort_by": "3",  # sort by lowest price
            # "max_price": budget,
            "api_key": serpapi_key
        }
        search = GoogleSearch(params)
        results = search.get_json()
        if results and 'hotels_results' in results:
            most_expensive_hotel = max(results['hotels_results'], key=lambda x: x['price'])
            hotels[destination] = most_expensive_hotel
    return hotels


def main():
    budget = 2000
    trip_type = 'solo adventure'
    start_date = datetime.datetime.strptime('2024-06-01', '%Y-%m-%d')
    end_date = datetime.datetime.strptime('2024-06-15', '%Y-%m-%d')

    # Get destinations
    destinations = get_travel_destinations(start_date, end_date, budget, trip_type)

    # Search for flights from Tel Aviv to each destination
    flights = search_flights(destinations, start_date, end_date)

    # Find hotels in each destination within budget
    hotels = find_hotels(destinations, budget, start_date, end_date)

    # Combine results and display to user
    trip_options = []
    for destination in destinations:
        trip_options.append({
            'destination': destination,
            'flight': flights[destination],
            'hotel': hotels[destination]
        })

    # Example of output, replace with actual display logic
    for option in trip_options:
        print(f"Destination: {option['destination']}")
        print(f"Flight: {option['flight']}")
        print(f"Hotel: {option['hotel']}")

if __name__ == "__main__":
    main()