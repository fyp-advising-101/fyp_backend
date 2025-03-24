import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Typography, Button, Paper, Table, TableBody, TableCell, 
  TableContainer, TableHead, TableRow, Box, CircularProgress,
  Chip, IconButton, Dialog, DialogActions, DialogContent,
  DialogContentText, DialogTitle, Card, CardMedia, CardContent
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';
import ImageIcon from '@mui/icons-material/Image';
import MovieIcon from '@mui/icons-material/Movie';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { mediaAssetsAPI } from '../../api';

function MediaAssetsList() {
  const [mediaAssets, setMediaAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [assetToDelete, setAssetToDelete] = useState(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [previewAsset, setPreviewAsset] = useState(null);

  // Function to fetch media assets
  const fetchMediaAssets = async () => {
    try {
      setLoading(true);
      const response = await mediaAssetsAPI.getAll();
      setMediaAssets(response.data);
      setError(null);
    } catch (err) {
      console.error("Error fetching media assets:", err);
      setError("Failed to load media assets. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Load media assets when component mounts
  useEffect(() => {
    fetchMediaAssets();
  }, []);

  // Handle delete dialog
  const handleDeleteClick = (asset) => {
    setAssetToDelete(asset);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!assetToDelete) return;
    
    try {
      await mediaAssetsAPI.delete(assetToDelete.id);
      setDeleteDialogOpen(false);
      setAssetToDelete(null);
      // Refresh media assets list
      fetchMediaAssets();
    } catch (err) {
      console.error("Error deleting media asset:", err);
      setError("Failed to delete media asset. Please try again.");
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setAssetToDelete(null);
  };

  // Handle preview dialog
  const handlePreviewClick = (asset) => {
    setPreviewAsset(asset);
    setPreviewDialogOpen(true);
  };

  const handlePreviewClose = () => {
    setPreviewDialogOpen(false);
    setPreviewAsset(null);
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
          Media Assets
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          component={Link} 
          to="/media-assets/create"
          startIcon={<AddIcon />}
        >
          Add Media Asset
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Media Type</TableCell>
              <TableCell>Caption</TableCell>
              <TableCell>Preview</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {mediaAssets.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No media assets found
                </TableCell>
              </TableRow>
            ) : (
              mediaAssets.map((asset) => (
                <TableRow key={asset.id}>
                  <TableCell>{asset.id}</TableCell>
                  <TableCell>
                    <Chip 
                      icon={asset.media_type === 'image' ? <ImageIcon /> : <MovieIcon />}
                      label={asset.media_type} 
                      color={asset.media_type === 'image' ? 'success' : 'info'} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>
                    {asset.caption ? asset.caption.substring(0, 50) + '...' : 'No caption'}
                  </TableCell>
                  <TableCell>
                    <Button 
                      size="small" 
                      onClick={() => handlePreviewClick(asset)}
                    >
                      Preview
                    </Button>
                    <IconButton 
                      href={asset.media_blob_url} 
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <OpenInNewIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                  <TableCell>
                    <IconButton 
                      component={Link} 
                      to={`/media-assets/edit/${asset.id}`}
                      color="primary"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton 
                      color="error"
                      onClick={() => handleDeleteClick(asset)}
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
            Are you sure you want to delete this media asset? This action cannot be undone.
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

      {/* Preview Dialog */}
      <Dialog
        open={previewDialogOpen}
        onClose={handlePreviewClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Media Preview</DialogTitle>
        <DialogContent>
          {previewAsset && (
            <Card>
              {previewAsset.media_type === 'image' ? (
                <CardMedia
                  component="img"
                  image={previewAsset.media_blob_url}
                  alt="Media preview"
                  sx={{ maxHeight: '400px', objectFit: 'contain' }}
                />
              ) : previewAsset.media_type === 'video' ? (
                <CardMedia
                  component="video"
                  src={previewAsset.media_blob_url}
                  controls
                  sx={{ maxHeight: '400px' }}
                />
              ) : (
                <Box sx={{ p: 2, textAlign: 'center' }}>
                  <Typography>
                    Preview not available for this media type.
                  </Typography>
                  <Button 
                    href={previewAsset.media_blob_url} 
                    target="_blank"
                    rel="noopener noreferrer"
                    startIcon={<OpenInNewIcon />}
                  >
                    Open in new tab
                  </Button>
                </Box>
              )}
              <CardContent>
                <Typography gutterBottom variant="h6">
                  Caption:
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {previewAsset.caption || 'No caption available'}
                </Typography>
              </CardContent>
            </Card>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handlePreviewClose}>Close</Button>
          {previewAsset && (
            <Button 
              href={previewAsset.media_blob_url} 
              target="_blank"
              rel="noopener noreferrer"
              startIcon={<OpenInNewIcon />}
            >
              Open in new tab
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </div>
  );
}

export default MediaAssetsList;