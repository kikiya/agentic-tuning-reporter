import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Assessment as AssessmentIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { reportApi } from '../api';
import { Report } from '../types';
import ReportTypeModal from './ReportTypeModal';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const { data: reports, isLoading, error, refetch } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportApi.getReports().then(res => res.data),
  });

  const handleCreateReport = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    refetch(); // Refresh reports list in case a new one was generated
  };

  const handleViewReport = (reportId: string) => {
    navigate(`/reports/${reportId}`);
  };

  const handleEditReport = (reportId: string) => {
    navigate(`/reports/${reportId}/edit`);
  };

  const handleDeleteReport = (reportId: string) => {
    if (window.confirm('Are you sure you want to delete this report?')) {
      reportApi.deleteReport(reportId).then(() => {
        refetch();
      }).catch((error) => {
        console.error('Error deleting report:', error);
        alert('Failed to delete report');
      });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'success';
      case 'in_review':
        return 'warning';
      case 'draft':
        return 'default';
      case 'archived':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (isLoading) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <Typography>Loading reports...</Typography>
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <Typography color="error">Error loading reports: {error.message}</Typography>
        </Box>
      </Container>
    );
  }

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <AssessmentIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            CRDB Tuning Report Generator
          </Typography>
          <Button color="inherit" onClick={handleCreateReport} startIcon={<AddIcon />}>
            New Report
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            Reports Dashboard
          </Typography>
        </Box>

        {reports && reports.length === 0 ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="300px">
            <Box textAlign="center">
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No reports found
              </Typography>
              <Button variant="contained" onClick={handleCreateReport} startIcon={<AddIcon />}>
                Create Your First Report
              </Button>
            </Box>
          </Box>
        ) : (
          <Grid container spacing={3}>
            {reports?.map((report: Report) => (
              <Grid key={report.id} size={{ xs: 12, sm: 6, md: 4 }}>
                <Card sx={{ cursor: 'pointer' }} onClick={() => handleViewReport(report.id)}>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                      <Typography variant="h6" component="div" gutterBottom>
                        {report.title}
                      </Typography>
                      <Chip
                        label={report.status}
                        color={getStatusColor(report.status) as any}
                        size="small"
                      />
                    </Box>

                    <Typography variant="body2" color="text.secondary" paragraph>
                      Cluster: {report.cluster_id}
                    </Typography>

                    {report.description && (
                      <Typography variant="body2" paragraph>
                        {report.description.length > 100
                          ? `${report.description.substring(0, 100)}...`
                          : report.description}
                      </Typography>
                    )}

                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="caption" color="text.secondary">
                        Version {report.version}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(report.created_at)}
                      </Typography>
                    </Box>

                    {report.findings && (
                      <Box mt={2}>
                        <Typography variant="body2" color="text.secondary">
                          Findings: {report.findings.length}
                        </Typography>
                      </Box>
                    )}
                  </CardContent>

                  <CardActions onClick={(e) => e.stopPropagation()}>
                    <Button size="small" onClick={(e) => { e.stopPropagation(); handleViewReport(report.id); }}>
                      <VisibilityIcon fontSize="small" sx={{ mr: 0.5 }} />
                      View
                    </Button>
                    <Button size="small" onClick={(e) => { e.stopPropagation(); handleEditReport(report.id); }}>
                      <EditIcon fontSize="small" sx={{ mr: 0.5 }} />
                      Edit
                    </Button>
                    <IconButton
                      size="small"
                      onClick={(e) => { e.stopPropagation(); handleDeleteReport(report.id); }}
                      color="error"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>

      <ReportTypeModal open={isModalOpen} onClose={handleCloseModal} />
    </>
  );
};

export default Dashboard;
