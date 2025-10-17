import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  AppBar,
  Toolbar,
  IconButton,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
  Archive as ArchiveIcon,
  Publish as PublishIcon,
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { reportApi } from '../api';
import { Report, CreateReportRequest, UpdateReportRequest } from '../types';

// Validation schema
const reportSchema = yup.object({
  cluster_id: yup.string().required('Cluster ID is required'),
  title: yup.string().required('Title is required').min(3, 'Title must be at least 3 characters'),
  description: yup.string(),
  status: yup.string().oneOf(['draft', 'in_review', 'published', 'archived']),
});

type ReportFormData = yup.InferType<typeof reportSchema>;

interface ReportFormProps {
  mode: 'create' | 'edit';
}

const ReportForm: React.FC<ReportFormProps> = ({ mode }) => {
  const navigate = useNavigate();
  const { reportId } = useParams<{ reportId: string }>();
  const queryClient = useQueryClient();

  // Fetch report data for edit mode
  const { data: report, isLoading: isLoadingReport } = useQuery({
    queryKey: ['report', reportId],
    queryFn: () => reportId ? reportApi.getReport(reportId).then(res => res.data) : null,
    enabled: mode === 'edit' && !!reportId,
  });

  // Form setup
  const {
    control,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<ReportFormData>({
    resolver: yupResolver(reportSchema) as any,
    defaultValues: {
      cluster_id: '',
      title: '',
      description: '',
      status: 'draft',
    },
  });

  // Reset form when report data loads (for edit mode)
  useEffect(() => {
    if (mode === 'edit' && report) {
      reset({
        cluster_id: report.cluster_id,
        title: report.title,
        description: report.description || '',
        status: report.status,
      });
    }
  }, [report, mode, reset]);

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: async (data: ReportFormData) => {
      if (mode === 'create') {
        const createData: CreateReportRequest = {
          cluster_id: data.cluster_id,
          title: data.title,
          description: data.description,
        };
        return reportApi.createReport(createData).then(res => res.data);
      } else {
        const updateData: UpdateReportRequest = {
          title: data.title,
          description: data.description,
          status: data.status as UpdateReportRequest['status'],
        };
        return reportApi.updateReport(reportId!, updateData).then(res => res.data);
      }
    },
    onSuccess: (saved: Report) => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      if (mode === 'create') {
        navigate(`/reports/${saved.id}`);
      } else {
        navigate(`/reports/${reportId}`);
      }
    },
    onError: (error: any) => {
      console.error('Error saving report:', error);
    },
  });

  // Delete mutation (for archiving)
  const deleteMutation = useMutation({
    mutationFn: () => reportApi.deleteReport(reportId!).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      navigate('/');
    },
  });

  const onSubmit = (data: ReportFormData) => {
    saveMutation.mutate(data);
  };

  const handleArchive = () => {
    if (mode === 'edit' && report) {
      const archiveData: UpdateReportRequest = { status: 'archived' };
      reportApi.updateReport(reportId!, archiveData).then(() => {
        queryClient.invalidateQueries({ queryKey: ['reports'] });
        navigate('/');
      });
    }
  };

  const handlePublish = () => {
    if (mode === 'edit' && report) {
      const publishData: UpdateReportRequest = { status: 'published' };
      reportApi.updateReport(reportId!, publishData).then(() => {
        queryClient.invalidateQueries({ queryKey: ['reports'] });
        navigate('/');
      });
    }
  };

  if (mode === 'edit' && isLoadingReport) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate('/')}
            sx={{ mr: 2 }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            {mode === 'create' ? 'Create New Report' : `Edit Report: ${report?.title}`}
          </Typography>
          {mode === 'edit' && (
            <Box>
              <Button
                color="inherit"
                onClick={handlePublish}
                startIcon={<PublishIcon />}
                sx={{ mr: 1 }}
              >
                Publish
              </Button>
              <Button
                color="inherit"
                onClick={handleArchive}
                startIcon={<ArchiveIcon />}
              >
                Archive
              </Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h5" component="h1" gutterBottom>
              Report Details
            </Typography>

            {saveMutation.error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                Error saving report: {saveMutation.error.message}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
              <Controller
                name="cluster_id"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    margin="normal"
                    required
                    fullWidth
                    label="Cluster ID"
                    error={!!errors.cluster_id}
                    helperText={errors.cluster_id?.message}
                    placeholder="e.g., prod-cluster-001"
                  />
                )}
              />

              <Controller
                name="title"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    margin="normal"
                    required
                    fullWidth
                    label="Report Title"
                    error={!!errors.title}
                    helperText={errors.title?.message}
                    placeholder="e.g., Q4 2024 Performance Tuning Report"
                  />
                )}
              />

              <Controller
                name="description"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    margin="normal"
                    fullWidth
                    multiline
                    rows={4}
                    label="Description"
                    error={!!errors.description}
                    helperText={errors.description?.message}
                    placeholder="Describe the purpose and scope of this tuning report..."
                  />
                )}
              />

              <Controller
                name="status"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth margin="normal" error={!!errors.status}>
                    <InputLabel>Status</InputLabel>
                    <Select {...field} label="Status">
                      <MenuItem value="draft">Draft</MenuItem>
                      <MenuItem value="in_review">In Review</MenuItem>
                      <MenuItem value="published">Published</MenuItem>
                      <MenuItem value="archived">Archived</MenuItem>
                    </Select>
                    {errors.status && <FormHelperText>{errors.status.message}</FormHelperText>}
                  </FormControl>
                )}
              />

              {mode === 'edit' && report && (
                <Box mt={2} p={2} bgcolor="grey.50" borderRadius={1}>
                  <Typography variant="body2" color="text.secondary">
                    <strong>Created:</strong> {new Date(report.created_at).toLocaleString()}
                    <br />
                    <strong>Last Updated:</strong> {new Date(report.updated_at).toLocaleString()}
                    <br />
                    <strong>Version:</strong> {report.version}
                  </Typography>
                </Box>
              )}

              <Box mt={3} display="flex" gap={2}>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<SaveIcon />}
                  disabled={saveMutation.isPending}
                >
                  {saveMutation.isPending ? 'Saving...' : 'Save Report'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/')}
                >
                  Cancel
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </>
  );
};

export default ReportForm;
