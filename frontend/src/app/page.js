'use client';

import { useState } from 'react';

export default function Home() {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [budget, setBudget] = useState('');
    const [tripType, setTripType] = useState('');
    const [results, setResults] = useState(null);
    const [dailyPlan, setDailyPlan] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await fetch('http://127.0.0.1:8000/plan_trip/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_date: startDate,
                    end_date: endDate,
                    budget: parseInt(budget, 10),
                    trip_type: tripType,
                }),
            });

            const data = await response.json();
            setResults(data.destinations);
            setDailyPlan(null); // Clear any previous daily plan
        } catch (error) {
            console.error('Error:', error);
        }
    };

    const handleGeneratePlan = async (city, country) => {
        try {
            const response = await fetch('http://127.0.0.1:8000/generate_plan/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    city,
                    country,
                    start_date: startDate,
                    end_date: endDate,
                }),
            });

            const data = await response.json();
            setDailyPlan(data);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    return (
        <div>
            <h1>Trip Planner</h1>
            <form onSubmit={handleSubmit}>
                <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    required
                />
                <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    required
                />
                <input
                    type="number"
                    placeholder="Budget"
                    value={budget}
                    onChange={(e) => setBudget(e.target.value)}
                    required
                />
                <select
                    value={tripType}
                    onChange={(e) => setTripType(e.target.value)}
                    required
                >
                    <option value="">Select Trip Type</option>
                    <option value="ski">Ski</option>
                    <option value="beach">Beach</option>
                    <option value="city">City</option>
                </select>
                <button type="submit">Plan My Trip</button>
            </form>

            {results && (
                <div>
                    <h2>Results</h2>
                    <ul>
                        {results.map((destination, index) => (
                            <li key={index}>
                                <h3>{destination.city}, {destination.country}</h3>
                                <p>
                                    <strong>Flight Price:</strong> ${destination.flight_price} <br />
                                    <strong>Hotel:</strong> {destination.hotel.name} <br />
                                    <strong>Hotel Price:</strong> ${destination.hotel.total_rate}
                                </p>
                                <button
                                    onClick={() => handleGeneratePlan(destination.city, destination.country)}
                                >
                                    Select This Trip
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {dailyPlan && (
                <div>
                    <h2>Daily Plan</h2>
                    <p>{dailyPlan.daily_plan}</p>
                    <h3>Visual Summaries:</h3>
                    <ul>
                        {dailyPlan.image_descriptions.map((desc, index) => (
                            <li key={index}>{desc}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}