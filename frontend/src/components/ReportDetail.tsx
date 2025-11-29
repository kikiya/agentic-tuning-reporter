import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Divider,
  AppBar,
  Toolbar,
  IconButton,
  Tab,
  Tabs,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Add as AddIcon,
  BugReport as BugReportIcon,
  Build as BuildIcon,
  Comment as CommentIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { reportApi } from '../api';
import { Report, Finding, RecommendedAction, Comment, ReportStatusHistory, CreateActionRequest, UpdateActionRequest, UpdateFindingRequest } from '../types';
import { UserContext } from '../App';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`report-tabpanel-${index}`}
      aria-labelledby={`report-tab-${index}`}
      tabIndex={0}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ReportDetail: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const [tabValue, setTabValue] = React.useState(0);
  const queryClient = useQueryClient();

  // State for adding a finding
  const [findingOpen, setFindingOpen] = React.useState(false);
  const [newFinding, setNewFinding] = React.useState({
    title: '',
    description: '',
    category: 'performance',
    severity: 'medium',
    tags: '' as string,
  });

  // State for similar reports dialog
  const [similarReportsOpen, setSimilarReportsOpen] = React.useState(false);
  
  // Get current user from context
  const { selectedUser } = React.useContext(UserContext);

  // Redirect to dashboard if user switches while viewing a report
  const previousUserRef = React.useRef(selectedUser);
  React.useEffect(() => {
    if (previousUserRef.current && previousUserRef.current !== selectedUser) {
      navigate('/');
    }
    previousUserRef.current = selectedUser;
  }, [selectedUser, navigate]);

  const updateFindingMutation = useMutation({
    mutationFn: async () => {
      if (!editingFindingId) return;
      const payload: UpdateFindingRequest = {
        title: editFinding.title,
        description: editFinding.description,
        category: editFinding.category as UpdateFindingRequest['category'],
        severity: editFinding.severity as UpdateFindingRequest['severity'],
        tags: editFinding.tags
          .split(',')
          .map(t => t.trim())
          .filter(Boolean),
      };
      return reportApi.updateFinding(editingFindingId, payload).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report', reportId] });
      setEditFindingOpen(false);
      setEditingFindingId(null);
    },
  });

  const updateActionMutation = useMutation({
    mutationFn: async () => {
      if (!editingActionId) return;
      const payload: UpdateActionRequest = {
        title: editAction.title,
        description: editAction.description,
        action_type: editAction.action_type as UpdateActionRequest['action_type'],
        priority: editAction.priority as UpdateActionRequest['priority'],
        estimated_effort: editAction.estimated_effort as UpdateActionRequest['estimated_effort'],
        status: editAction.status as UpdateActionRequest['status'],
        due_date: editAction.due_date ? new Date(editAction.due_date).toISOString() : undefined,
        implementation_notes: editAction.implementation_notes || undefined,
      };
      return reportApi.updateAction(editingActionId, payload).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report', reportId] });
      setEditActionOpen(false);
      setEditingActionId(null);
    },
  });

  // State for adding a comment
  const [commentText, setCommentText] = React.useState('');

  // State for adding an action to a finding
  const [actionOpen, setActionOpen] = React.useState(false);
  const [actionFindingId, setActionFindingId] = React.useState<string | null>(null);
  const [newAction, setNewAction] = React.useState({
    title: '',
    description: '',
    action_type: 'configuration_change',
    priority: 'medium',
    estimated_effort: 'medium',
    due_date: '' as string,
  });

  // State for editing a finding
  const [editFindingOpen, setEditFindingOpen] = React.useState(false);
  const [editingFindingId, setEditingFindingId] = React.useState<string | null>(null);
  const [editFinding, setEditFinding] = React.useState({
    title: '',
    description: '',
    category: 'performance',
    severity: 'medium',
    tags: '' as string,
  });

  // State for editing an action
  const [editActionOpen, setEditActionOpen] = React.useState(false);
  const [editingActionId, setEditingActionId] = React.useState<string | null>(null);
  const [editAction, setEditAction] = React.useState({
    title: '',
    description: '',
    action_type: 'configuration_change',
    priority: 'medium',
    estimated_effort: 'medium',
    status: 'pending',
    due_date: '' as string,
    implementation_notes: '',
  });

  const { data: report, isLoading, error } = useQuery({
    queryKey: ['report', reportId],
    queryFn: () => reportId ? reportApi.getReport(reportId).then(res => res.data) : null,
    enabled: !!reportId,
  });

  // Query for similar reports (only fetch when dialog is open)
  const { data: similarReports, isLoading: similarReportsLoading } = useQuery({
    queryKey: ['similarReports', reportId, selectedUser],
    queryFn: () => {
      if (!reportId) return null;
      return reportApi.getSimilarReports(reportId, 5, selectedUser).then(res => res.data);
    },
    enabled: !!reportId && similarReportsOpen,
  });

  // Mutations
  const createFindingMutation = useMutation({
    mutationFn: async () => {
      if (!reportId) return;
      const payload = {
        title: newFinding.title,
        description: newFinding.description,
        category: newFinding.category as Finding['category'],
        severity: newFinding.severity as Finding['severity'],
        tags: newFinding.tags
          .split(',')
          .map(t => t.trim())
          .filter(Boolean),
      };
      return reportApi.createFinding(reportId, payload).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report', reportId] });
      setFindingOpen(false);
      setNewFinding({ title: '', description: '', category: 'performance', severity: 'medium', tags: '' });
    },
  });

  const publishReportMutation = useMutation({
    mutationFn: async () => {
      if (!reportId) return;
      return reportApi.updateReport(reportId, { status: 'published' }).then((res) => res.data);
    },
    onSuccess: (updatedReport) => {
      if (!reportId) return;
      queryClient.setQueryData(['report', reportId], updatedReport);
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
  });

  const createCommentMutation = useMutation({
    mutationFn: async () => {
      if (!reportId) return;
      return reportApi.createComment(reportId, { content: commentText }).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report', reportId] });
      setCommentText('');
    },
  });

  const createActionMutation = useMutation({
    mutationFn: async () => {
      if (!actionFindingId) return;
      const payload = {
        title: newAction.title,
        description: newAction.description,
        action_type: newAction.action_type as CreateActionRequest['action_type'],
        priority: newAction.priority as CreateActionRequest['priority'],
        estimated_effort: newAction.estimated_effort as CreateActionRequest['estimated_effort'],
        due_date: newAction.due_date ? new Date(newAction.due_date).toISOString() : undefined,
      };
      return reportApi.createAction(actionFindingId, payload).then(r => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report', reportId] });
      setActionOpen(false);
      setActionFindingId(null);
      setNewAction({
        title: '',
        description: '',
        action_type: 'configuration_change',
        priority: 'medium',
        estimated_effort: 'medium',
        due_date: '',
      });
    },
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    if (typeof document !== 'undefined' && document.activeElement instanceof HTMLElement) {
      document.activeElement.blur();
    }
    setTabValue(newValue);
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'success';
      default:
        return 'default';
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

  const getActionStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'info';
      case 'pending':
        return 'default';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  if (isLoading) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <Typography>Loading report...</Typography>
        </Box>
      </Container>
    );
  }

  if (error || !report) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <Alert severity="error">
            {error ? `Error loading report: ${error.message}` : 'Report not found'}
          </Alert>
        </Box>
      </Container>
    );
  }

  return (
    <>
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        {/* Report Header */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
              <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
                {report.title}
              </Typography>
              <Box display="flex" gap={1} alignItems="center">
                <Chip
                  label={report.status}
                  color={getStatusColor(report.status) as any}
                  size="medium"
                />
                {report.status !== 'published' && (
                  <Button
                    variant="contained"
                    color="success"
                    size="small"
                    onClick={() => publishReportMutation.mutate()}
                    disabled={publishReportMutation.isPending}
                  >
                    {publishReportMutation.isPending ? 'Publishing…' : 'Publish'}
                  </Button>
                )}
                <Button
                  variant="outlined"
                  onClick={() => setSimilarReportsOpen(true)}
                  startIcon={<SearchIcon />}
                  size="small"
                >
                  Find Similar
                </Button>
                <Button
                  variant="contained"
                  onClick={() => navigate(`/reports/${reportId}/edit`)}
                  startIcon={<EditIcon />}
                  size="small"
                >
                  Edit
                </Button>
              </Box>
            </Box>

            <Typography variant="body1" paragraph>
              Cluster: <strong>{report.cluster_id}</strong>
            </Typography>

            {report.description && (
              <Typography variant="body1" paragraph>
                {report.description}
              </Typography>
            )}

            <Box display="flex" gap={2} flexWrap="wrap">
              <Typography variant="body2" color="text.secondary">
                Version: {report.version}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Created: {new Date(report.created_at).toLocaleDateString()}
              </Typography>
              {report.generated_at && (
                <Typography variant="body2" color="text.secondary">
                  Generated: {new Date(report.generated_at).toLocaleDateString()}
                </Typography>
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Tabs for different sections */}
        <Card>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="report sections">
              <Tab label={`Findings (${report.findings?.length || 0})`} />
              <Tab label={`Comments (${report.comments?.length || 0})`} />
              <Tab label="Status History" />
            </Tabs>
          </Box>

          {/* Findings Tab */}
          <TabPanel value={tabValue} index={0}>
            <Box display="flex" justifyContent="flex-end" mb={2}>
              <Button variant="contained" size="small" startIcon={<AddIcon />} onClick={() => {
                if (typeof document !== 'undefined' && document.activeElement instanceof HTMLElement) {
                  document.activeElement.blur();
                }
                setFindingOpen(true);
              }}>
                Add Finding
              </Button>
            </Box>
            {report.findings && report.findings.length > 0 ? (
              <Box display="grid" gridTemplateColumns={{ xs: '1fr' }} gap={3}>
                {report.findings.map((finding: Finding) => (
                  <Box key={finding.id}>
                    <Card>
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                          <Typography variant="h6">
                            {finding.title}
                          </Typography>
                          <Box display="flex" gap={1}>
                            <Chip
                              label={finding.category}
                              size="small"
                              variant="outlined"
                            />
                            <Chip
                              label={finding.severity}
                              color={getSeverityColor(finding.severity) as any}
                              size="small"
                            />
                            <Chip
                              label={finding.status}
                              color={getStatusColor(finding.status) as any}
                              size="small"
                            />
                          </Box>
                          <Box mt={1} display="flex" justifyContent="flex-end" gap={1}>
                            <Button
                              size="small"
                              variant="text"
                              startIcon={<EditIcon />}
                              onClick={() => {
                                if (typeof document !== 'undefined' && document.activeElement instanceof HTMLElement) {
                                  document.activeElement.blur();
                                }
                                setEditingFindingId(finding.id);
                                setEditFinding({
                                  title: finding.title,
                                  description: finding.description,
                                  category: finding.category as string,
                                  severity: finding.severity as string,
                                  tags: (finding.tags || []).join(','),
                                });
                                setEditFindingOpen(true);
                              }}
                            >
                              Edit Finding
                            </Button>
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<BuildIcon />}
                              onClick={() => {
                                if (typeof document !== 'undefined' && document.activeElement instanceof HTMLElement) {
                                  document.activeElement.blur();
                                }
                                setActionFindingId(finding.id);
                                setActionOpen(true);
                              }}
                            >
                              Add Action
                            </Button>
                          </Box>
                        </Box>

                        <Typography variant="body1" paragraph>
                          {finding.description}
                        </Typography>

                        {finding.tags && finding.tags.length > 0 && (
                          <Box mb={2}>
                            {finding.tags.map((tag: string) => (
                              <Chip key={tag} label={tag} size="small" sx={{ mr: 1 }} />
                            ))}
                          </Box>
                        )}

                        {/* Actions for this finding */}
                        {finding.actions && finding.actions.length > 0 && (
                          <Box mt={3}>
                            <Typography variant="h6" gutterBottom>
                              Recommended Actions
                            </Typography>
                            {finding.actions.map((action: RecommendedAction) => (
                              <Card key={action.id} variant="outlined" sx={{ mb: 2 }}>
                                <CardContent>
                                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                                    <Typography variant="subtitle1">
                                      {action.title}
                                    </Typography>
                                    <Chip
                                      label={action.status}
                                      color={getActionStatusColor(action.status) as any}
                                      size="small"
                                    />
                                  </Box>
                                  <Typography variant="body2" color="text.secondary">
                                    {action.description}
                                  </Typography>
                                  <Box mt={1} display="flex" gap={1}>
                                    <Chip label={action.action_type} size="small" variant="outlined" />
                                    <Chip label={action.priority} size="small" variant="outlined" />
                                  </Box>
                                  <Box mt={1} display="flex" justifyContent="flex-end">
                                    <Button
                                      size="small"
                                      variant="text"
                                      startIcon={<EditIcon />}
                                      onClick={() => {
                                        if (typeof document !== 'undefined' && document.activeElement instanceof HTMLElement) {
                                          document.activeElement.blur();
                                        }
                                        setEditingActionId(action.id);
                                        setEditAction({
                                          title: action.title,
                                          description: action.description,
                                          action_type: action.action_type as string,
                                          priority: action.priority as string,
                                          estimated_effort: action.estimated_effort as string,
                                          status: action.status as string,
                                          due_date: action.due_date ? new Date(action.due_date).toISOString().slice(0, 10) : '',
                                          implementation_notes: action.implementation_notes || '',
                                        });
                                        setEditActionOpen(true);
                                      }}
                                    >
                                      Edit Action
                                    </Button>
                                  </Box>
                                </CardContent>
                              </Card>
                            ))}
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  </Box>
                ))}
              </Box>
            ) : (
              <Box textAlign="center" py={4}>
                <BugReportIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  No findings yet
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Add findings to document issues discovered during cluster analysis
                </Typography>
              </Box>
            )}
          </TabPanel>

          {/* Comments Tab */}
          <TabPanel value={tabValue} index={1}>
            {report.comments && report.comments.length > 0 ? (
              <List>
                {report.comments.map((comment: Comment, index: number) => (
                  <React.Fragment key={comment.id}>
                    <ListItem alignItems="flex-start">
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="subtitle2">
                              Comment by User {comment.author_id}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(comment.created_at).toLocaleString()}
                            </Typography>
                          </Box>
                        }
                        secondary={comment.content}
                        primaryTypographyProps={{ component: 'div' }}
                      />
                    </ListItem>
                    {index < ((report.comments?.length ?? 0) - 1) && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Box textAlign="center" py={4}>
                <CommentIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  No comments yet
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Add comments to discuss findings and recommendations
                </Typography>
              </Box>
            )}

            {/* Add comment form */}
            <Box mt={2} display="flex" gap={1}>
              <TextField
                fullWidth
                placeholder="Write a comment..."
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                multiline
                minRows={2}
              />
              <Button
                variant="contained"
                onClick={() => createCommentMutation.mutate()}
                disabled={!commentText.trim() || createCommentMutation.isPending}
              >
                Post
              </Button>
            </Box>
          </TabPanel>

          {/* Status History Tab */}
          <TabPanel value={tabValue} index={2}>
            {report.status_history && report.status_history.length > 0 ? (
              <List>
                {report.status_history.map((history: ReportStatusHistory, index: number) => (
                  <React.Fragment key={history.id}>
                    <ListItem>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Chip label={history.new_status} size="small" />
                            <Typography variant="body2">
                              Changed by User {history.changed_by}
                            </Typography>
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {new Date(history.created_at).toLocaleString()}
                            </Typography>
                            {history.change_reason && (
                              <Typography variant="body2" style={{ marginTop: 4 }}>
                                Reason: {history.change_reason}
                              </Typography>
                            )}
                          </Box>
                        }
                        secondaryTypographyProps={{ component: 'div' }}
                      />
                    </ListItem>
                    {index < ((report.status_history?.length ?? 0) - 1) && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Box textAlign="center" py={4}>
                <Typography variant="body1" color="text.secondary">
                  No status history available
                </Typography>
              </Box>
            )}
          </TabPanel>
        </Card>
      </Container>

      {/* Create Finding Dialog */}
      <Dialog open={findingOpen} onClose={() => setFindingOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Finding</DialogTitle>
        <DialogContent>
          <Box mt={1} display="flex" flexDirection="column" gap={2}>
            <TextField
              label="Title"
              value={newFinding.title}
              onChange={(e) => setNewFinding({ ...newFinding, title: e.target.value })}
              fullWidth
            />
            <TextField
              label="Description"
              value={newFinding.description}
              onChange={(e) => setNewFinding({ ...newFinding, description: e.target.value })}
              fullWidth
              multiline
              minRows={3}
            />
            <Box display="flex" gap={2}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  label="Category"
                  value={newFinding.category}
                  onChange={(e) => setNewFinding({ ...newFinding, category: e.target.value as string })}
                >
                  <MenuItem value="performance">Performance</MenuItem>
                  <MenuItem value="configuration">Configuration</MenuItem>
                  <MenuItem value="security">Security</MenuItem>
                  <MenuItem value="reliability">Reliability</MenuItem>
                  <MenuItem value="monitoring">Monitoring</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Severity</InputLabel>
                <Select
                  label="Severity"
                  value={newFinding.severity}
                  onChange={(e) => setNewFinding({ ...newFinding, severity: e.target.value as string })}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <TextField
              label="Tags (comma separated)"
              value={newFinding.tags}
              onChange={(e) => setNewFinding({ ...newFinding, tags: e.target.value })}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFindingOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => createFindingMutation.mutate()}
            disabled={!newFinding.title.trim() || !newFinding.description.trim() || createFindingMutation.isPending}
          >
            Add Finding
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Finding Dialog */}
      <Dialog open={editFindingOpen} onClose={() => setEditFindingOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Finding</DialogTitle>
        <DialogContent>
          <Box mt={1} display="flex" flexDirection="column" gap={2}>
            <TextField
              label="Title"
              value={editFinding.title}
              onChange={(e) => setEditFinding({ ...editFinding, title: e.target.value })}
              fullWidth
            />
            <TextField
              label="Description"
              value={editFinding.description}
              onChange={(e) => setEditFinding({ ...editFinding, description: e.target.value })}
              fullWidth
              multiline
              minRows={3}
            />
            <Box display="flex" gap={2}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  label="Category"
                  value={editFinding.category}
                  onChange={(e) => setEditFinding({ ...editFinding, category: e.target.value as string })}
                >
                  <MenuItem value="performance">Performance</MenuItem>
                  <MenuItem value="configuration">Configuration</MenuItem>
                  <MenuItem value="security">Security</MenuItem>
                  <MenuItem value="reliability">Reliability</MenuItem>
                  <MenuItem value="monitoring">Monitoring</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Severity</InputLabel>
                <Select
                  label="Severity"
                  value={editFinding.severity}
                  onChange={(e) => setEditFinding({ ...editFinding, severity: e.target.value as string })}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <TextField
              label="Tags (comma separated)"
              value={editFinding.tags}
              onChange={(e) => setEditFinding({ ...editFinding, tags: e.target.value })}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditFindingOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => updateFindingMutation.mutate()}
            disabled={!editFinding.title.trim() || !editFinding.description.trim() || updateFindingMutation.isPending}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Action Dialog */}
      <Dialog open={editActionOpen} onClose={() => setEditActionOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Recommended Action</DialogTitle>
        <DialogContent>
          <Box mt={1} display="flex" flexDirection="column" gap={2}>
            <TextField
              label="Title"
              value={editAction.title}
              onChange={(e) => setEditAction({ ...editAction, title: e.target.value })}
              fullWidth
            />
            <TextField
              label="Description"
              value={editAction.description}
              onChange={(e) => setEditAction({ ...editAction, description: e.target.value })}
              fullWidth
              multiline
              minRows={3}
            />
            <Box display="flex" gap={2}>
              <FormControl fullWidth>
                <InputLabel>Action Type</InputLabel>
                <Select
                  label="Action Type"
                  value={editAction.action_type}
                  onChange={(e) => setEditAction({ ...editAction, action_type: e.target.value as string })}
                >
                  <MenuItem value="configuration_change">Configuration Change</MenuItem>
                  <MenuItem value="query_optimization">Query Optimization</MenuItem>
                  <MenuItem value="index_creation">Index Creation</MenuItem>
                  <MenuItem value="hardware_upgrade">Hardware Upgrade</MenuItem>
                  <MenuItem value="monitoring_setup">Monitoring Setup</MenuItem>
                  <MenuItem value="backup_strategy">Backup Strategy</MenuItem>
                  <MenuItem value="security_hardening">Security Hardening</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  label="Priority"
                  value={editAction.priority}
                  onChange={(e) => setEditAction({ ...editAction, priority: e.target.value as string })}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="urgent">Urgent</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box display="flex" gap={2}>
              <FormControl fullWidth>
                <InputLabel>Estimated Effort</InputLabel>
                <Select
                  label="Estimated Effort"
                  value={editAction.estimated_effort}
                  onChange={(e) => setEditAction({ ...editAction, estimated_effort: e.target.value as string })}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  label="Status"
                  value={editAction.status}
                  onChange={(e) => setEditAction({ ...editAction, status: e.target.value as string })}
                >
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="in_progress">In Progress</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="cancelled">Cancelled</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box display="flex" gap={2}>
              <TextField
                label="Due Date"
                type="date"
                value={editAction.due_date}
                onChange={(e) => setEditAction({ ...editAction, due_date: e.target.value })}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Box>
            <TextField
              label="Implementation Notes"
              value={editAction.implementation_notes}
              onChange={(e) => setEditAction({ ...editAction, implementation_notes: e.target.value })}
              fullWidth
              multiline
              minRows={2}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditActionOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => updateActionMutation.mutate()}
            disabled={!editAction.title.trim() || !editAction.description.trim() || updateActionMutation.isPending}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Action Dialog */}
      <Dialog open={actionOpen} onClose={() => setActionOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Recommended Action</DialogTitle>
        <DialogContent>
          <Box mt={1} display="flex" flexDirection="column" gap={2}>
            <TextField
              label="Title"
              value={newAction.title}
              onChange={(e) => setNewAction({ ...newAction, title: e.target.value })}
              fullWidth
            />
            <TextField
              label="Description"
              value={newAction.description}
              onChange={(e) => setNewAction({ ...newAction, description: e.target.value })}
              fullWidth
              multiline
              minRows={3}
            />
            <Box display="flex" gap={2}>
              <FormControl fullWidth>
                <InputLabel>Action Type</InputLabel>
                <Select
                  label="Action Type"
                  value={newAction.action_type}
                  onChange={(e) => setNewAction({ ...newAction, action_type: e.target.value as string })}
                >
                  <MenuItem value="configuration_change">Configuration Change</MenuItem>
                  <MenuItem value="query_optimization">Query Optimization</MenuItem>
                  <MenuItem value="index_creation">Index Creation</MenuItem>
                  <MenuItem value="hardware_upgrade">Hardware Upgrade</MenuItem>
                  <MenuItem value="monitoring_setup">Monitoring Setup</MenuItem>
                  <MenuItem value="backup_strategy">Backup Strategy</MenuItem>
                  <MenuItem value="security_hardening">Security Hardening</MenuItem>
                </Select>
              </FormControl>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  label="Priority"
                  value={newAction.priority}
                  onChange={(e) => setNewAction({ ...newAction, priority: e.target.value as string })}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="urgent">Urgent</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box display="flex" gap={2}>
              <FormControl fullWidth>
                <InputLabel>Estimated Effort</InputLabel>
                <Select
                  label="Estimated Effort"
                  value={newAction.estimated_effort}
                  onChange={(e) => setNewAction({ ...newAction, estimated_effort: e.target.value as string })}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                </Select>
              </FormControl>
              <TextField
                label="Due Date"
                type="date"
                value={newAction.due_date}
                onChange={(e) => setNewAction({ ...newAction, due_date: e.target.value })}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => createActionMutation.mutate()}
            disabled={!newAction.title.trim() || !newAction.description.trim() || createActionMutation.isPending}
          >
            Add Action
          </Button>
        </DialogActions>
      </Dialog>

      {/* Similar Reports Dialog */}
      <Dialog
        open={similarReportsOpen}
        onClose={() => setSimilarReportsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Similar Reports</DialogTitle>
        <DialogContent>
          {similarReportsLoading ? (
            <Box display="flex" justifyContent="center" alignItems="center" p={3}>
              <Typography>Loading similar reports...</Typography>
            </Box>
          ) : similarReports?.similar_reports?.length > 0 ? (
            <>
              <Alert severity="info" sx={{ mb: 2 }}>
                Viewing as <strong>{selectedUser}</strong> • 
                Showing {similarReports.count} result{similarReports.count !== 1 ? 's' : ''}
              </Alert>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Similar to "{similarReports.source_report_title}"
              </Typography>
              <List>
                {similarReports.similar_reports.map((similar: any) => (
                  <ListItem
                    key={similar.id}
                    disablePadding
                    sx={{ mb: 1 }}
                  >
                    <ListItemButton
                      onClick={() => {
                        setSimilarReportsOpen(false);
                        navigate(`/reports/${similar.id}`);
                      }}
                      sx={{
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                      }}
                    >
                      <ListItemText
                        primary={
                          <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Typography variant="subtitle1">{similar.title}</Typography>
                            <Chip
                              label={`${(similar.similarity_score * 100).toFixed(0)}% match`}
                              size="small"
                              color={similar.similarity_score > 0.7 ? 'success' : 'default'}
                            />
                          </Box>
                        }
                        secondary={
                          <>
                            Cluster: {similar.cluster_id} • Status: {similar.status} • Created: {new Date(similar.created_at).toLocaleDateString()}
                          </>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            </>
          ) : (
            <Box p={3} textAlign="center">
              <Alert severity="warning" sx={{ mb: 2 }}>
                Viewing as <strong>{selectedUser}</strong> • No similar reports found
              </Alert>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                • No similar reports exist for customers you have access to<br/>
                • Try switching users in the top navigation
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSimilarReportsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ReportDetail;
