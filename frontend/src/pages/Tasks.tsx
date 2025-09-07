import React from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { 
  Plus, 
  Play, 
  Pause, 
  Eye, 
  Download,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Calendar,
  Users,
  Plane
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import type { Task } from '../types'
import { formatDate, getStatusColor } from '../lib/utils'
import api from '../lib/api'

const Tasks: React.FC = () => {
  const { data: tasks, isLoading } = useQuery<Task[]>({
    queryKey: ['tasks'],
    queryFn: async () => {
      const response = await api.get('/tasks')
      return response.data.tasks
    },
    refetchInterval: 10000, // Refetch every 10 seconds
  })

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Play className="h-4 w-4 text-green-600" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-emerald-600" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-dots">
          <div></div>
          <div></div>
          <div></div>
          <div></div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Task Management</h1>
          <p className="text-muted-foreground">
            Manage your flight scraping tasks
          </p>
        </div>
        <Link to="/tasks/create">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Create New Task
          </Button>
        </Link>
      </div>

      {/* Tasks Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Tasks</CardTitle>
          <CardDescription>
            View and manage all your scraping tasks
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-4 font-medium text-muted-foreground">Creation Time</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Status</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Completion Time</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Departure</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Arrival</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Date</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Travelers</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Cabin</th>
                  <th className="text-left p-4 font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {tasks?.map((task) => (
                  <motion.tr
                    key={task.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className="border-b hover:bg-accent/50 transition-colors"
                  >
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">{formatDate(task.created_at)}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(task.status)}
                        <Badge 
                          variant={
                            task.status === 'completed' ? 'success' :
                            task.status === 'running' ? 'warning' :
                            task.status === 'failed' ? 'error' : 'secondary'
                          }
                        >
                          {task.status}
                        </Badge>
                      </div>
                    </td>
                    <td className="p-4">
                      <span className="text-sm text-muted-foreground">
                        {task.completed_at ? formatDate(task.completed_at) : '-'}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Plane className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{task.departure_city}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Plane className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium">{task.arrival_city}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <span className="text-sm">{formatDate(task.travel_date)}</span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">{task.num_travelers}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      <span className="text-sm capitalize">{task.cabin_class}</span>
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Link to={`/tasks/${task.id}`}>
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                        
                        {task.status === 'completed' && (
                          <Button variant="outline" size="sm">
                            <Download className="h-4 w-4" />
                          </Button>
                        )}
                        
                        {task.status === 'pending' && (
                          <Button size="sm">
                            <Play className="h-4 w-4" />
                          </Button>
                        )}
                        
                        {task.status === 'running' && (
                          <Button variant="outline" size="sm">
                            <Pause className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {tasks?.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <div className="text-muted-foreground mb-4">
              <Clock className="h-12 w-12 mx-auto mb-4" />
              <h3 className="text-lg font-medium">No tasks yet</h3>
              <p>Create your first scraping task to get started</p>
            </div>
            <Link to="/tasks/create">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Your First Task
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default Tasks
