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
openai_api_key =  "" # Add your OpenAI API key here
serpapi_key =  "" # Add your SerpAPI API key here

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
                    "content": f"Given a budget of ${budget} for a {trip_type} trip in the month of {month}, suggest 5 destinations worldwide. Provide the response in this format:\n1. Destination, Country (Airport Code) - Description\n2. Destination, Country (Airport Code) - Description\n",
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
    for destination in destinations:
        city = destination["city"]
        country = destination["country"]
        flight_info = flights.get(city)

        if flight_info and flight_info["price"]:
            remaining_budget = budget - flight_info["price"]
            params = {
                "engine": "google_hotels",
                "q": f"hotels in {city}, {country}",
                "check_in_date": start_date.strftime("%Y-%m-%d"),
                "check_out_date": end_date.strftime("%Y-%m-%d"),
                "adults": "1",
                "currency": "USD",
                "sort_by": "3",  # Sort by lowest price
                "max_price": remaining_budget,
                "api_key": serpapi_key,
            }
            search = GoogleSearch(params)
            try:
                results = search.get_json()
                if results and "properties" in results:
                    most_expensive_hotel = max(
                        results["properties"],
                        key=lambda x: x["total_rate"]["extracted_lowest"],
                    )
                    hotels[city] = {
                        "name": most_expensive_hotel["name"],
                        "price": most_expensive_hotel["total_rate"]["extracted_lowest"],
                    }
                else:
                    hotels[city] = {"name": "No hotels available", "price": 0}
            except Exception as e:
                print(f"Error fetching hotels for {city}: {e}")
                hotels[city] = {"name": "Error retrieving hotel data", "price": 0}
        else:
            hotels[city] = {"name": "No valid flight data", "price": 0}

    return hotels


def generate_daily_plan(city, country, start_date, end_date):
    openai.api_key = openai_api_key
    prompt = f"Create a daily plan for a trip to {city}, {country} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}. Format your response as follows:\n\nDaily Plan:\n[Detailed daily plan - start each day with his number below each activity in different line. use this format: Day 1\n -Morning: relaxation at the beach or spa\n -Afternoon:  Explore the ancient Mayan ruins and learn about the history\n -Evning: Farewell drinks and evening entertainment at the resort]\n\nSummary: [provide exactly 4 descriptions that could visually summarize the entire trip. make the description clear and detailed. please use this format for the  visually summariz:  visually summarize:\n1. A picture of the Eiffel Tower at sunset, symbolizing the iconic landmark of Paris.\n2. A snapshot of colorful flowers in full bloom at the gardens of Versailles, representing the beauty of French landscapes.\n3. An image of the Seine River with historic bridges in the background, showcasing the romantic charm of Paris.\n4. A shot of street artists painting in Montmartre, capturing the artistic spirit and bohemian vibe of the neighborhood]"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sophisticated travel planner assistant and a creative advisor for visual content."},
                {"role": "user", "content": prompt}
            ]
        )
       
        content = response.choices[0].message.content.strip()
        print (content)
        
        if "Daily Plan:" in content and "Summary:" in content:
            daily_plan, summary = content.split("Summary:")
            daily_plan = daily_plan.replace("Daily Plan:", "").strip()
            summary = summary.strip()
            print(summary)

        # Extracting image descriptions using the provided method
        image_descriptions = extract_image_descriptions(summary)

        return daily_plan, image_descriptions
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

@app.post("/generate_plan/")
def generate_plan(request: dict):
    try:
        city = request.get("city")
        country = request.get("country")
        start_date = datetime.datetime.strptime(request["start_date"], "%Y-%m-%d")
        end_date = datetime.datetime.strptime(request["end_date"], "%Y-%m-%d")

        if not city or not country:
            raise HTTPException(status_code=400, detail="City and country are required.")

        # Generate the daily plan and image descriptions
        daily_plan, image_descriptions = generate_daily_plan(city, country, start_date, end_date)

        # Generate images based on descriptions
        generated_images = generate_activity_images(image_descriptions)

        return {
            "daily_plan": daily_plan,
            "image_descriptions": image_descriptions,
            "images": generated_images,  # Include generated image URLs
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            flight_info = flights.get(city, {"price": "No flights available"})
            hotel_info = hotels.get(city, {"name": "No hotels available", "price": "N/A"})

            results.append({
                "city": city,
                "country": country,
                "flight_price": flight_info["price"],
                "hotel_name": hotel_info["name"],
                "hotel_price": hotel_info["price"],
            })

        return {"destinations": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
