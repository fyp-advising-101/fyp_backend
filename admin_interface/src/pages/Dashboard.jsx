import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Typography, Grid, Card, CardContent, CardActions, 
  Button, Paper, Box, CircularProgress 
} from '@mui/material';

import { jobsAPI, scrapeTargetsAPI, mediaGenOptionsAPI } from '../api';

function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    jobs: { total: 0, pending: 0, processing: 0, completed: 0, failed: 0 },
    scrapeTargets: { total: 0 },
    mediaGenOptions: { total: 0 }
  });

  useEffect(() => {
    async function fetchStats() {
      try {
        setLoading(true);
        
        // Fetch jobs
        const jobsResponse = await jobsAPI.getAll();
        const jobs = jobsResponse.data;
        
        const jobStats = {
          total: jobs.length,
          pending: jobs.filter(job => job.status === 0).length,
          processing: jobs.filter(job => job.status === 1).length,
          completed: jobs.filter(job => job.status === 2).length,
          failed: jobs.filter(job => job.status === -1).length,
        };
        
        // Fetch scrape targets
        const scrapeTargetsResponse = await scrapeTargetsAPI.getAll();
        const scrapeTargets = scrapeTargetsResponse.data;
        
        // Fetch media gen options
        const mediaGenOptionsResponse = await mediaGenOptionsAPI.getAll();
        const mediaGenOptions = mediaGenOptionsResponse.data;
        
        setStats({
          jobs: jobStats,
          scrapeTargets: { total: scrapeTargets.length },
          mediaGenOptions: { total: mediaGenOptions.length }
        });
      } catch (error) {
        console.error("Error fetching dashboard stats:", error);
      } finally {
        setLoading(false);
      }
    }
    
    fetchStats();
  }, []);
  
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
        Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Jobs Statistics */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="h2">
                Jobs
              </Typography>
              <Box sx={{ my: 2 }}>
                <Paper elevation={0} sx={{ p: 1, mb: 1, backgroundColor: '#f5f5f5' }}>
                  <Typography variant="body1">
                    Total: {stats.jobs.total}
                  </Typography>
                </Paper>
                <Paper elevation={0} sx={{ p: 1, mb: 1, backgroundColor: '#fff9c4' }}>
                  <Typography variant="body1">
                    Pending: {stats.jobs.pending}
                  </Typography>
                </Paper>
                <Paper elevation={0} sx={{ p: 1, mb: 1, backgroundColor: '#bbdefb' }}>
                  <Typography variant="body1">
                    Processing: {stats.jobs.processing}
                  </Typography>
                </Paper>
                <Paper elevation={0} sx={{ p: 1, mb: 1, backgroundColor: '#c8e6c9' }}>
                  <Typography variant="body1">
                    Completed: {stats.jobs.completed}
                  </Typography>
                </Paper>
                <Paper elevation={0} sx={{ p: 1, mb: 1, backgroundColor: '#ffcdd2' }}>
                  <Typography variant="body1">
                    Failed: {stats.jobs.failed}
                  </Typography>
                </Paper>
              </Box>
            </CardContent>
            <CardActions>
              <Button size="small" color="primary" component={Link} to="/jobs">
                View All Jobs
              </Button>
              <Button size="small" color="primary" component={Link} to="/jobs/create">
                Create New Job
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="h2">
                Quick Actions
              </Typography>
              <Box sx={{ my: 2 }}>
                <Button 
                  variant="contained" 
                  color="primary" 
                  fullWidth 
                  sx={{ mb: 1 }}
                  component={Link} 
                  to="/jobs/create"
                >
                  Create Job
                </Button>
                <Button 
                  variant="contained" 
                  color="primary" 
                  fullWidth 
                  sx={{ mb: 1 }}
                  component={Link} 
                  to="/scrape-targets/create"
                >
                  Add Scrape Target
                </Button>
                <Button 
                  variant="contained" 
                  color="primary" 
                  fullWidth 
                  sx={{ mb: 1 }}
                  component={Link} 
                  to="/media-gen-options/create"
                >
                  Add Media Generation Option
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Other Stats */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="h2">
                Scrape Targets
              </Typography>
              <Box sx={{ my: 2 }}>
                <Paper elevation={0} sx={{ p: 1, mb: 1, backgroundColor: '#f5f5f5' }}>
                  <Typography variant="body1">
                    Total: {stats.scrapeTargets.total}
                  </Typography>
                </Paper>
              </Box>
            </CardContent>
            <CardActions>
              <Button size="small" color="primary" component={Link} to="/scrape-targets">
                View All Scrape Targets
              </Button>
            </CardActions>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="h2">
                Media Generation Options
              </Typography>
              <Box sx={{ my: 2 }}>
                <Paper elevation={0} sx={{ p: 1, mb: 1, backgroundColor: '#f5f5f5' }}>
                  <Typography variant="body1">
                    Total: {stats.mediaGenOptions.total}
                  </Typography>
                </Paper>
              </Box>
            </CardContent>
            <CardActions>
              <Button size="small" color="primary" component={Link} to="/media-gen-options">
                View All Media Generation Options
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
}

export default Dashboard;