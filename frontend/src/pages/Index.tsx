import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Index = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is authenticated
    const token = localStorage.getItem('token');
    
    // If no token, redirect to login
    if (!token) {
      navigate('/login');
      return;
    }

    // If authenticated, check role and redirect accordingly
    const isAdmin = localStorage.getItem('isAdmin') === 'true';
    if (isAdmin) {
      navigate('/admin-dashboard');
    } else {
      navigate('/video-library');
    }
  }, [navigate]);

  // Show nothing while redirecting
  return null;
};

export default Index;