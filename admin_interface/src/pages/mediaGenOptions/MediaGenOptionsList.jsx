import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Typography, Button, Paper, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Box, CircularProgress,
  Chip, IconButton, Dialog, DialogActions, DialogContent,
  DialogContentText, DialogTitle, Tooltip
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import CategoryIcon from '@mui/icons-material/Category';
import { mediaGenOptionsAPI } from '../../api';

function MediaGenOptionsList() {
  const [mediaGenOptions, setMediaGenOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [optionToDelete, setOptionToDelete] = useState(null);

  // Function to fetch media gen options
  const fetchMediaGenOptions = async () => {
    try {
      setLoading(true);
      const response = await mediaGenOptionsAPI.getAll();
      setMediaGenOptions(response.data);
      setError(null);
    } catch (err) {
      console.error("Error fetching media generation options:", err);
      setError("Failed to load media generation options. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Load media gen options when component mounts
  useEffect(() => {
    fetchMediaGenOptions();
  }, []);

  // Handle delete dialog
  const handleDeleteClick = (option) => {
    setOptionToDelete(option);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!optionToDelete) return;
    
    try {
      await mediaGenOptionsAPI.delete(optionToDelete.id);
      setDeleteDialogOpen(false);
      setOptionToDelete(null);
      // Refresh media gen options list
      fetchMediaGenOptions();
    } catch (err) {
      console.error("Error deleting media generation option:", err);
      setError("Failed to delete media generation option. Please try again.");
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
        <Typography variant="h4" gutterBottom>
          Media Generation Options
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          component={Link} 
          to="/media-gen-options/create"
          startIcon={<AddIcon />}
        >
          Add Media Generation Option
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Media Type</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Category Options</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {mediaGenOptions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No media generation options found
                </TableCell>
              </TableRow>
            ) : (
              mediaGenOptions.map((option) => (
                <TableRow key={option.id}>
                  <TableCell>{option.id}</TableCell>
                  <TableCell>{option.category}</TableCell>
                  <TableCell>
                    <Chip 
                      label={option.media_type} 
                      color={option.media_type === 'image' ? 'success' : 'info'} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>{option.description || 'N/A'}</TableCell>
                  <TableCell>
                    <Tooltip title="View Category Options">
                      <IconButton 
                        color="primary" 
                        component={Link} 
                        to={`/media-category-options?optionId=${option.id}`}
                      >
                        <CategoryIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <IconButton 
                      component={Link} 
                      to={`/media-gen-options/edit/${option.id}`}
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
            Are you sure you want to delete this media generation option? This will also delete all associated category options.
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

export default MediaGenOptionsList;