import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Typography, Button, Box, Paper, TextField, MenuItem,
  FormControl, InputLabel, Select, CircularProgress,
  Alert, FormHelperText, Grid
} from '@mui/material';

import { LocalizationProvider, DateTimePicker } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useForm, Controller } from 'react-hook-form';
import { jobsAPI, mediaGenOptionsAPI, scrapeTargetsAPI, mediaAssetsAPI } from '../../api';

function JobsForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditMode = Boolean(id);
  
  const [loading, setLoading] = useState(isEditMode);
  const [error, setError] = useState(null);
  const [mediaGenOptions, setMediaGenOptions] = useState([]);
  const [scrapeTargets, setScrapeTargets] = useState([]);
  const [mediaAssets, setMediaAssets] = useState([]);
  const [taskIdType, setTaskIdType] = useState('string');
  
  const { control, handleSubmit, reset, watch, setValue, formState: { errors } } = useForm({
    defaultValues: {
      task_name: '',
      task_id: '',
      scheduled_date: new Date(),
      status: 0,
      error_message: ''
    }
  });

  // Watch the task name to dynamically change the task_id field
  const taskName = watch('task_name');

  useEffect(() => {
    // Reset task_id when task_name changes
    setValue('task_id', '');
    
    // Set task ID type based on task name
    if (taskName === 'create media') {
      setTaskIdType('mediaGenOption');
    } else if (taskName === 'web scrape' || taskName === 'insta scrape') {
      setTaskIdType('scrapeTarget');
    } else if (taskName.includes('post image') || taskName.includes('post video')) {
      setTaskIdType('mediaAsset');
    } else {
      setTaskIdType('string');
    }
  }, [taskName, setValue]);

  // Fetch dependent data
  useEffect(() => {
    const fetchMediaGenOptions = async () => {
      try {
        const response = await mediaGenOptionsAPI.getAll();
        setMediaGenOptions(response.data);
      } catch (err) {
        console.error("Error fetching media generation options:", err);
      }
    };

    const fetchScrapeTargets = async () => {
      try {
        const response = await scrapeTargetsAPI.getAll();
        setScrapeTargets(response.data);
      } catch (err) {
        console.error("Error fetching scrape targets:", err);
      }
    };

    const fetchMediaAssets = async () => {
      try {
        const response = await mediaAssetsAPI.getAll();
        setMediaAssets(response.data);
      } catch (err) {
        console.error("Error fetching media assets:", err);
      }
    };

    // Load dependent data
    fetchMediaGenOptions();
    fetchScrapeTargets();
    fetchMediaAssets();
  }, []);

  // Fetch job data if in edit mode
  useEffect(() => {
    const fetchJob = async () => {
      try {
        const response = await jobsAPI.getById(id);
        const job = response.data;
        
        // Convert string date to Date object
        job.scheduled_date = new Date(job.scheduled_date);
        
        // Set task ID type based on task name
        if (job.task_name === 'create media') {
          setTaskIdType('mediaGenOption');
        } else if (job.task_name === 'web scrape' || job.task_name === 'insta scrape') {
          setTaskIdType('scrapeTarget');
        } else if (job.task_name.includes('post image') || job.task_name.includes('post video')) {
          setTaskIdType('mediaAsset');
        } else {
          setTaskIdType('string');
        }
        
        // Reset form with job data
        reset(job);
      } catch (err) {
        console.error("Error fetching job:", err);
        setError("Failed to load job data. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    if (isEditMode) {
      fetchJob();
    } else {
      setLoading(false);
    }
  }, [id, isEditMode, reset]);

  const onSubmit = async (data) => {
    try {
      setLoading(true);
      
      // Format the date to match the API's expected format
      // Your API expects the format "YYYY-MM-DD HH:MM:SS"
      const formattedDate = data.scheduled_date.toISOString().replace('T', ' ').substring(0, 19);
      const formData = {
        ...data,
        scheduled_date: formattedDate
      };
      
      if (isEditMode) {
        await jobsAPI.update(id, formData);
      } else {
        await jobsAPI.create(formData);
      }
      
      // Redirect back to jobs list
      navigate('/jobs');
      
    } catch (err) {
      console.error("Error saving job:", err);
      setError("Failed to save job. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        {isEditMode ? 'Edit Job' : 'Create Job'}
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Controller
                name="task_name"
                control={control}
                rules={{ required: 'Task name is required' }}
                render={({ field }) => (
                  <FormControl fullWidth error={!!errors.task_name}>
                    <InputLabel id="task-name-label">Task Name</InputLabel>
                    <Select
                      {...field}
                      labelId="task-name-label"
                      label="Task Name"
                    >
                      <MenuItem value="web scrape">Web Scrape</MenuItem>
                      <MenuItem value="insta scrape">Instagram Scrape</MenuItem>
                      <MenuItem value="create media">Create Media</MenuItem>
                      <MenuItem value="post image whatsapp">Post Image to WhatsApp</MenuItem>
                      <MenuItem value="post image instagram">Post Image to Instagram</MenuItem>
                      <MenuItem value="post video whatsapp">Post Video to WhatsApp</MenuItem>
                      <MenuItem value="post video instagram">Post Video to Instagram</MenuItem>
                    </Select>
                    {errors.task_name && (
                      <FormHelperText>{errors.task_name.message}</FormHelperText>
                    )}
                  </FormControl>
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="task_id"
                control={control}
                rules={{ required: 'Task ID is required' }}
                render={({ field }) => {
                  // For media gen options
                  if (taskIdType === 'mediaGenOption') {
                    return (
                      <FormControl fullWidth error={!!errors.task_id}>
                        <InputLabel id="task-id-label">Media Generation Option</InputLabel>
                        <Select
                          {...field}
                          labelId="task-id-label"
                          label="Media Generation Option"
                        >
                          {mediaGenOptions.map(option => (
                            <MenuItem key={option.id} value={option.id.toString()}>
                              {option.category} ({option.media_type})
                            </MenuItem>
                          ))}
                        </Select>
                        {errors.task_id && (
                          <FormHelperText>{errors.task_id.message}</FormHelperText>
                        )}
                      </FormControl>
                    );
                  }
                  
                  // For scrape targets
                  if (taskIdType === 'scrapeTarget') {
                    return (
                      <FormControl fullWidth error={!!errors.task_id}>
                        <InputLabel id="task-id-label">Scrape Target</InputLabel>
                        <Select
                          {...field}
                          labelId="task-id-label"
                          label="Scrape Target"
                        >
                          {scrapeTargets.map(target => (
                            <MenuItem key={target.id} value={target.id.toString()}>
                              {target.name} ({target.url})
                            </MenuItem>
                          ))}
                        </Select>
                        {errors.task_id && (
                          <FormHelperText>{errors.task_id.message}</FormHelperText>
                        )}
                      </FormControl>
                    );
                  }
                  
                  // For media assets
                  if (taskIdType === 'mediaAsset') {
                    return (
                      <FormControl fullWidth error={!!errors.task_id}>
                        <InputLabel id="task-id-label">Media Asset</InputLabel>
                        <Select
                          {...field}
                          labelId="task-id-label"
                          label="Media Asset"
                        >
                          {mediaAssets.map(asset => (
                            <MenuItem key={asset.id} value={asset.id.toString()}>
                              ID: {asset.id} - {asset.media_type} - {asset.caption ? asset.caption.substring(0, 30) + '...' : 'No caption'}
                            </MenuItem>
                          ))}
                        </Select>
                        {errors.task_id && (
                          <FormHelperText>{errors.task_id.message}</FormHelperText>
                        )}
                      </FormControl>
                    );
                  }
                  
                  // Default string input
                  return (
                    <TextField
                      {...field}
                      fullWidth
                      label="Task ID"
                      variant="outlined"
                      error={!!errors.task_id}
                      helperText={errors.task_id?.message || "ID of the task to perform"}
                    />
                  );
                }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="scheduled_date"
                control={control}
                rules={{ required: 'Scheduled date is required' }}
                render={({ field }) => (
                  <LocalizationProvider dateAdapter={AdapterDateFns}>
                    <DateTimePicker
                      {...field}
                      label="Scheduled Date"
                      renderInput={(params) => (
                        <TextField
                          {...params}
                          fullWidth
                          error={!!errors.scheduled_date}
                          helperText={errors.scheduled_date?.message}
                        />
                      )}
                    />
                  </LocalizationProvider>
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Controller
                name="status"
                control={control}
                render={({ field }) => (
                  <FormControl fullWidth>
                    <InputLabel id="status-label">Status</InputLabel>
                    <Select
                      {...field}
                      labelId="status-label"
                      label="Status"
                    >
                      <MenuItem value={0}>Pending</MenuItem>
                      <MenuItem value={1}>Processing</MenuItem>
                      <MenuItem value={2}>Completed</MenuItem>
                      <MenuItem value={-1}>Failed</MenuItem>
                    </Select>
                  </FormControl>
                )}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Controller
                name="error_message"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Error Message"
                    variant="outlined"
                    multiline
                    rows={2}
                  />
                )}
              />
            </Grid>
          </Grid>
          
          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={loading}
            >
              {isEditMode ? 'Update' : 'Create'}
            </Button>
            <Button
              variant="outlined"
              component={Link}
              to="/jobs"
            >
              Cancel
            </Button>
          </Box>
        </form>
      </Paper>
      
      {/* Help section */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Job Types Help
        </Typography>
        <Typography variant="body2" paragraph>
          <strong>Web Scrape</strong>: Scrapes content from a website. Select a scrape target from the list.
        </Typography>
        <Typography variant="body2" paragraph>
          <strong>Instagram Scrape</strong>: Scrapes content from Instagram. Select a scrape target from the list.
        </Typography>
        <Typography variant="body2" paragraph>
          <strong>Create Media</strong>: Generates new media (images or videos). Select a media generation option from the list.
        </Typography>
        <Typography variant="body2" paragraph>
          <strong>Post Image to WhatsApp/Instagram</strong>: Posts an existing image to social media. Select a media asset from the list.
        </Typography>
        <Typography variant="body2" paragraph>
          <strong>Post Video to WhatsApp/Instagram</strong>: Posts an existing video to social media. Select a media asset from the list.
        </Typography>
      </Paper>
    </div>
  );
}

export default JobsForm;