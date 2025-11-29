import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  IconButton,
} from '@mui/material';
import { Person as PersonIcon, Info as InfoIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface LayoutProps {
  children: React.ReactNode;
  selectedUser: string;
  onUserChange: (user: string) => void;
}

const Layout: React.FC<LayoutProps> = ({ children, selectedUser, onUserChange }) => {
  const navigate = useNavigate();

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, cursor: 'pointer' }}
            onClick={() => navigate('/')}
          >
            CockroachDB Tuning Reporter
          </Typography>

          {/* Demo User Selector */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip 
              title="Demo Mode: Switch users to see how access control filters similarity search results"
              arrow
            >
              <IconButton size="small" sx={{ color: 'white' }}>
                <InfoIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            
            <PersonIcon sx={{ mr: 1 }} />
            
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel 
                sx={{ 
                  color: 'white',
                  '&.Mui-focused': { color: 'white' }
                }}
              >
                Demo User
              </InputLabel>
              <Select
                value={selectedUser}
                label="Demo User"
                onChange={(e) => onUserChange(e.target.value)}
                sx={{
                  color: 'white',
                  '.MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.5)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.8)',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'white',
                  },
                  '.MuiSvgIcon-root': {
                    color: 'white',
                  },
                }}
              >
                <MenuItem value="analyst_alice">
                  <Box>
                    <Typography variant="body2">Alice Johnson</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Analyst • Acme Corp only
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="analyst_bob">
                  <Box>
                    <Typography variant="body2">Bob Smith</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Analyst • Globex only
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem value="admin_charlie">
                  <Box>
                    <Typography variant="body2">Charlie Davis</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Admin • All customers
                    </Typography>
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Toolbar>
      </AppBar>
      
      <Box component="main" sx={{ flexGrow: 1 }}>
        {children}
      </Box>
    </Box>
  );
};

export default Layout;
