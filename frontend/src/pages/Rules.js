import React, { useEffect, useState } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, Dialog, DialogTitle, DialogContent, TextField, Box } from '@mui/material';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const Rules = () => {
  const [rules, setRules] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [newRule, setNewRule] = useState({ name: '', priority: 1, conditions: '', actions: '' });

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/rules`);
      setRules(response.data.rules || []);
    } catch (error) {
      console.error('Error fetching rules:', error);
    }
  };

  const handleCreateRule = async () => {
    try {
      await axios.post(`${API_URL}/api/rules`, newRule);
      alert('Regla creada exitosamente');
      setOpenDialog(false);
      fetchRules();
    } catch (error) {
      alert('Error: ' + error.message);
    }
  };

  const handleDeleteRule = async (ruleId) => {
    if (window.confirm('¿Eliminar esta regla?')) {
      try {
        await axios.delete(`${API_URL}/api/rules/${ruleId}`);
        fetchRules();
      } catch (error) {
        alert('Error: ' + error.message);
      }
    }
  };

  return (
    <Box sx={{ py: 3 }}>
      <Button variant="contained" sx={{ mb: 2 }} onClick={() => setOpenDialog(true)}>
        + Nueva Regla
      </Button>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Crear Nueva Regla</DialogTitle>
        <DialogContent sx={{ minWidth: '400px', pt: 2 }}>
          <TextField
            fullWidth
            label="Nombre"
            size="small"
            sx={{ mb: 2 }}
            onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
          />
          <TextField
            fullWidth
            label="Prioridad"
            type="number"
            size="small"
            sx={{ mb: 2 }}
            onChange={(e) => setNewRule({ ...newRule, priority: parseInt(e.target.value) })}
          />
          <TextField
            fullWidth
            label="Condiciones (JSON)"
            multiline
            rows={4}
            size="small"
            sx={{ mb: 2 }}
            onChange={(e) => setNewRule({ ...newRule, conditions: e.target.value })}
          />
          <TextField
            fullWidth
            label="Acciones"
            size="small"
            onChange={(e) => setNewRule({ ...newRule, actions: e.target.value })}
          />
          <Button onClick={handleCreateRule} variant="contained" sx={{ mt: 2 }}>Crear</Button>
        </DialogContent>
      </Dialog>

      <TableContainer component={Paper}>
        <Table>
          <TableHead sx={{ bgcolor: '#f5f5f5' }}>
            <TableRow>
              <TableCell>Nombre</TableCell>
              <TableCell align="right">Prioridad</TableCell>
              <TableCell>Habilitada</TableCell>
              <TableCell>Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rules.map((rule) => (
              <TableRow key={rule.id}>
                <TableCell>{rule.name}</TableCell>
                <TableCell align="right">{rule.priority}</TableCell>
                <TableCell>{rule.enabled ? '✅' : '❌'}</TableCell>
                <TableCell>
                  <Button size="small">Editar</Button>
                  <Button size="small" sx={{ color: '#f44336' }} onClick={() => handleDeleteRule(rule.id)}>Eliminar</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default Rules;
