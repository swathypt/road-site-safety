import React, { useState, useEffect } from "react";
import axios from "axios";
import { Container, Card, Form } from "react-bootstrap";
import Select from "react-select";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import "./App.css";

function App() {
  const [violations, setViolations] = useState([]);
  const [filteredViolations, setFilteredViolations] = useState([]);
  const [fromDate, setFromDate] = useState(null);
  const [toDate, setToDate] = useState(null);
  const [selectedLocations, setSelectedLocations] = useState([]);
  const [selectedRiskLevel, setSelectedRiskLevel] = useState("");

  // Fetch Data on Load
  useEffect(() => {
    axios.get("http://127.0.0.1:5000/violations")
      .then(response => {
        setViolations(response.data);
        setFilteredViolations(response.data); // Initially set filtered data to all
      })
      .catch(error => console.error("Error fetching data:", error));
  }, []);

  // Extract Unique Locations and Risk Levels
  const uniqueLocations = [...new Set(violations.map(v => v.Location_ID))].filter(Boolean);
  const uniqueRiskLevels = [...new Set(violations.map(v => v.Risk_Level))].filter(Boolean);

  const locationOptions = uniqueLocations.map(loc => ({ value: loc, label: loc }));

  // Filtering Logic
  useEffect(() => {
    let filteredData = violations;

    // Filter by Time Period
    if (fromDate || toDate) {
      filteredData = filteredData.filter(v => {
        const violationDate = new Date(v.Timestamp);
        return (
          (!fromDate || violationDate >= fromDate) &&
          (!toDate || violationDate <= toDate)
        );
      });
    }

    // Filter by Location
    if (selectedLocations.length > 0) {
      const selectedValues = selectedLocations.map(loc => loc.value);
      filteredData = filteredData.filter(v => selectedValues.includes(v.Location_ID));
    }

    // Filter by Risk Level
    if (selectedRiskLevel) {
      filteredData = filteredData.filter(v => v.Risk_Level === selectedRiskLevel);
    }

    setFilteredViolations(filteredData);
  }, [fromDate, toDate, selectedLocations, selectedRiskLevel, violations]);

  return (
    <Container fluid className="dashboard-container">
      <h1 className="dashboard-title">🚧 PPE Compliance Dashboard</h1>
      <div className="dashboard-layout">
        {/* Grid 1: Filters Section */}
        <div className="grid1">
          <Card className="shadow p-4">
            <h2 className="filter-title">Filters</h2>

            <Form.Group>
              <Form.Label className="filter-label">Time Period:</Form.Label>
              <div className="date-range">
                <DatePicker selected={fromDate} onChange={setFromDate} placeholderText="From" className="form-control filter-input" />
                <DatePicker selected={toDate} onChange={setToDate} placeholderText="To" className="form-control filter-input" />
              </div>
            </Form.Group>

            <Form.Group>
              <Form.Label className="filter-label">Site Location:</Form.Label>
              <Select options={locationOptions} isMulti value={selectedLocations} onChange={setSelectedLocations} placeholder="Select Locations" className="filter-input" />
            </Form.Group>

            <Form.Group>
              <Form.Label className="filter-label">Risk Level:</Form.Label>
              <Form.Control as="select" value={selectedRiskLevel} onChange={e => setSelectedRiskLevel(e.target.value)} className="filter-input">
                <option value="">All</option>
                {uniqueRiskLevels.map(level => <option key={level} value={level}>{level}</option>)}
              </Form.Control>
            </Form.Group>
          </Card>
        </div>

        {/* Grid 2: Dashboard Section */}
        <div className="grid2">
          <div className="grid-container">
            <div className="grid-box">
              <Card className="shadow p-3">
                <h4>📊 Grid 3</h4>
                <p>Content coming soon...</p>
              </Card>
            </div>
            <div className="grid-box">
              <Card className="shadow p-3">
                <h4>📊 Grid 4</h4>
                <p>Content coming soon...</p>
              </Card>
            </div>
            <div className="grid-box">
              <Card className="shadow p-3">
                <h4>📊 Grid 5</h4>
                <p>Content coming soon...</p>
              </Card>
            </div>
            <div className="grid-box">
              <Card className="shadow p-3">
                <h4>📊 Grid 6</h4>
                <p>Content coming soon...</p>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </Container>
  );
}

export default App;
