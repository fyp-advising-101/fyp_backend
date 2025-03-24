import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Typography, Button, Paper, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Box, CircularProgress,
  Chip, IconButton, Dialog, DialogActions, DialogContent,
  DialogContentText, DialogTitle
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import { scrapeTargetsAPI } from '../../api';

function ScrapeTargetsList() {
  const [scrapeTargets, setScrapeTargets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [targetToDelete, setTargetToDelete] = useState(null);

  // Function to fetch scrape targets
  const fetchScrapeTargets = async () => {
    try {
      setLoading(true);
      const response = await scrapeTargetsAPI.getAll();
      setScrapeTargets(response.data);
      setError(null);
    } catch (err) {
      console.error("Error fetching scrape targets:", err);
      setError("Failed to load scrape targets. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Load scrape targets when component mounts
  useEffect(() => {
    fetchScrapeTargets();
  }, []);

  // Handle delete dialog
  const handleDeleteClick = (target) => {
    setTargetToDelete(target);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!targetToDelete) return;
    
    try {
      await scrapeTargetsAPI.delete(targetToDelete.id);
      setDeleteDialogOpen(false);
      setTargetToDelete(null);
      // Refresh scrape targets list
      fetchScrapeTargets();
    } catch (err) {
      console.error("Error deleting scrape target:", err);
      setError("Failed to delete scrape target. Please try again.");
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setTargetToDelete(null);
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
          Scrape Targets
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          component={Link} 
          to="/scrape-targets/create"
          startIcon={<AddIcon />}
        >
          Add Scrape Target
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>URL</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Frequency (days)</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {scrapeTargets.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No scrape targets found
                </TableCell>
              </TableRow>
            ) : (
              scrapeTargets.map((target) => (
                <TableRow key={target.id}>
                  <TableCell>{target.id}</TableCell>
                  <TableCell>{target.name}</TableCell>
                  <TableCell>
                    <a href={target.url} target="_blank" rel="noopener noreferrer">
                      {target.url}
                    </a>
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={target.type} 
                      color={
                        target.type === 'news' ? 'primary' : 
                        target.type === 'blog' ? 'success' : 'info'
                      } 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>{target.frequency}</TableCell>
                  <TableCell>
                    <IconButton 
                      component={Link} 
                      to={`/scrape-targets/edit/${target.id}`}
                      color="primary"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton 
                      color="error"
                      onClick={() => handleDeleteClick(target)}
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
            Are you sure you want to delete this scrape target? This action cannot be undone.
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

export default ScrapeTargetsList;