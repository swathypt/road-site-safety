// importing required modules
import React, { useState, useEffect } from "react";
import axios from "axios";
import { Card, Form } from "react-bootstrap";
import Select from "react-select";
import DatePicker from "react-datepicker";
import { Tab, Tabs, TabList, TabPanel } from "react-tabs";
import "react-tabs/style/react-tabs.css";
import { useTable, useSortBy, useFilters, useGlobalFilter } from "react-table";
import "react-datepicker/dist/react-datepicker.css";
import "./App.css";
import "chart.js/auto";
import { Chart as ChartJS, ArcElement, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale } from "chart.js";
import { Pie } from "react-chartjs-2";
import { Bar } from "react-chartjs-2";
import { Line } from "react-chartjs-2";
import { format } from "date-fns";


// Register required Chart.js elements
ChartJS.register(ArcElement, Tooltip, Legend, LineElement, PointElement, CategoryScale, LinearScale);

const ViolationBarChart = ({ violations }) => {
  const [violationCounts, setViolationCounts] = useState({
    compliant: 0,
    medium: 0,
    high: 0,
  });

  // Process data and count violations by risk level
  useEffect(() => {
    const counts = { compliant: 0, medium: 0, high: 0 };
    violations.forEach(v => {
      counts[v.Risk_Level] = (counts[v.Risk_Level] || 0) + 1;
    });
    setViolationCounts(counts);
  }, [violations]);

  const data = {
    labels: ["Compliant", "Medium Risk", "High Risk"],
    datasets: [
      {
        label: "Number of Violations",
        data: [violationCounts.compliant, violationCounts.medium, violationCounts.high],
        backgroundColor: ["#2ECC71", "#F1C40F", "#E74C3C"],
        borderWidth: 1,
      }
    ]
  };

  return (
    <div className="grid-box">
      <Card className="shadow p-3">
        <h4>📊 Real-Time Violation Counts by Category</h4>
        <Bar data={data} />
      </Card>
    </div>
  );
};

