import React from 'react';
import { Link } from 'react-router-dom';
import { Box, Button, Stack } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleIcon from '@mui/icons-material/People';
import RuleIcon from '@mui/icons-material/Rule';
import HistoryIcon from '@mui/icons-material/History';
import ErrorIcon from '@mui/icons-material/Error';
import { useTranslation } from 'react-i18next';

const Navigation = () => {
  const { t } = useTranslation();
  const navItems = [
    { label: t('dashboard'), path: '/', icon: DashboardIcon },
    { label: t('users'), path: '/users', icon: PeopleIcon },
    { label: t('rules'), path: '/rules', icon: RuleIcon },
    { label: t('audit'), path: '/audit', icon: HistoryIcon },
    { label: t('alerts'), path: '/alerts', icon: ErrorIcon },
  ];

  return (
    <Box sx={{ bgcolor: '#f5f5f5', py: 2, borderBottom: '1px solid #ddd' }}>
      <Stack direction="row" spacing={2} sx={{ px: 3 }}>
        {navItems.map((item) => (
          <Button
            key={item.path}
            component={Link}
            to={item.path}
            startIcon={<item.icon />}
            sx={{ textTransform: 'none' }}
          >
            {item.label}
          </Button>
        ))}
      </Stack>
    </Box>
  );
};

export default Navigation;
