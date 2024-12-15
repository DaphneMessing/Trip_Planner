import openai
from serpapi.google_search import GoogleSearch
import datetime
import re

      
openai_api_key = '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'
serpapi_key = 'bac33b4ea8bb20045ef2bf2de0b101b0cae36c44ae6e7e9a25425b4830748462'

def get_travel_destinations(start_date, end_date, budget, trip_type):
    openai.api_key = openai_api_key
    month = start_date.strftime("%B")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                    {"role": "system", "content": "You are a travel planner."},
                    {"role": "user", "content": f"Given a budget of ${budget} for a {trip_type} trip in the month of {month}, suggest 2 destinations worldwide. provide the response in the following format:\n1. Destination, Country (Airport Code) - Description\n2. Destination, Country (Airport Code) - Description\n"}
                ]
        )#suggest 5 destinations worldwide. provide the response in the following format:\n1. Destination, Country (Airport Code) - Description\n2. Destination, Country (Airport Code) - Description\n3. Destination, Country (Airport Code) - Description\n4. Destination, Country (Airport Code) - Description\n5. Destination, Country (Airport Code) - Description"}
        # Parse the destinations
        lines = response['choices'][0]['message']['content'].split('\n')
        destinations = [parse_destination(line.split(' - ')[0].strip()) for line in lines if line.strip()]
        return destinations
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return [], "No suggestions due to API failure."
    
def parse_destination(destination):
    # Regular expression to match the pattern "City, Country (Code)"
    match = re.match(r"^\d+\.\s*(.+?), (.+?) \((.+?)\)$", destination)
    if match:
        city, country, airport_code = match.groups()
        first_airport_code = airport_code.split('/')[0].strip()  # Take only the first code
        parsed_data = {
            "city": city,
            "country": country,
            "airport_code": first_airport_code
        }
        # print(f"Parsed Data: City - {city}, Country - {country}, Airport Code - {airport_code}")  # Debug: print parsed data
        return parsed_data
    else:
        print("Failed to parse destination:", destination)  # Debug: indicate a failure in parsing
        return None

   
        

