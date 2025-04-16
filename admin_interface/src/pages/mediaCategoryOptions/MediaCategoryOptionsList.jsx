import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Typography, Button, Paper, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Box, CircularProgress,
  IconButton, Dialog, DialogActions, DialogContent,
  DialogContentText, DialogTitle, Chip
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { mediaCategoryOptionsAPI, mediaGenOptionsAPI } from '../../api';

function MediaCategoryOptionsList() {
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const optionId = searchParams.get('optionId');
  
  const [categoryOptions, setCategoryOptions] = useState([]);
  const [parentOption, setParentOption] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [optionToDelete, setOptionToDelete] = useState(null);

  // Function to fetch category options
  const fetchCategoryOptions = async () => {
    try {
      setLoading(true);
      let response;
      
      // If optionId is provided, fetch only that option's category options
      if (optionId) {
        response = await mediaGenOptionsAPI.getCategoryOptions(optionId);
        
        // Also fetch the parent option details
        const parentResponse = await mediaGenOptionsAPI.getById(optionId);
        setParentOption(parentResponse.data);
      } else {
        response = await mediaCategoryOptionsAPI.getAll();
      }
      
      setCategoryOptions(response.data);
      setError(null);
    } catch (err) {
      console.error("Error fetching media category options:", err);
      setError("Failed to load media category options. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Load category options when component mounts
  useEffect(() => {
    fetchCategoryOptions();
  }, [optionId]);

  // Handle delete dialog
  const handleDeleteClick = (option) => {
    setOptionToDelete(option);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!optionToDelete) return;
    
    try {
      await mediaCategoryOptionsAPI.delete(optionToDelete.id);
      setDeleteDialogOpen(false);
      setOptionToDelete(null);
      // Refresh category options list
      fetchCategoryOptions();
    } catch (err) {
      console.error("Error deleting media category option:", err);
      setError("Failed to delete media category option. Please try again.");
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setOptionToDelete(null);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mt: 2 }}>
        <Paper sx={{ p: 2, backgroundColor: '#ffcdd2' }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      </Box>
    );
  }

  return (
    <div>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {optionId && (
            <IconButton 
              component={Link} 
              to="/media-gen-options"
              sx={{ mr: 1 }}
            >
              <ArrowBackIcon />
            </IconButton>
          )}
          <Typography variant="h4" gutterBottom>
            {optionId && parentOption 
              ? `Category Options for ${parentOption.category}` 
              : 'All Media Category Options'}
          </Typography>
        </Box>
        <Button 
          variant="contained" 
          color="primary" 
          component={Link} 
          to={optionId 
            ? `/media-category-options/create?optionId=${optionId}` 
            : '/media-category-options/create'}
          startIcon={<AddIcon />}
        >
          Add Category Option
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Prompt Text</TableCell>
              <TableCell>Chroma Query</TableCell>
              <TableCell>Parent Option ID</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {categoryOptions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No media category options found
                </TableCell>
              </TableRow>
            ) : (
              categoryOptions.slice().reverse().map((option) => (
                <TableRow key={option.id}>
                  <TableCell>{option.id}</TableCell>
                  <TableCell>{option.title}</TableCell>
                  <TableCell>{option.prompt_text.substring(0, 50)}...</TableCell>
                  <TableCell>{option.chroma_query.substring(0, 50)}...</TableCell>
                  <TableCell>
                    <Chip 
                      label={option.option_id} 
                      color="primary" 
                      size="small" 
                      component={Link}
                      to={`/media-gen-options/edit/${option.option_id}`}
                      clickable
                    />
                  </TableCell>
                  <TableCell>
                    <IconButton 
                      component={Link} 
                      to={`/media-category-options/edit/${option.id}`}
                      color="primary"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton 
                      color="error"
                      onClick={() => handleDeleteClick(option)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this media category option? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel} color="primary">
            Cancel
          </Button>
          <Button onClick={handleDeleteConfirm} color="error">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default MediaCategoryOptionsList;