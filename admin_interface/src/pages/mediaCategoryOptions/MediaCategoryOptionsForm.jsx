import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom';
import { 
  Typography, Button, Box, Paper, TextField, MenuItem,
  FormControl, InputLabel, Select, CircularProgress,
  Alert, FormHelperText
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { mediaCategoryOptionsAPI, mediaGenOptionsAPI } from '../../api';

function MediaCategoryOptionsForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const defaultOptionId = searchParams.get('optionId');
  
  const isEditMode = Boolean(id);
  
  const [loading, setLoading] = useState(isEditMode);
  const [error, setError] = useState(null);
  const [mediaGenOptions, setMediaGenOptions] = useState([]);
  
  const { control, handleSubmit, reset, formState: { errors } } = useForm({
    defaultValues: {
      title: '',
      prompt_text: '',
      chroma_query: '',
      option_id: defaultOptionId || ''
    }
  });

  // Fetch data when component mounts
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch all media gen options for the dropdown
        const optionsResponse = await mediaGenOptionsAPI.getAll();
        setMediaGenOptions(optionsResponse.data);
        
        // If in edit mode, fetch the current category option
        if (isEditMode) {
          const response = await mediaCategoryOptionsAPI.getById(id);
          reset(response.data);
        }
        
      } catch (err) {
        console.error("Error fetching data:", err);
        setError("Failed to load data. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, isEditMode, reset]);

  const onSubmit = async (data) => {
    try {
      setLoading(true);
      
      if (isEditMode) {
        await mediaCategoryOptionsAPI.update(id, data);
      } else {
        await mediaCategoryOptionsAPI.create(data);
      }
      
      // Redirect back to media category options list
      // If we came from a specific parent option, go back to that view
      if (defaultOptionId) {
        navigate(`/media-category-options?optionId=${defaultOptionId}`);
      } else {
        navigate('/media-category-options');
      }
      
    } catch (err) {
      console.error("Error saving media category option:", err);
      setError("Failed to save media category option. Please try again.");
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
        {isEditMode ? 'Edit Media Category Option' : 'Add Media Category Option'}
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
              name="title"
              control={control}
              rules={{ required: 'Title is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Title"
                  variant="outlined"
                  error={!!errors.title}
                  helperText={errors.title?.message}
                />
              )}
            />
          </Box>
          
          <Box sx={{ mb: 2 }}>
            <Controller
              name="prompt_text"
              control={control}
              rules={{ required: 'Prompt text is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Prompt Text"
                  variant="outlined"
                  multiline
                  rows={4}
                  error={!!errors.prompt_text}
                  helperText={errors.prompt_text?.message || "Text used to generate media with AI"}
                />
              )}
            />
          </Box>
          
          <Box sx={{ mb: 2 }}>
            <Controller
              name="chroma_query"
              control={control}
              rules={{ required: 'Chroma query is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Chroma Query"
                  variant="outlined"
                  multiline
                  rows={4}
                  error={!!errors.chroma_query}
                  helperText={errors.chroma_query?.message || "Query to retrieve relevant context from the vector database"}
                />
              )}
            />
          </Box>
          
          <Box sx={{ mb: 2 }}>
            <Controller
              name="option_id"
              control={control}
              rules={{ required: 'Parent option is required' }}
              render={({ field }) => (
                <FormControl fullWidth error={!!errors.option_id}>
                  <InputLabel id="option-id-label">Parent Media Gen Option</InputLabel>
                  <Select
                    {...field}
                    labelId="option-id-label"
                    label="Parent Media Gen Option"
                  >
                    {mediaGenOptions.map(option => (
                      <MenuItem key={option.id} value={option.id}>
                        {option.category} ({option.media_type})
                      </MenuItem>
                    ))}
                  </Select>
                  {errors.option_id && (
                    <FormHelperText>{errors.option_id.message}</FormHelperText>
                  )}
                </FormControl>
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
              to={defaultOptionId 
                ? `/media-category-options?optionId=${defaultOptionId}` 
                : '/media-category-options'}
            >
              Cancel
            </Button>
          </Box>
        </form>
      </Paper>
    </div>
  );
}

export default MediaCategoryOptionsForm;