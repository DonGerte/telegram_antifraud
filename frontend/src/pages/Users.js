import React, { useEffect, useState } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TextField, Box, Button } from '@mui/material';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const Users = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ score_min: 0, score_max: 100 });

  useEffect(() => {
    fetchUsers();
  }, [filter]);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/users`, {
        params: filter
      });
      setUsers(response.data.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (userId, action) => {
    try {
      await axios.post(`${API_URL}/api/users/${userId}/action`, {
        action: action,
        reason: 'Manual moderator action'
      });
      alert(`Acción ${action} ejecutada`);
      fetchUsers();
    } catch (error) {
      alert('Error: ' + error.message);
    }
  };

  return (
    <Box sx={{ py: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <TextField
          label="Score Mínimo"
          type="number"
          size="small"
          onChange={(e) => setFilter({ ...filter, score_min: e.target.value })}
        />
        <TextField
          label="Score Máximo"
          type="number"
          size="small"
          onChange={(e) => setFilter({ ...filter, score_max: e.target.value })}
        />
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead sx={{ bgcolor: '#f5f5f5' }}>
            <TableRow>
              <TableCell>Usuario ID</TableCell>
              <TableCell align="right">Score</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell>Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.user_id}>
                <TableCell>{user.user_id}</TableCell>
                <TableCell align="right">{user.current_score?.toFixed(1)}</TableCell>
                <TableCell>
                  <span style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    bgcolor: user.status === 'banned' ? '#f44336' : user.status === 'restricted' ? '#ff9800' : '#4caf50',
                    color: 'white'
                  }}>
                    {user.status}
                  </span>
                </TableCell>
                <TableCell>
                  <Button size="small" onClick={() => handleAction(user.user_id, 'mute')}>Mutecar</Button>
                  <Button size="small" sx={{ color: '#ff9800' }} onClick={() => handleAction(user.user_id, 'restrict')}>Restricción</Button>
                  <Button size="small" sx={{ color: '#f44336' }} onClick={() => handleAction(user.user_id, 'kick')}>Kick</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default Users;
