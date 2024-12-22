# AI-Trip-planner

## Description

🎥 [Watch Demo Video](https://drive.google.com/file/d/1HV1djoTyw0QUROHCWKh4SAteCUxw2wyW/view?usp=sharing)

AI-Trip-planner is an AI-powered trip planning application that helps users plan their vacations by suggesting destinations, finding flights and hotels, and creating detailed daily itineraries. This project was developed as part of an assignment to create an AI-driven trip planner using various technologies and APIs.

Users input their trip details, including:
- Start date
- End date
- Total budget (for hotel and flights)
- Type of trip (ski, beach, or city)

Based on this input, the application provides:
1. Four destination options, each including:
   - Flight details and prices
   - Hotel recommendations within the budget
   - Total cost breakdown
2. For the selected destination:
   - A detailed daily planner for the entire trip duration
   - Four AI-generated images that visually represent the trip, created using DALL-E

The application leverages AI to create personalized trip suggestions and itineraries, making the planning process both efficient and inspiring for users.

## Installation

To run this project, you'll need to install the following:

1. Next.js and npm (for the frontend)
2. Python 3.7+ (for the backend)

### Frontend Setup
1. Clone the repository:
   ```
   git clone https://github.com/DaphneMessing/Trip_planner.git
   cd Trip_planner
   ```

2. Navigate to the frontend directory:
   ```
   cd frontend
   ```

3. Install the required Node.js packages:
   ```
   npm install
   ```

   Note: This will create the `node_modules` folder which is necessary for the project to run but is not included in the GitHub repository.

### Backend Setup
1. From the root directory of the project, install the required Python packages:
   ```
   pip install fastapi uvicorn pydantic requests serpapi openai
   ```
2. Update the `trip_planner.py` file in the root directory with your OpenAI and SerpAPI keys:
     ```bash
     openai.api_key = "your_openai_api_key_here"
     serpapi_key =  "your_serpapi_key_here"
     ```
     
## How It Works

1. The user enters their trip details (start date, end date, budget, and trip type) on the frontend.
2. The frontend sends this information to the backend.
3. The backend uses OpenAI's GPT model to generate destination suggestions based on the trip type and month.
4. For each suggested destination, the backend uses SerpAPI to fetch flight prices and hotel options within the user's budget.
5. The frontend displays the destination options to the user.
6. When the user selects a destination, the backend generates a daily itinerary using OpenAI's GPT model.
7. The backend also generates trip images using OpenAI's DALL-E model based on the trip summary.
8. The frontend displays the detailed itinerary and generated images to the user.

## Running the Project

1. Start the backend server from the root directory:
   ```
   uvicorn trip_planner:app --reload
   ```

2. In a new terminal, start the frontend development server:
   ```
   cd frontend
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:3000` to use the application.

## Technologies Used

- Frontend:
  - Next.js
  - React
  - CSS Modules

- Backend:
  - FastAPI (Python)
  - OpenAI API (for text generation and image creation)
  - SerpAPI (for flight and hotel data)

- APIs:
  - OpenAI GPT-3.5 Turbo
  - OpenAI DALL-E
  - Google Flights (via SerpAPI)
  - Google Hotels (via SerpAPI)

Note: Make sure you have valid API keys for OpenAI and SerpAPI, and that you've added them to the appropriate files as mentioned in the installation instructions.
