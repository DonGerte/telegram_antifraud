import React from 'react';
import { useTranslation } from 'react-i18next';
import { Grid, Paper, Typography, Box, CircularProgress } from '@mui/material';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Dashboard = ({ stats, loading }) => {
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!stats) {
    return <Typography color="error">Error: No data available</Typography>;
  }

  const { t } = useTranslation();
  const statusData = [
    { name: t('normal'), value: stats.total_users - stats.restricted - stats.banned },
    { name: t('restricted'), value: stats.restricted },
    { name: t('banned'), value: stats.banned },
  ];

  const COLORS = ['#4caf50', '#ff9800', '#f44336'];

  const StatCard = ({ title, value, color }) => (
    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: color, color: 'white' }}>
      <Typography variant="h6">{title}</Typography>
      <Typography variant="h4" sx={{ mt: 1 }}>{value}</Typography>
    </Paper>
  );

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} sm={6} md={3}>
        <StatCard title={t('total_users')} value={stats.total_users} color="#2196F3" />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <StatCard title={t('actions_today')} value={stats.actions_today} color="#4CAF50" />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <StatCard title={t('restricted')} value={stats.restricted} color="#FF9800" />
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <StatCard title={t('banned')} value={stats.banned} color="#F44336" />
      </Grid>

      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>{t('user_status')}</Typography>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={statusData} cx="50%" cy="50%" labelLine={false} label>
                {statusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Paper>
      </Grid>

      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>{t('recent_actions')}</Typography>
          <Box sx={{ overflowX: 'auto' }}>
            <Typography variant="body2">{t('last_24h')}: {stats.actions_today} {t('actions')}</Typography>
            <Typography variant="body2">{t('last_7d')}: {stats.actions_today * 7} {t('estimated')}</Typography>
          </Box>
        </Paper>
      </Grid>
    </Grid>
  );
};

export default Dashboard;
