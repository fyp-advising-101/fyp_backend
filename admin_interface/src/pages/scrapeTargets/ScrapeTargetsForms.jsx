import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Typography, Button, Box, Paper, TextField, MenuItem,
  FormControl, InputLabel, Select, CircularProgress,
  Alert, FormHelperText
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { scrapeTargetsAPI } from '../../api';

function ScrapeTargetsForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditMode = Boolean(id);
  
  const [loading, setLoading] = useState(isEditMode);
  const [error, setError] = useState(null);
  
  const { control, handleSubmit, reset, formState: { errors } } = useForm({
    defaultValues: {
      name: '',
      url: '',
      type: 'news',
      frequency: 1
    }
  });

  // Fetch scrape target data if in edit mode
  useEffect(() => {
    const fetchScrapeTarget = async () => {
      try {
        const response = await scrapeTargetsAPI.getById(id);
        reset(response.data);
      } catch (err) {
        console.error("Error fetching scrape target:", err);
        setError("Failed to load scrape target data. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    if (isEditMode) {
      fetchScrapeTarget();
    }
  }, [id, isEditMode, reset]);

  const onSubmit = async (data) => {
    try {
      setLoading(true);
      
      if (isEditMode) {
        await scrapeTargetsAPI.update(id, data);
      } else {
        await scrapeTargetsAPI.create(data);
      }
      
      // Redirect back to scrape targets list
      navigate('/scrape-targets');
      
    } catch (err) {
      console.error("Error saving scrape target:", err);
      setError("Failed to save scrape target. Please try again.");
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
        {isEditMode ? 'Edit Scrape Target' : 'Add Scrape Target'}
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Box sx={{ mb: 2 }}>
            <Controller
              name="name"
              control={control}
              rules={{ required: 'Name is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Name"
                  variant="outlined"
                  error={!!errors.name}
                  helperText={errors.name?.message}
                />
              )}
            />
          </Box>
          
          <Box sx={{ mb: 2 }}>
            <Controller
              name="url"
              control={control}
              rules={{ 
                required: 'URL is required',
                pattern: {
                  value: /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([\/\w .-]*)*\/?$/,
                  message: 'Please enter a valid URL'
                }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="URL"
                  variant="outlined"
                  error={!!errors.url}
                  helperText={errors.url?.message}
                />
              )}
            />
          </Box>
          
          <Box sx={{ mb: 2 }}>
            <Controller
              name="type"
              control={control}
              rules={{ required: 'Type is required' }}
              render={({ field }) => (
                <FormControl fullWidth error={!!errors.type}>
                  <InputLabel id="type-label">Type</InputLabel>
                  <Select
                    {...field}
                    labelId="type-label"
                    label="Type"
                  >
                    <MenuItem value="news">News</MenuItem>
                    <MenuItem value="blog">Blog</MenuItem>
                    <MenuItem value="social">Social Media</MenuItem>
                  </Select>
                  {errors.type && (
                    <FormHelperText>{errors.type.message}</FormHelperText>
                  )}
                </FormControl>
              )}
            />
          </Box>
          
          <Box sx={{ mb: 2 }}>
            <Controller
              name="frequency"
              control={control}
              rules={{ 
                required: 'Frequency is required',
                min: {
                  value: 0.1,
                  message: 'Frequency must be positive'
                }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Frequency (days)"
                  variant="outlined"
                  type="number"
                  inputProps={{ step: 0.1 }}
                  error={!!errors.frequency}
                  helperText={errors.frequency?.message || "How often to scrape (in days)"}
                />
              )}
            />
          </Box>
          
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
              to="/scrape-targets"
            >
              Cancel
            </Button>
          </Box>
        </form>
      </Paper>
    </div>
  );
}

export default ScrapeTargetsForm;