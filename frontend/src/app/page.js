'use client';

import { useState } from 'react';
import styles from './TripPlanner.module.css';

export default function Home() {
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [budget, setBudget] = useState('');
    const [tripType, setTripType] = useState('');
    const [results, setResults] = useState(null);
    const [selectedResult, setSelectedResult] = useState(null);

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
            console.log('API Response:', data);
            setResults(data.destinations);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    const handleSelectResult = (result) => {
        setSelectedResult(result);
    };

    return (
        <div className={styles.container}>
            {/* Header */}
            <header className={styles.header}>
                <h1 className={styles.title}>Trip Planner</h1>
            </header>

            {/* Form Section */}
            {!results && !selectedResult && (
                <main className={styles.main}>
                    <section className={styles.searchSection}>
                        <form onSubmit={handleSubmit} className={styles.searchForm}>
                            {/* Start Date */}
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Start Date:</label>
                                <input
                                    type="date"
                                    value={startDate}
                                    onChange={(e) => setStartDate(e.target.value)}
                                    className={styles.datePicker}
                                    required
                                />
                            </div>

                            {/* End Date */}
                            <div className={styles.formGroup}>
                                <label className={styles.label}>End Date:</label>
                                <input
                                    type="date"
                                    value={endDate}
                                    onChange={(e) => setEndDate(e.target.value)}
                                    className={styles.datePicker}
                                    required
                                />
                            </div>

                            {/* Budget */}
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Budget:</label>
                                <input
                                    type="number"
                                    placeholder="Enter your budget"
                                    value={budget}
                                    onChange={(e) => setBudget(e.target.value)}
                                    className={styles.input}
                                    required
                                />
                            </div>

                            {/* Trip Type */}
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Trip Type:</label>
                                <select
                                    value={tripType}
                                    onChange={(e) => setTripType(e.target.value)}
                                    className={styles.select}
                                    required
                                >
                                    <option value="">Select trip type</option>
                                    <option value="ski">Ski</option>
                                    <option value="beach">Beach</option>
                                    <option value="city">City</option>
                                </select>
                            </div>
                        </form>

                        {/* Submit Button Centered Below */}
                        <div className={styles.searchButtonContainer}>
                            <button type="submit" className={styles.searchButton} onClick={handleSubmit}>
                                Get Suggestions
                            </button>
                        </div>
                    </section>
                </main>
            )}

            {/* Results Section */}
            {results && !selectedResult && (
                <main className={styles.resultsSection}>
                    <h2 className={styles.resultsTitle}>Your Trip Suggestions</h2>
                    <div className={styles.resultsGrid}>
                        {results.map((result, index) => (
                            <div
                                key={index}
                                className={styles.resultCard}
                                onClick={() => handleSelectResult(result)}
                            >
                                <h3 className={styles.resultCardTitle}>
                                    {result.city}, {result.country}
                                </h3>
                                <p>
                                    <strong>Flight Price:</strong> ${result.flight_price|| "N/A"}
                                </p>
                                <p>
                                    <strong>Hotel Name:</strong> {result.hotel_name || "No hotel available"}
                                </p>
                                <p>
                                    <strong>Hotel Price:</strong> ${result.hotel_price|| "N/A"}
                                </p>
                                <button className={styles.selectButton}>Select</button>
                            </div>
                        ))}
                    </div>
                </main>
            )}

            {/* Selected Result Section */}
            {selectedResult && (
                <main className={styles.selectedSection}>
                    <h2 className={styles.selectedTitle}>Your Selected Trip</h2>
                    <div className={styles.selectedCard}>
                        <h3 className={styles.resultCardTitle}>
                            {selectedResult.city}, {selectedResult.country}
                        </h3>
                        <p>
                            <strong>Flight Price:</strong> ${selectedResult.flight_price}
                        </p>
                        <p>
                            <strong>Hotel Name:</strong> {selectedResult.hotel_name}
                        </p>
                        <p>
                            <strong>Hotel Price:</strong> ${selectedResult.hotel_price}
                        </p>
                    </div>
                </main>
            )}

            {/* Footer */}
            <footer className={styles.footer}>
                <p className={styles.footerText}>© 2024 Trip Planner</p>
            </footer>
        </div>
    );
}