def search_flights(destinations, start_date, end_date):
    flights = {}
    # print("Starting flight search for destinations:", destinations) #Debug
    for destination in destinations:
        code = destination['airport_code']
        #print(f"Searching flights for {destination['city']}, {destination['country']} ({code})")
        params = {
                "engine": "google_flights",
                "departure_id": "TLV",
                "arrival_id": code,
                "outbound_date": start_date.strftime("%Y-%m-%d"),
                "return_date": end_date.strftime("%Y-%m-%d"),
                "currency": "USD",
                "api_key": serpapi_key
            }
        search = GoogleSearch(params)

        try:
            results = search.get_json()
            if results and 'best_flights' in results:
                flights_data = results['best_flights']
                # Assuming the price is accessible directly under the flight details
                cheapest_flight = min(flights_data, key=lambda x: x['price'])
                flights[destination['city']] = {
                    "city": destination['city'],
                    "country": destination['country'],
                    "price": cheapest_flight['price'],
                    "details": cheapest_flight
                }
                # print(f"Cheapest flight for {destination['city']}: {cheapest_flight['price']}")
            else:
                print(f"No flight results found for {destination['city']}.")
                flights[destination['city']] = {
                    "city": destination['city'],
                    "country": destination['country'],
                    "price": None,
                    "details": "No flights available"
                }
        except Exception as e:
            print(f"An error occurred while searching for flights for {destination['city']}: {str(e)}")
            flights[destination['city']] = {
                "city": destination['city'],
                "country": destination['country'],
                "price": None,
                "details": "Error retrieving flights"
            }

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
            # print(f"Searching for hotels in {city}, {country} with remaining budget: ${remaining_budget}")  # Debug
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

                    # # Print all hotel prices to debug
                    # print(f"Hotel search results for {city}:")
                    # for hotel in results['properties']:
                    #     print(f"{hotel['name']}: ${hotel['total_rate']['extracted_lowest']}")

                    # print(f"Hotel search results for {city}: {results['properties']}")  # Debug: print all hotel results
                    most_expensive_hotel = max(results['properties'], key=lambda x: x['total_rate']['extracted_lowest'])
                    hotels[city] = {
                        "name": most_expensive_hotel['name'],
                        "total_rate": most_expensive_hotel['total_rate']['extracted_lowest']
                    }
                    # print(f"Most expensive hotel found in {city}: {hotels[city]['name']} at ${hotels[city]['total_rate']}")  # Debug
                else:
                    # print(f"No hotel results found for {city} within the budget.")  # Debug
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
    days = (end_date - start_date).days + 1
    prompt = f"Create a detailed daily plan for a trip to {city}, {country} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}. Include activities, meal suggestions, and local travel tips for each day of the {days}-day trip. At the end provide exactly 2 descriptions that could visually summarize the entire trip. make the description clear and detailed. please use this format for the  visually summariz:  visually summarize:\n1. A picture of the Eiffel Tower at sunset, symbolizing the iconic landmark of Paris.\n2. A snapshot of colorful flowers in full bloom at the gardens of Versailles, representing the beauty of French landscapes.\n3. An image of the Seine River with historic bridges in the background, showcasing the romantic charm of Paris.\n4. A shot of street artists painting in Montmartre, capturing the artistic spirit and bohemian vibe of the neighborhood."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sophisticated travel planner assistant and a creative advisor for visual content."},
                {"role": "user", "content": prompt}
            ]
        )
        full_response = response['choices'][0]['message']['content'] if response['choices'][0]['message']['content'] else "No plan could be generated."

        # Splitting the daily plan from the image descriptions using a case-insensitive regex
        parts = re.split(r'(?i)visually summarize:', full_response, 1)
        plan_content = parts[0].strip() if len(parts) > 1 else full_response
        image_descriptions_content = parts[1].strip() if len(parts) > 1 else ""

        # Extracting image descriptions using the provided method
        image_descriptions = extract_image_descriptions(image_descriptions_content)

        # Printing the extracted image descriptions for debugging
        print("Extracted Image Descriptions:")
        for desc in image_descriptions:
            print(desc)

        return plan_content, image_descriptions
    except Exception as e:
        print(f"An error occurred while generating the daily plan: {str(e)}")
        return "Failed to generate a daily plan. Please try again.", []


def extract_image_descriptions(image_descriptions_content):
    descriptions = []
    lines = image_descriptions_content.split('\n')
    for line in lines:
        # Check if the line starts with a number followed by a period, denoting the start of a description
        if line.strip().startswith(("1.", "2.", "3.", "4.")):
            description = line.split(". ", 1)[1] if ". " in line else line
            descriptions.append(description)

            print(f"Extracted description: {description}")  # Debug print of each description
    return descriptions



def generate_activity_images(descriptions):
    openai.api_key = openai_api_key
    images = []

    for description in descriptions:
        try:
            # Generate the image using OpenAI's DALL-E
            response = openai.Image.create(
                #model="dalle-2",  # or "dalle-mini" depending on availability
                prompt=description,
                n=1,  # Number of images to generate
                size="1024x1024"  # Choose the size of the generated images
            )
            # Extracting the URL from the response
            if 'data' in response and len(response['data']) > 0:
                image_url = response['data'][0]['url']
                images.append(image_url)
                print(f"Generated image for: {description} - URL: {image_url}")
            else:
                error_message = "No image generated"
                images.append(error_message)
                print(f"{error_message} for description: {description}")
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            images.append(error_message)
            print(f"{error_message} for description: {description}")
    
    return images

def display_images(image_urls):
    print("\nGenerated Images:")
    for index, url in enumerate(image_urls, start=1):
        if url.startswith("http"):
            print(f"{index}. {url}")
        else:
            print(f"{index}. Error: {url}")


def validate_date_input(prompt):
    while True:
        date_str = input(prompt)
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            if date < datetime.datetime.now():
                print("Please enter a future date.")
            else:
                return date
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD format.")


def validate_budget_input(prompt, min_budget=0):  # You can adjust the minimum budget as needed
    while True:
        try:
            budget = int(input(prompt))
            if budget > min_budget:
                return budget
            else:
                print("Please enter a positive number for the budget.")
        except ValueError:
            print("Invalid input. Please enter a numeric value for the budget.")



