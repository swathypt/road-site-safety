import React, { useState, useEffect } from "react";
import axios from "axios";
import { Container, Table, Nav, Spinner, Alert, Card } from "react-bootstrap";
import "./App.css"; // Ensure CSS is applied

function App() {
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("dataTable"); // Manage active tab

  useEffect(() => {
    axios.get("http://127.0.0.1:5000/violations")
      .then(response => {
        setViolations(response.data);
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching data:", error);
        setError("Failed to fetch data from server.");
        setLoading(false);
      });
  }, []);

  return (
    <Container className="mt-4">
      {/* Header */}
      <h1 className="dashboard-title">
        <span role="img" aria-label="helmet">🚧</span> PPE Compliance Dashboard
      </h1>


      {/* Styled Nav for Tabs (Side by Side) */}
      <Nav variant="pills" className="nav-container">
        <Nav.Item>
          <Nav.Link 
            eventKey="dataTable" 
            active={activeTab === "dataTable"}
            onClick={() => setActiveTab("dataTable")}
          >
            <span role="img" aria-label="table">📊</span> Data Table
          </Nav.Link>
        </Nav.Item>
        <Nav.Item>
          <Nav.Link 
            eventKey="summary" 
            active={activeTab === "summary"}
            onClick={() => setActiveTab("summary")}
          >
            <span role="img" aria-label="chart">📈</span> Summary
          </Nav.Link>
        </Nav.Item>
      </Nav>

      {/* Data Table Section */}
      {activeTab === "dataTable" && (
        <Card className="shadow p-4 mt-3">
          {loading && <Spinner animation="border" className="d-block mx-auto" />}
          {error && <Alert variant="danger">{error}</Alert>}
          
          <Table striped bordered hover responsive className="mt-3">
            <thead className="table-dark">
              <tr>
                <th>ID</th>
                <th>Timestamp</th>
                <th>Location</th>
                <th>Violation Type</th>
                <th>Risk Level</th>
                <th>Image Reference</th>
              </tr>
            </thead>
            <tbody>
              {violations.map((item, index) => (
                <tr key={index}>
                  <td>{item.id}</td>
                  <td>{item.Timestamp}</td>
                  <td>{item.Location_ID}</td>
                  <td>{item.Violation_Type}</td>
                  <td className={`risk-level ${item.Risk_Level.toLowerCase()}`}>
                    {item.Risk_Level}
                  </td>
                  <td>{item.Image_Reference}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      {/* Summary Section */}
      {activeTab === "summary" && (
        <Card className="shadow p-4 mt-3 text-center summary-section">
          <h3 className="mb-3">
            <span role="img" aria-label="chart">📈</span> <strong>Summary of Violations</strong>
          </h3>
          <p>
            <span role="img" aria-label="rocket">🚀</span> This section will show <strong>charts and insights</strong> in the next step.
          </p>
        </Card>
      )}
    </Container>
  );
}

export default App;
