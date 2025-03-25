import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Typography, Button, Box, Paper, TextField, MenuItem,
  FormControl, InputLabel, Select, CircularProgress,
  Alert, FormHelperText, Card, CardMedia
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import { mediaAssetsAPI } from '../../api';

function MediaAssetsForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditMode = Boolean(id);
  
  const [loading, setLoading] = useState(isEditMode);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);
  
  const { control, handleSubmit, reset, watch, formState: { errors } } = useForm({
    defaultValues: {
      media_blob_url: '',
      caption: '',
      media_type: 'image'
    }
  });

  // Watch the media URL for preview
  const mediaUrl = watch('media_blob_url');
  const mediaType = watch('media_type');

  // Update preview when URL changes
  useEffect(() => {
    if (mediaUrl) {
      setPreview(mediaUrl);
    }
  }, [mediaUrl]);

  // Fetch media asset data if in edit mode
  useEffect(() => {
    const fetchMediaAsset = async () => {
      try {
        const response = await mediaAssetsAPI.getById(id);
        const asset = response.data;
        reset(asset);
        setPreview(asset.media_blob_url);
      } catch (err) {
        console.error("Error fetching media asset:", err);
        setError("Failed to load media asset data. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    if (isEditMode) {
      fetchMediaAsset();
    } else {
      setLoading(false);
    }
  }, [id, isEditMode, reset]);

  const onSubmit = async (data) => {
    try {
      setLoading(true);
      
      if (isEditMode) {
        await mediaAssetsAPI.update(id, data);
      } else {
        await mediaAssetsAPI.create(data);
      }
      
      // Redirect back to media assets list
      navigate('/media-assets');
      
    } catch (err) {
      console.error("Error saving media asset:", err);
      setError("Failed to save media asset. Please try again.");
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
        {isEditMode ? 'Edit Media Asset' : 'Add Media Asset'}
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
              name="media_blob_url"
              control={control}
              rules={{ 
                required: 'Media URL is required',
                pattern: {
                  value: /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([\/\w .-]*)*\/?$/,
                  message: 'Please enter a valid URL'
                }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Media URL"
                  variant="outlined"
                  error={!!errors.media_blob_url}
                  helperText={errors.media_blob_url?.message || "URL to the media file in Azure Blob Storage"}
                />
              )}
            />
          </Box>
          
          <Box sx={{ mb: 2 }}>
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
          </Box>
          
          <Box sx={{ mb: 2 }}>
            <Controller
              name="caption"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Caption"
                  variant="outlined"
                  multiline
                  rows={4}
                  helperText="Caption for the media asset"
                />
              )}
            />
          </Box>
          
          {/* Media Preview */}
          {preview && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Preview
              </Typography>
              <Card>
                {mediaType === 'image' ? (
                  <CardMedia
                    component="img"
                    image={preview}
                    alt="Media preview"
                    sx={{ height: 240, objectFit: 'contain' }}
                  />
                ) : mediaType === 'video' ? (
                  <CardMedia
                    component="video"
                    src={preview}
                    controls
                    sx={{ height: 240 }}
                  />
                ) : (
                  <Box sx={{ p: 2, textAlign: 'center' }}>
                    <Typography>
                      Preview not available for this media type.
                    </Typography>
                    <Button 
                      href={preview} 
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Open in new tab
                    </Button>
                  </Box>
                )}
              </Card>
            </Box>
          )}
          
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
              to="/media-assets"
            >
              Cancel
            </Button>
          </Box>
        </form>
      </Paper>
    </div>
  );
}

export default MediaAssetsForm;