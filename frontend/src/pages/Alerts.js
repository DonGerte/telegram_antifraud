import React, { useEffect, useState } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Box, Typography, Chip } from '@mui/material';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const Alerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/alerts`);
      setAlerts(response.data.alerts || []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'critical': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ py: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>Alertas en Tiempo Real</Typography>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead sx={{ bgcolor: '#f5f5f5' }}>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>Severidad</TableCell>
              <TableCell>Tipo</TableCell>
              <TableCell>Descripción</TableCell>
              <TableCell>Valor</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {alerts.map((alert, idx) => (
              <TableRow key={idx}>
                <TableCell>{new Date(alert.timestamp).toLocaleString()}</TableCell>
                <TableCell>
                  <Chip
                    label={alert.severity || 'info'}
                    color={getSeverityColor(alert.severity)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{alert.alert_type}</TableCell>
                <TableCell>{alert.description}</TableCell>
                <TableCell align="right">{alert.value?.toFixed(2)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {alerts.length === 0 && (
        <Box sx={{ py: 3, textAlign: 'center' }}>
          <Typography color="textSecondary">✅ Sin alertas activas</Typography>
        </Box>
      )}
    </Box>
  );
};

export default Alerts;
