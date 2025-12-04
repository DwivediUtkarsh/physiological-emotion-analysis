import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Users, Video, Activity, PieChart } from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart as RePieChart,
  Pie,
  Cell,
} from 'recharts';

interface EmotionDistribution {
  [key: string]: number;
}

interface UserStats {
  total_annotations: number;
  emotion_distribution: EmotionDistribution;
  videos_annotated: string[];
  last_active: string;
  completion_rate: number;
}

interface VideoStats {
  total_segments: number;
  annotated_segments: number;
  completion_percentage: number;
  emotion_distribution: EmotionDistribution;
  annotated_by_users: string[];
}

interface DetailedStats {
  user_statistics: { [key: string]: UserStats };
  video_statistics: { [key: string]: VideoStats };
  overall_emotion_distribution: EmotionDistribution;
  total_users: number;
  total_videos_annotated: number;
}

const COLORS = {
  Happy: '#4CAF50',
  Sad: '#2196F3',
  Angry: '#F44336',
  Neutral: '#9E9E9E'
};

export default function AdminDashboard() {
  const [stats, setStats] = useState<DetailedStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const isAdmin = localStorage.getItem('isAdmin') === 'true';

    if (!token || !isAdmin) {
      navigate('/login');
      return;
    }

    fetchStats();
  }, [navigate]);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/admin/detailed-stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch statistics');
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError('Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('isAdmin');
    navigate('/login');
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const prepareEmotionData = (distribution: EmotionDistribution) => {
    return Object.entries(distribution).map(([name, value]) => ({
      name,
      value
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-red-500">{error || 'No data available'}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <Button 
          variant="outline" 
          onClick={handleLogout}
          className="border-border hover:bg-secondary"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Logout
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-blue-500" />
              <div className="ml-4">
                <p className="text-2xl font-bold">{stats.total_users}</p>
                <p className="text-sm text-muted-foreground">Total Users</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <Video className="h-8 w-8 text-green-500" />
              <div className="ml-4">
                <p className="text-2xl font-bold">{stats.total_videos_annotated}</p>
                <p className="text-sm text-muted-foreground">Videos Annotated</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-purple-500" />
              <div className="ml-4">
                <p className="text-2xl font-bold">
                  {Object.values(stats.user_statistics).reduce((acc, user) => acc + user.total_annotations, 0)}
                </p>
                <p className="text-sm text-muted-foreground">Total Annotations</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center">
              <PieChart className="h-8 w-8 text-orange-500" />
              <div className="ml-4">
                <p className="text-2xl font-bold">
                  {Object.values(stats.user_statistics).reduce((acc, user) => acc + user.completion_rate, 0) / stats.total_users}%
                </p>
                <p className="text-sm text-muted-foreground">Avg. Completion Rate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Overall Emotion Distribution */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Overall Emotion Distribution</CardTitle>
          <CardDescription>Distribution of emotions across all annotations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <RePieChart>
                <Pie
                  data={prepareEmotionData(stats.overall_emotion_distribution)}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {prepareEmotionData(stats.overall_emotion_distribution).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </RePieChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* User Statistics */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>User Statistics</CardTitle>
          <CardDescription>Detailed statistics for each user</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Username</TableHead>
                <TableHead>Total Annotations</TableHead>
                <TableHead>Videos Annotated</TableHead>
                <TableHead>Completion Rate</TableHead>
                <TableHead>Last Active</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(stats.user_statistics).map(([username, userStats]) => (
                <TableRow key={username}>
                  <TableCell className="font-medium">{username}</TableCell>
                  <TableCell>{userStats.total_annotations}</TableCell>
                  <TableCell>{userStats.videos_annotated.length}</TableCell>
                  <TableCell>{userStats.completion_rate.toFixed(1)}%</TableCell>
                  <TableCell>{formatDate(userStats.last_active)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Video Statistics */}
      <Card>
        <CardHeader>
          <CardTitle>Video Statistics</CardTitle>
          <CardDescription>Annotation statistics per video</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Video Name</TableHead>
                <TableHead>Total Segments</TableHead>
                <TableHead>Annotated Segments</TableHead>
                <TableHead>Completion</TableHead>
                <TableHead>Annotated By</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(stats.video_statistics).map(([videoName, videoStats]) => (
                <TableRow key={videoName}>
                  <TableCell className="font-medium">{videoName}</TableCell>
                  <TableCell>{videoStats.total_segments}</TableCell>
                  <TableCell>{videoStats.annotated_segments}</TableCell>
                  <TableCell>{videoStats.completion_percentage.toFixed(1)}%</TableCell>
                  <TableCell>{videoStats.annotated_by_users.join(', ')}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}