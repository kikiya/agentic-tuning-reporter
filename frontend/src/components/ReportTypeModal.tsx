import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  TextField,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  AutoAwesome as AutoAwesomeIcon,
  Edit as EditIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { agentApi } from '../api';

interface ReportTypeModalProps {
  open: boolean;
  onClose: () => void;
}

const ReportTypeModal: React.FC<ReportTypeModalProps> = ({ open, onClose }) => {
  const navigate = useNavigate();
  const [showQuickAnalysisForm, setShowQuickAnalysisForm] = useState(false);
  const [database, setDatabase] = useState('bookly');
  const [appName, setAppName] = useState('bookly');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleQuickAnalysis = () => {
    setShowQuickAnalysisForm(true);
    setError(null);
  };

  const handleCustomReport = () => {
    onClose();
    navigate('/reports/create');
  };

  const handleGenerateReport = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await agentApi.generateReport({
        database,
        app: appName,
      });

      if (response.data.success) {
        // Report was generated successfully and created in the database
        // Navigate to the reports list to see it
        onClose();
        navigate('/');
        // The report will appear in the dashboard after refresh
      } else {
        setError(response.data.error || 'Failed to generate report');
      }
    } catch (err: any) {
      console.error('Error generating report:', err);
      setError(err.response?.data?.detail || 'Failed to generate report. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleBack = () => {
    setShowQuickAnalysisForm(false);
    setError(null);
  };

  const handleCloseModal = () => {
    setShowQuickAnalysisForm(false);
    setError(null);
    setDatabase('bookly');
    setAppName('bookly');
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleCloseModal} maxWidth="sm" fullWidth>
      <DialogTitle>
        {showQuickAnalysisForm ? 'Quick Analysis' : 'Choose Report Type'}
      </DialogTitle>

      <DialogContent>
        {!showQuickAnalysisForm ? (
          <Box sx={{ py: 2 }}>
            {/* Quick Analysis Option */}
            <Box
              sx={{
                p: 3,
                mb: 2,
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                cursor: 'pointer',
                '&:hover': {
                  bgcolor: 'action.hover',
                },
              }}
              onClick={handleQuickAnalysis}
            >
              <Box display="flex" alignItems="center" mb={1}>
                <AutoAwesomeIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Quick Analysis</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" paragraph>
                AI-powered performance analysis
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Generate a report, then edit as needed
              </Typography>
            </Box>

            {/* Custom Report Option */}
            <Box
              sx={{
                p: 3,
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                cursor: 'pointer',
                '&:hover': {
                  bgcolor: 'action.hover',
                },
              }}
              onClick={handleCustomReport}
            >
              <Box display="flex" alignItems="center" mb={1}>
                <EditIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Custom Report</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Start from scratch with full control
              </Typography>
            </Box>
          </Box>
        ) : (
          <Box sx={{ py: 2 }}>
            <Typography variant="body2" color="text.secondary" paragraph>
              Configure your AI-powered performance analysis
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            <TextField
              fullWidth
              label="Database Name"
              value={database}
              onChange={(e) => setDatabase(e.target.value)}
              margin="normal"
              disabled={isGenerating}
              helperText="The database to analyze"
            />

            <TextField
              fullWidth
              label="Application Name"
              value={appName}
              onChange={(e) => setAppName(e.target.value)}
              margin="normal"
              disabled={isGenerating}
              helperText="Filter slow statements by application"
            />

            {isGenerating && (
              <Box display="flex" alignItems="center" justifyContent="center" mt={3}>
                <CircularProgress size={24} sx={{ mr: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  Analyzing cluster performance...
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        {!showQuickAnalysisForm ? (
          <Button onClick={handleCloseModal}>Cancel</Button>
        ) : (
          <>
            <Button onClick={handleBack} disabled={isGenerating}>
              Back
            </Button>
            <Button onClick={handleCloseModal} disabled={isGenerating}>
              Cancel
            </Button>
            <Button
              onClick={handleGenerateReport}
              variant="contained"
              disabled={isGenerating || !database || !appName}
              startIcon={isGenerating ? <CircularProgress size={20} /> : <AutoAwesomeIcon />}
            >
              {isGenerating ? 'Generating...' : 'Generate'}
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ReportTypeModal;
