import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { 
  AppBar, Box, Toolbar, Typography, Drawer, List, ListItem, 
  ListItemIcon, ListItemText, IconButton, Divider, Container 
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import WorkIcon from '@mui/icons-material/Work';
import LanguageIcon from '@mui/icons-material/Language';
import ImageIcon from '@mui/icons-material/Image';
import CategoryIcon from '@mui/icons-material/Category';
import LibraryBooksIcon from '@mui/icons-material/LibraryBooks';
// Import pages
import JobsList from './pages/jobs/JobsList.jsx';
import JobsForm from './pages/jobs/JobsForm.jsx';
import ScrapeTargetsList from './pages/scrapeTargets/ScrapeTargetsList.jsx';
import ScrapeTargetsForm from './pages/scrapeTargets/ScrapeTargetsForms.jsx';
import MediaGenOptionsList from './pages/mediaGenOptions/MediaGenOptionsList.jsx';
import MediaGenOptionsForm from './pages/mediaGenOptions/MediaGenOptionsForm.jsx';
import MediaCategoryOptionsList from './pages/mediaCategoryOptions/MediaCategoryOptionsList.jsx';
import MediaCategoryOptionsForm from './pages/mediaCategoryOptions/MediaCategoryOptionsForm.jsx';
import MediaAssetsList from './pages/mediaAssets/MediaAssetsList.jsx';
import MediaAssetsForm from './pages/mediaAssets/MediaAssetsForm.jsx';
import Dashboard from './pages/Dashboard.jsx';

const drawerWidth = 240;

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap>
          Admin Dashboard
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        <ListItem button component={Link} to="/">
          <ListItemIcon><WorkIcon /></ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItem>
        <ListItem button component={Link} to="/jobs">
          <ListItemIcon><WorkIcon /></ListItemIcon>
          <ListItemText primary="Jobs" />
        </ListItem>
        <ListItem button component={Link} to="/scrape-targets">
          <ListItemIcon><LanguageIcon /></ListItemIcon>
          <ListItemText primary="Scrape Targets" />
        </ListItem>
        <ListItem button component={Link} to="/media-gen-options">
          <ListItemIcon><ImageIcon /></ListItemIcon>
          <ListItemText primary="Media Gen Options" />
        </ListItem>
        <ListItem button component={Link} to="/media-category-options">
          <ListItemIcon><CategoryIcon /></ListItemIcon>
          <ListItemText primary="Category Options" />
        </ListItem>
        <ListItem button component={Link} to="/media-assets">
          <ListItemIcon><LibraryBooksIcon /></ListItemIcon>
          <ListItemText primary="Media Assets" />
        </ListItem>
      </List>
    </div>
  );

  return (
    <ThemeProvider theme={theme}>
      <Router>
        <Box sx={{ display: 'flex' }}>
          <AppBar
            position="fixed"
            sx={{
              width: { sm: `calc(100% - ${drawerWidth}px)` },
              ml: { sm: `${drawerWidth}px` },
            }}
          >
            <Toolbar>
              <IconButton
                color="inherit"
                aria-label="open drawer"
                edge="start"
                onClick={handleDrawerToggle}
                sx={{ mr: 2, display: { sm: 'none' } }}
              >
                <MenuIcon />
              </IconButton>
              <Typography variant="h6" noWrap component="div">
                Content Management System
              </Typography>
            </Toolbar>
          </AppBar>
          <Box
            component="nav"
            sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
            aria-label="menu items"
          >
            {/* Mobile drawer */}
            <Drawer
              variant="temporary"
              open={mobileOpen}
              onClose={handleDrawerToggle}
              ModalProps={{ keepMounted: true }}
              sx={{
                display: { xs: 'block', sm: 'none' },
                '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
              }}
            >
              {drawer}
            </Drawer>
            
            {/* Desktop drawer */}
            <Drawer
              variant="permanent"
              sx={{
                display: { xs: 'none', sm: 'block' },
                '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
              }}
              open
            >
              {drawer}
            </Drawer>
          </Box>
          
          {/* Main content */}
          <Box
            component="main"
            sx={{ 
              flexGrow: 1, 
              p: 3, 
              width: { sm: `calc(100% - ${drawerWidth}px)` },
              mt: '64px' 
            }}
          >
            <Container maxWidth="lg">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                
                <Route path="/jobs" element={<JobsList />} />
                <Route path="/jobs/create" element={<JobsForm />} />
                <Route path="/jobs/edit/:id" element={<JobsForm />} />
                
                <Route path="/scrape-targets" element={<ScrapeTargetsList />} />
                <Route path="/scrape-targets/create" element={<ScrapeTargetsForm />} />
                <Route path="/scrape-targets/edit/:id" element={<ScrapeTargetsForm />} />
                
                <Route path="/media-gen-options" element={<MediaGenOptionsList />} />
                <Route path="/media-gen-options/create" element={<MediaGenOptionsForm />} />
                <Route path="/media-gen-options/edit/:id" element={<MediaGenOptionsForm />} />
                
                <Route path="/media-category-options" element={<MediaCategoryOptionsList />} />
                <Route path="/media-category-options/create" element={<MediaCategoryOptionsForm />} />
                <Route path="/media-category-options/edit/:id" element={<MediaCategoryOptionsForm />} />
                
                <Route path="/media-assets" element={<MediaAssetsList />} />
                <Route path="/media-assets/create" element={<MediaAssetsForm />} />
                <Route path="/media-assets/edit/:id" element={<MediaAssetsForm />} />
              </Routes>
            </Container>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;