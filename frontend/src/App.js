import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Container, AppBar, Toolbar, Typography } from '@mui/material';
import axios from 'axios';

import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import Rules from './pages/Rules';
import AuditLog from './pages/AuditLog';
import Alerts from './pages/Alerts';
import Navigation from './components/Navigation';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/stats`);
      setStats(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch stats');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Router>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            🛡️ Telegram Antifraud Dashboard
          </Typography>
          <Typography variant="body2">
            {stats && `Usuarios: ${stats.total_users} | En restricción: ${stats.restricted}`}
          </Typography>
        </Toolbar>
      </AppBar>

      <Navigation />

      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Routes>
          <Route path="/" element={<Dashboard stats={stats} loading={loading} />} />
          <Route path="/users" element={<Users />} />
          <Route path="/rules" element={<Rules />} />
          <Route path="/audit" element={<AuditLog />} />
          <Route path="/alerts" element={<Alerts />} />
        </Routes>
      </Container>
    </Router>
  );
}

export default App;