const SiteComplianceChart = ({ violations }) => {
  const [complianceScores, setComplianceScores] = useState([]);

  useEffect(() => {
    if (!violations || violations.length === 0) {
      setComplianceScores([]);
      return;
    }

    // Define weights for compliance scoring
    const WEIGHTS = { compliant: 3, medium: 2, high: 1 };
    const MAX_WEIGHT = WEIGHTS.compliant; // Normalization factor

    // Compute compliance scores for each site
    const siteData = {};
    violations.forEach((v) => {
      const siteName = v.Site_Name;
      const riskLevel = v.Risk_Level.toLowerCase();

      if (!siteData[siteName]) {
        siteData[siteName] = { high: 0, medium: 0, compliant: 0 };
      }

      if (WEIGHTS[riskLevel] !== undefined) {
        siteData[siteName][riskLevel] += 1;
      }
    });

    // Convert data into an array of { site, score }
    const calculatedScores = Object.keys(siteData).map((site) => {
      const counts = siteData[site];
      const totalInstances = counts.high + counts.medium + counts.compliant;

      if (totalInstances === 0) return { site, score: 0 };

      const weightedSum =
        counts.compliant * WEIGHTS.compliant +
        counts.medium * WEIGHTS.medium +
        counts.high * WEIGHTS.high;

      const complianceScore = (weightedSum / (totalInstances * MAX_WEIGHT)) * 100;
      return { site, score: parseFloat(complianceScore.toFixed(2)) };
    });

    setComplianceScores(calculatedScores);
  }, [violations]);

  return (
    <div className="grid-box">
      <Card className="shadow p-3">
        <h4>📊 Site Compliance Scores</h4>
        {complianceScores.length > 0 ? (
          <table className="styled-table">
            <thead>
              <tr>
                <th>Site Name</th>
                <th>Compliance Score (%)</th>
              </tr>
            </thead>
            <tbody>
              {complianceScores.map((entry, index) => (
                <tr key={index}>
                  <td>{entry.site}</td>
                  <td>{entry.score}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No data available</p>
        )}
      </Card>
    </div>
  );
};

const RiskDistributionPieChart = ({ violations }) => {
  // State to hold counts for each risk level
  const [riskCounts, setRiskCounts] = useState({
    compliant: 0,
    medium: 0,
    high: 0
  });

  // Whenever violations update, recalculate the risk counts
  useEffect(() => {
    const counts = { compliant: 0, medium: 0, high: 0 };
    violations.forEach(v => {
      // Make sure we map to the correct riskLevel key here
      // (If your backend uses "High", "Medium", "Compliant", ensure you match them exactly)
      const riskLevel = v.Risk_Level.toLowerCase(); // e.g. "high"
      if (counts[riskLevel] !== undefined) {
        counts[riskLevel] += 1;
      }
    });
    setRiskCounts(counts);
  }, [violations]);

  // Prepare data for the Pie chart
  const chartData = {
    labels: ["Compliant", "Medium Risk", "High Risk"],
    datasets: [
      {
        data: [
          riskCounts.compliant,
          riskCounts.medium,
          riskCounts.high
        ],
        backgroundColor: ["#2ECC71", "#F1C40F", "#E74C3C"]
      }
    ]
  };

  return (
    <div className="grid-box">
      <Card className="shadow p-3">
        <h4>Risk Level Distribution</h4>
        <Pie data={chartData} />
      </Card>
    </div>
  );
};

const HistoricalTrendLineChart = ({ violations }) => {
  const [chartData, setChartData] = useState({ labels: [], datasets: [] });

  useEffect(() => {
    if (!violations || violations.length === 0) {
      setChartData({ labels: [], datasets: [] });
      return;
    }

    // 1. Count violations by date
    const countsByDate = {};
    violations.forEach((v) => {
      const d = new Date(v.Date);

      // Format to 'yyyy-MM-dd' using date-fns
      const dateString = format(d, "yyyy-MM-dd");
      countsByDate[dateString] = (countsByDate[dateString] || 0) + 1;
    });

    // 2. Sort the dates chronologically
    const sortedDates = Object.keys(countsByDate).sort(
      (a, b) => new Date(a) - new Date(b)
    );

    // 3. Build your data arrays
    const violationCounts = sortedDates.map(date => countsByDate[date]);

    // 4. Update chartData
    setChartData({
      labels: sortedDates,
      datasets: [
        {
          label: "Violations Over Time",
          data: violationCounts,
          borderColor: "#3498DB",
          backgroundColor: "rgba(52, 152, 219, 0.2)",
          fill: true,
          tension: 0.1
        }
      ]
    });
  }, [violations]);

  return (
    <div className="grid-box">
      <Card className="shadow p-3">
        <h4>📈 Historical Trend Analysis</h4>
        {chartData.labels.length > 0 ? (
          <Line data={chartData} />
        ) : (
          <p>No data available for the selected filters.</p>
        )}
      </Card>
    </div>
  );
};

function App() {
  const [violations, setViolations] = useState([]);
  const [siteCompliance, setSiteCompliance] = useState([]);
  const [filteredViolations, setFilteredViolations] = useState([]);
  const [fromDate, setFromDate] = useState(null);
  const [toDate, setToDate] = useState(null);
  const [selectedRiskLevel, setSelectedRiskLevel] = useState("");
  const uniqueRiskLevels = [...new Set(violations.map(v => v.Risk_Level))].filter(Boolean);
  const uniqueSiteNames = [...new Set(violations.map(v => v.Site_Name))].filter(Boolean);
  const siteNameOptions = [...new Set(violations.map(v => v.Site_Name))].filter(Boolean).map(name => ({ value: name, label: name }));
  const [selectedSites, setSelectedSites] = useState([]);

  useEffect(() => {
    axios.get("http://127.0.0.1:5000/violations")
      .then(response => {
        console.log("API Data Loaded:", response.data);
        setViolations(response.data);
        setFilteredViolations(response.data);
      })
      .catch(error => console.error("Error fetching data:", error));

  }, []);
 

  
  // Apply Filters
  useEffect(() => {
    let filteredData = violations;

    if (fromDate || toDate) {
      filteredData = filteredData.filter(v => {
        const violationDate = new Date(v.Date);
        return (
          (!fromDate || violationDate >= fromDate) &&
          (!toDate || violationDate <= toDate)
        );
      });
    }

    if (selectedSites.length > 0) {
      const selectedValues = selectedSites.map(s => s.value);
      filteredData = filteredData.filter(v => selectedValues.includes(v.Site_Name));
    }

    if (selectedRiskLevel) {
      filteredData = filteredData.filter(v => v.Risk_Level === selectedRiskLevel);
    }

    setFilteredViolations(filteredData);
  }, [fromDate, toDate,selectedSites , selectedRiskLevel, violations]);


  // React-Table Columns
  const columns = React.useMemo(() => [
    { Header: "Date", accessor: "Date", Filter: DefaultColumnFilter },
    { Header: "Time", accessor: "Time", Filter: DefaultColumnFilter },
    { Header: "Site Name", accessor: "Site_Name", Filter: DefaultColumnFilter },
    { Header: "Violation Type", accessor: "Violation_Type", Filter: DefaultColumnFilter },
    { Header: "Risk Level", accessor: "Risk_Level", Filter: DefaultColumnFilter },
    { Header: "Image", accessor: "Image_Reference", 
      Cell: ({ value }) => (
        <button 
          onClick={() => window.open(`http://127.0.0.1:5000/images/${value}`, '_blank')}
          className="preview-btn">
          Preview
        </button>
      ) 
    }
  ], []);
  
  const defaultColumn = { Filter: DefaultColumnFilter };

  const {
    getTableProps, getTableBodyProps, headerGroups, rows, prepareRow,
    state, setGlobalFilter
  } = useTable(
    {
      columns,
      data: filteredViolations,
      defaultColumn,
    },
    useFilters,
    useGlobalFilter,
    useSortBy
  );

  return (
    <div className="dashboard-container">
      <h1 className="dashboard-title">🚧 PPE Compliance Dashboard</h1>

      <Tabs>
        <TabList>
          <Tab>📊 Dashboard</Tab>
          <Tab>📋 Data Table</Tab>
        </TabList>

        {/* Dashboard Tab */}
        <TabPanel>
          <div className="dashboard-layout">
            <div className="grid1">
              <Card className="shadow p-4">
                <h2 className="filter-title">Filters</h2>
                <Form.Group>
                  <Form.Label className="filter-label">Time Period:</Form.Label>
                  <div className="date-range">
                    <DatePicker selected={fromDate} onChange={setFromDate} placeholderText="From" />
                    <DatePicker selected={toDate} onChange={setToDate} placeholderText="To" />
                  </div>
                </Form.Group>
                <Form.Group>
                  <Form.Label className="filter-label">Site Name:</Form.Label>
                    <Select 
                      options={siteNameOptions} 
                      isMulti 
                      value={selectedSites} 
                      onChange={setSelectedSites} 
                    />
                </Form.Group>
                <Form.Group>
                  <Form.Label className="filter-label">Risk Level:</Form.Label>
                  <Form.Control
                    as="select"
                    value={selectedRiskLevel}
                    onChange={(e) => setSelectedRiskLevel(e.target.value)}
                  >
                    <option value="">All</option>
                    {uniqueRiskLevels.map((level) => (
                      <option key={level} value={level}>
                        {level}
                      </option>
                    ))}
                  </Form.Control>
                </Form.Group>

              </Card>
            </div>

            <div className="grid2">
              <div className="grid-container">
                {/* 🔹 Grid 3, 4, 5, 6: All Contain Pie Charts */}
                <div className="grid-box">
                  <ViolationBarChart violations={filteredViolations} />
                </div>

                <div className="grid-box">
                <SiteComplianceChart violations={filteredViolations} />
                </div>

                <div className="grid-box">
                  <RiskDistributionPieChart violations={filteredViolations} />
                </div>

                <div className="grid-box">
                <HistoricalTrendLineChart violations={filteredViolations} />
                </div>


              </div>
            </div>
          </div>
        </TabPanel>

        {/* Data Table Tab */}
        <TabPanel>
          <div className="data-table-container">
            <input
              className="table-search"
              type="text"
              placeholder="Search all columns..."
              value={state.globalFilter || ""}
              onChange={(e) => setGlobalFilter(e.target.value)}
            />
            <table {...getTableProps()} className="styled-table">
              <thead>
                {headerGroups.map(headerGroup => (
                  <tr {...headerGroup.getHeaderGroupProps()}>
                    {headerGroup.headers.map(column => (
                      <th {...column.getHeaderProps(column.getSortByToggleProps())}>
                        {column.render("Header")}
                        <span>{column.isSorted ? (column.isSortedDesc ? " 🔽" : " 🔼") : ""}</span>
                        <div>{column.canFilter ? column.render("Filter") : null}</div>
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody {...getTableBodyProps()}>
                {rows.map(row => {
                  prepareRow(row);
                  return (
                    <tr {...row.getRowProps()}>
                      {row.cells.map(cell => <td {...cell.getCellProps()}>{cell.render("Cell")}</td>)}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </TabPanel>
      </Tabs>
    </div>
  );
}

// Default Column Filter
function DefaultColumnFilter({ column: { filterValue, setFilter } }) {
  return (
    <input
      value={filterValue || ""}
      onChange={(e) => setFilter(e.target.value || undefined)}
      placeholder={`Filter...`}
      className="table-filter"
    />
  );
}

export default App;
