import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Dashboard from './components/Dashboard';
import ReportForm from './components/ReportForm';
import ReportDetail from './components/ReportDetail';
import Layout from './components/Layout';

// Create a React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Create Material-UI theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

// Create a context for the selected user
export const UserContext = React.createContext<{
  selectedUser: string;
  setSelectedUser: (user: string) => void;
}>({
  selectedUser: 'analyst_alice',
  setSelectedUser: () => {},
});

function App() {
  const [selectedUser, setSelectedUser] = React.useState('analyst_alice');

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <UserContext.Provider value={{ selectedUser, setSelectedUser }}>
          <Router>
            <Layout selectedUser={selectedUser} onUserChange={setSelectedUser}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/reports" element={<Dashboard />} />
                <Route path="/reports/create" element={<ReportForm mode="create" />} />
                <Route path="/reports/:reportId/edit" element={<ReportForm mode="edit" />} />
                <Route path="/reports/:reportId" element={<ReportDetail />} />
              </Routes>
            </Layout>
          </Router>
        </UserContext.Provider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