def validate_trip_type(prompt):
    valid_trip_types = ["ski", "beach", "city"]
    while True:
        trip_type = input(prompt).lower()  # Convert to lower case to ensure case insensitivity
        if trip_type in valid_trip_types:
            return trip_type
        else:
            print(f"Invalid trip type. Please choose one of the following: {', '.join(valid_trip_types)}.")            



20

def main():
    # User inputs for trip details
    print("Welcome to the Trip Planner!")
    # Validate dates input
    start_date = validate_date_input("Enter the start date of your trip (YYYY-MM-DD): ")
    end_date = validate_date_input("Enter the end date of your trip (YYYY-MM-DD): ")

    while end_date <= start_date:
            print("End date must be after start date. Please enter the dates again.")
            start_date = validate_date_input("Enter the start date of your trip (YYYY-MM-DD): ")
            end_date = validate_date_input("Enter the end date of your trip (YYYY-MM-DD): ")

    
    # Validate budget input
    budget = validate_budget_input("Enter your total budget for the trip in USD: ")

     # Validate trip type input
    trip_type = validate_trip_type("Enter the type of your trip (ski, beach, city): ")


    while True:
        destinations = get_travel_destinations(start_date, end_date, budget, trip_type)
        if not destinations:
            print("No destinations could be suggested within your budget. Please consider increasing your budget.")
            budget = validate_budget_input("Please enter a larger budget for the trip in USD: ")
            continue
        
        flights = search_flights(destinations, start_date, end_date)
        if not any(flight.get('price') for flight in flights.values()):
            print("No flights available within your budget. Please increase your budget or adjust your travel dates.")
            budget = validate_budget_input("Please enter a larger budget for the trip in USD: ")
            continue

        hotels = find_hotels(destinations, flights, budget, start_date, end_date)
        if not any(hotel.get('total_rate') > 0 for hotel in hotels.values()):
            print("No hotels available within your budget. Please increase your budget.")
            budget = validate_budget_input("Please enter a larger budget for the trip in USD: ")
            continue

        break  # Exit the loop if all conditions are met


    # Combine results and display to user
    trips = []
    for destination in destinations:
        city = destination['city']
        country = destination['country']
        flight_info = flights.get(city, {})
        hotel_info = hotels.get(city, {"name": "No hotels available", "total_rate": 0})

        trip_details = {
            "city": city,
            "country": country,
            "flight_price": flight_info.get('price', 'No valid flight found'),
            "hotel_name": hotel_info.get('name'),
            "hotel_price": hotel_info.get('total_rate'),
            "total_cost": flight_info.get('price', 0) + hotel_info.get('total_rate', 0) if flight_info.get('price') is not None else 'Pricing incomplete'
        }
        trips.append(trip_details)

    # Display the trip details
    print("\nTrip Details:")
    for index, trip in enumerate(trips, start=1):
        print(f"\n{index}. Destination: {trip['city']}, {trip['country']}")
        print(f"   Flight: {trip['flight_price']} USD")
        print(f"   Hotel: {trip['hotel_name']} at {trip['hotel_price']} USD")
        if isinstance(trip['total_cost'], int):
            print(f"   Total price for the trip: {trip['total_cost']} USD")
        else:
            print("   Total price for the trip: Pricing incomplete")

    # Let the user select a trip
    while True:
        try:
            trip_choice = int(input("\nEnter the number of the trip you would like to select: "))
            if 1 <= trip_choice <= len(trips):
                selected_trip = trips[trip_choice - 1]  # Adjust index for zero-based list
                print(f"\nYou have selected the trip to {selected_trip['city']}, {selected_trip['country']}.")
                # Generate daily plan
                print("\nGenerating daily plan for your trip...")
                daily_plan, image_descriptions = generate_daily_plan(selected_trip['city'], selected_trip['country'], start_date, end_date)
                print("\nDaily Plan:")
                print(daily_plan)
                generated_images = generate_activity_images(image_descriptions)
                display_images(generated_images)  # Display image URLs
                for image in generated_images:
                    if image:
                        print(image)
                    else:
                        print("No image generated for this prompt.")
     
                break
            else:
                print("Invalid selection. Please enter a number corresponding to the trip.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

if __name__ == "__main__":
    main()