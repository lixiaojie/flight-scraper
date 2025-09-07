import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { 
  ClipboardList, 
  Play, 
  CheckCircle, 
  XCircle, 
  Clock,
  TrendingUp,
  DollarSign,
  Plane,
  Plus,
  BarChart3
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { LoadingSpinner } from '../components/ui/LoadingSpinner'
import type { DashboardStats, Task } from '../types'
import { formatDate, formatCurrency } from '../lib/utils'
import api from '../lib/api'

const Home: React.FC = () => {
  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get('/dashboard/stats')
      return response.data
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  })

  const { data: recentTasks, isLoading: tasksLoading } = useQuery<Task[]>({
    queryKey: ['recent-tasks'],
    queryFn: async () => {
      const response = await api.get('/dashboard/recent-tasks')
      return response.data.tasks
    },
  })

  const StatCard = ({ 
    title, 
    value, 
    icon: Icon, 
    color, 
    description,
    highlight = false
  }: {
    title: string
    value: string | number
    icon: React.ComponentType<{ className?: string }>
    color: string
    description?: string
    highlight?: boolean
  }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className={highlight ? "ring-2 ring-red-200 dark:ring-red-800" : ""}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-gray-500">{title}</CardTitle>
          <Icon className={`h-5 w-5 ${color}`} />
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">{value}</div>
          {description && (
            <p className="text-xs text-muted-foreground mt-1">{description}</p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )

  if (statsLoading || tasksLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Flight Scraper</h1>
          <p className="text-muted-foreground">
            Monitor your flight scraping tasks and results
          </p>
        </div>
        <div className="flex gap-3">
          <Link to="/tasks">
            <Button variant="outline">
              <ClipboardList className="h-4 w-4 mr-2" />
              Task List
            </Button>
          </Link>
          <Link to="/tasks/create">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Task
            </Button>
          </Link>
        </div>
      </div>

      {/* Dashboard Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          title="Total Tasks"
          value={stats?.task_stats.total || 0}
          icon={ClipboardList}
          color="text-blue-600"
          description="All time tasks"
        />
        <StatCard
          title="Running Tasks"
          value={stats?.task_stats.running || 0}
          icon={Play}
          color="text-blue-600"
          description="Currently active"
        />
        <StatCard
          title="Completed Tasks"
          value={stats?.task_stats.completed || 0}
          icon={CheckCircle}
          color="text-green-600"
          description="Successfully finished"
        />
        <StatCard
          title="Failed Tasks"
          value={stats?.task_stats.failed || 0}
          icon={XCircle}
          color="text-red-600"
          description="Need attention"
          highlight={stats?.task_stats.failed > 0}
        />
        <StatCard
          title="Last Execution"
          value={stats?.last_execution_time ? formatDate(stats.last_execution_time) : "Never"}
          icon={Clock}
          color="text-gray-600"
          description="System status"
        />
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-500">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Link to="/tasks/create" className="block">
              <Button className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                New Task
              </Button>
            </Link>
            <Link to="/tasks" className="block">
              <Button variant="outline" className="w-full">
                <ClipboardList className="h-4 w-4 mr-2" />
                Task List
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Flight Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Flights"
          value={stats?.flight_stats.total_flights || 0}
          icon={Plane}
          color="text-purple-600"
          description="Scraped flights"
        />
        <StatCard
          title="Unique Airlines"
          value={stats?.flight_stats.unique_airlines || 0}
          icon={TrendingUp}
          color="text-indigo-600"
          description="Different carriers"
        />
        <StatCard
          title="Average Price"
          value={formatCurrency(stats?.flight_stats.average_price || 0)}
          icon={DollarSign}
          color="text-green-600"
          description="Mean flight cost"
        />
        <StatCard
          title="Lowest Price"
          value={formatCurrency(stats?.flight_stats.lowest_price || 0)}
          icon={DollarSign}
          color="text-emerald-600"
          description="Best deal found"
        />
      </div>

      {/* Recent Tasks */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Tasks</CardTitle>
          <CardDescription>
            Latest scraping tasks and their status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentTasks?.slice(0, 5).map((task) => (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3 }}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    {task.status === 'running' && <Play className="h-4 w-4 text-green-600" />}
                    {task.status === 'completed' && <CheckCircle className="h-4 w-4 text-emerald-600" />}
                    {task.status === 'failed' && <XCircle className="h-4 w-4 text-red-600" />}
                    {task.status === 'pending' && <Clock className="h-4 w-4 text-yellow-600" />}
                  </div>
                  <div>
                    <h4 className="font-medium">{task.name}</h4>
                    <p className="text-sm text-muted-foreground">
                      {task.departure_city} → {task.arrival_city}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge 
                    variant={
                      task.status === 'completed' ? 'success' :
                      task.status === 'running' ? 'warning' :
                      task.status === 'failed' ? 'error' : 'secondary'
                    }
                  >
                    {task.status}
                  </Badge>
                  <div className="text-right">
                    <div className="text-xs text-muted-foreground">
                      {formatDate(task.created_at)}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

    </div>
  )
}

export default Home
