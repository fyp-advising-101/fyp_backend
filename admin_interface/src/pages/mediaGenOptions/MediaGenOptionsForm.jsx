import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Typography, Button, Box, Paper, TextField, MenuItem,
  FormControl, InputLabel, Select, CircularProgress,
  Alert, FormHelperText, Grid, Divider, IconButton,
  Card, CardContent, CardHeader, Accordion, AccordionSummary,
  AccordionDetails, List, ListItem, ListItemText
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { mediaGenOptionsAPI, mediaCategoryOptionsAPI } from '../../api';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

function MediaGenOptionsForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditMode = Boolean(id);
  
  const [loading, setLoading] = useState(isEditMode);
  const [categoryOptionsLoading, setCategoryOptionsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [categoryOptions, setCategoryOptions] = useState([]);
  const [showCategoryOptions, setShowCategoryOptions] = useState(false);
  
  const { control, handleSubmit, reset, watch, formState: { errors } } = useForm({
    defaultValues: {
      category: '',
      media_type: 'image',
      description: ''
    }
  });

  // Fetch media gen option data if in edit mode
  useEffect(() => {
    const fetchMediaGenOption = async () => {
      try {
        setLoading(true);
        const response = await mediaGenOptionsAPI.getById(id);
        reset(response.data);
        
        // Also fetch category options if in edit mode
        await fetchCategoryOptions();
      } catch (err) {
        console.error("Error fetching media generation option:", err);
        setError("Failed to load media generation option data. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    const fetchCategoryOptions = async () => {
      try {
        setCategoryOptionsLoading(true);
        const response = await mediaGenOptionsAPI.getCategoryOptions(id);
        setCategoryOptions(response.data);
        setShowCategoryOptions(true);
      } catch (err) {
        console.error("Error fetching category options:", err);
      } finally {
        setCategoryOptionsLoading(false);
      }
    };

    if (isEditMode) {
      fetchMediaGenOption();
    }
  }, [id, isEditMode, reset]);

  const onSubmit = async (data) => {
    try {
      setLoading(true);
      
      let savedOptionId;
      
      if (isEditMode) {
        await mediaGenOptionsAPI.update(id, data);
        savedOptionId = id;
      } else {
        const response = await mediaGenOptionsAPI.create(data);
        savedOptionId = response.data.option_id;
      }
      
      // Redirect back to media gen options list or to category options
      if (isEditMode) {
        navigate('/media-gen-options');
      } else {
        navigate(`/media-category-options/create?optionId=${savedOptionId}`);
      }
      
    } catch (err) {
      console.error("Error saving media generation option:", err);
      setError("Failed to save media generation option. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Handle category option deletion
  const handleDeleteCategoryOption = async (optionId) => {
    try {
      setCategoryOptionsLoading(true);
      await mediaCategoryOptionsAPI.delete(optionId);
      
      // Refresh the list
      const response = await mediaGenOptionsAPI.getCategoryOptions(id);
      setCategoryOptions(response.data);
    } catch (err) {
      console.error("Error deleting category option:", err);
      setError("Failed to delete category option. Please try again.");
    } finally {
      setCategoryOptionsLoading(false);
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
        {isEditMode ? 'Edit Media Generation Option' : 'Create Media Generation Option'}
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Grid container spacing={3}>
        {/* Media Gen Options Form */}
        <Grid item xs={12} lg={isEditMode ? 6 : 12}>
          <Paper sx={{ p: 3 }}>
            <form onSubmit={handleSubmit(onSubmit)}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Controller
                    name="category"
                    control={control}
                    rules={{ required: 'Category is required' }}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        fullWidth
                        label="Category"
                        variant="outlined"
                        error={!!errors.category}
                        helperText={errors.category?.message || "Enter a unique category name (e.g., 'Campus Life', 'Academic Programs')"}
                      />
                    )}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Controller
                    name="media_type"
                    control={control}
                    rules={{ required: 'Media type is required' }}
                    render={({ field }) => (
                      <FormControl fullWidth error={!!errors.media_type}>
                        <InputLabel id="media-type-label">Media Type</InputLabel>
                        <Select
                          {...field}
                          labelId="media-type-label"
                          label="Media Type"
                        >
                          <MenuItem value="image">Image</MenuItem>
                          <MenuItem value="video">Video</MenuItem>
                          <MenuItem value="audio">Audio</MenuItem>
                        </Select>
                        {errors.media_type && (
                          <FormHelperText>{errors.media_type.message}</FormHelperText>
                        )}
                      </FormControl>
                    )}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <Controller
                    name="description"
                    control={control}
                    render={({ field }) => (
                      <TextField
                        {...field}
                        fullWidth
                        label="Description"
                        variant="outlined"
                        multiline
                        rows={3}
                        helperText="A detailed description of what kind of media will be generated"
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
                  {isEditMode ? 'Update' : 'Create & Add Category Options'}
                </Button>
                <Button
                  variant="outlined"
                  component={Link}
                  to="/media-gen-options"
                >
                  Cancel
                </Button>
              </Box>
            </form>
          </Paper>
        </Grid>

        {/* Category Options Section - Only shown in edit mode */}
        {isEditMode && (
          <Grid item xs={12} lg={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Category Options
                </Typography>
                <Button
                  variant="contained"
                  color="primary"
                  component={Link}
                  to={`/media-category-options/create?optionId=${id}`}
                  startIcon={<AddIcon />}
                  size="small"
                >
                  Add Category Option
                </Button>
              </Box>
              
              <Divider sx={{ mb: 2 }} />
              
              {categoryOptionsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
                  <CircularProgress size={24} />
                </Box>
              ) : categoryOptions.length === 0 ? (
                <Box sx={{ py: 2, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    No category options found. Please add at least one category option.
                  </Typography>
                </Box>
              ) : (
                <List sx={{ width: '100%' }}>
                  {categoryOptions.map((option) => (
                    <Accordion key={option.id} sx={{ mb: 1 }}>
                      <AccordionSummary
                        expandIcon={<ExpandMoreIcon />}
                        aria-controls={`panel-${option.id}-content`}
                        id={`panel-${option.id}-header`}
                      >
                        <Typography sx={{ width: '33%', flexShrink: 0 }}>
                          {option.title}
                        </Typography>
                        <Typography sx={{ color: 'text.secondary' }}>
                          Query: {option.chroma_query.substring(0, 30)}...
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Grid container spacing={2}>
                          <Grid item xs={12}>
                            <Typography variant="subtitle2">Chroma Query:</Typography>
                            <Typography variant="body2" paragraph>
                              {option.chroma_query}
                            </Typography>
                          </Grid>
                          <Grid item xs={12}>
                            <Typography variant="subtitle2">Prompt Text:</Typography>
                            <Typography variant="body2" paragraph>
                              {option.prompt_text}
                            </Typography>
                          </Grid>
                          <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                            <Button
                              component={Link}
                              to={`/media-category-options/edit/${option.id}`}
                              color="primary"
                              size="small"
                              sx={{ mr: 1 }}
                            >
                              Edit
                            </Button>
                            <Button
                              color="error"
                              size="small"
                              onClick={() => handleDeleteCategoryOption(option.id)}
                            >
                              Delete
                            </Button>
                          </Grid>
                        </Grid>
                      </AccordionDetails>
                    </Accordion>
                  ))}
                </List>
              )}
            </Paper>
          </Grid>
        )}
      </Grid>
      
      {/* Tips section */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Creating Effective Media Generation Options
        </Typography>
        
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Tips for Creating Media Generation Options</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              <strong>1. Choose a Descriptive Category Name:</strong> Use clear, concise names that reflect the content theme (e.g., "Campus Life", "Academic Programs").
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>2. Select the Appropriate Media Type:</strong> Choose "image" for static visual content, "video" for dynamic content, or "audio" for sound-based content.
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>3. Write a Detailed Description:</strong> Include information about the purpose and expected content for this category.
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>4. Add Multiple Category Options:</strong> After creating the main option, add multiple category options to provide variety in generated media.
            </Typography>
          </AccordionDetails>
        </Accordion>
        
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Category Options Explained</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" paragraph>
              <strong>Title:</strong> A short, descriptive name for the specific prompt variation.
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Chroma Query:</strong> The question used to search the vector database for relevant context. This should be specific and targeted.
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>Prompt Text:</strong> The actual instructions sent to the AI to generate media. You can include specific style preferences, themes, or elements to include.
            </Typography>
          </AccordionDetails>
        </Accordion>
      </Paper>
    </div>
  );
}

export default MediaGenOptionsForm;