import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Smartphone,
  Play,
  Square,
  Download,
  Eye,
  Trash2,
  RefreshCw,
  Activity,
  Server,
  Monitor,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { useToastHelpers } from '../lib/toast'
import api, { endpoints } from '../lib/api'

interface Platform {
  id: number
  name: string
  display_name: string
  platform_type: string
  bundle_id?: string
  app_name?: string
  download_url?: string
}

interface AutomationSession {
  id: number
  session_id: string
  platform_id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  container_id?: string
  container_name?: string
  app_package?: string
  app_version?: string
  screenshot_url?: string
  start_time: string
  end_time?: string
  error_message?: string
  execution_time?: number
}

interface Container {
  id: number
  container_id: string
  container_name: string
  image_name: string
  image_tag: string
  status: 'stopped' | 'running' | 'error'
  is_active: boolean
  created_at: string
  started_at?: string
  stopped_at?: string
}

const AndroidAutomation: React.FC = () => {
  const [platforms, setPlatforms] = useState<Platform[]>([])
  const [sessions, setSessions] = useState<AutomationSession[]>([])
  const [containers, setContainers] = useState<Container[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('')
  const [showStartModal, setShowStartModal] = useState(false)
  const [selectedPlatform, setSelectedPlatform] = useState<number | null>(null)
  const [waitTime, setWaitTime] = useState(30)
  const [captureScreenshot, setCaptureScreenshot] = useState(true)
  const { showSuccess, showError } = useToastHelpers()

  // Fetch platforms
  const fetchPlatforms = async () => {
    try {
      const response = await api.get(endpoints.platforms.list)
      setPlatforms(response.data)
    } catch (error) {
      console.error('Failed to fetch platforms:', error)
      showError('Error', 'Failed to load platforms')
    }
  }

  // Fetch automation sessions
  const fetchSessions = async () => {
    try {
      const response = await api.get('/android-automation/sessions')
      setSessions(response.data)
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
      showError('Error', 'Failed to load automation sessions')
    }
  }

  // Fetch containers
  const fetchContainers = async () => {
    try {
      const response = await api.get('/android-automation/containers')
      // Sort containers by creation date in reverse chronological order (newest first)
      const sortedContainers = response.data.sort((a: any, b: any) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
      setContainers(sortedContainers)
    } catch (error) {
      console.error('Failed to fetch containers:', error)
      showError('Error', 'Failed to load containers')
    }
  }

  // Start automation
  const startAutomation = async () => {
    if (!selectedPlatform) {
      showError('Validation Error', 'Please select a platform')
      return
    }

    try {
      setIsLoading(true)
      setLoadingMessage('Initializing automation...')
      
      // Simulate progress updates
      const progressMessages = [
        'Initializing automation...',
        'Setting up Android container...',
        'Downloading and installing app...',
        'Launching application...',
        'Capturing screenshot...',
        'Finalizing automation...'
      ]
      
      let messageIndex = 0
      const progressInterval = setInterval(() => {
        if (messageIndex < progressMessages.length - 1) {
          messageIndex++
          setLoadingMessage(progressMessages[messageIndex])
        }
      }, 2000) // Update every 2 seconds
      
      const response = await api.post('/android-automation/start', {
        platform_id: selectedPlatform,
        wait_time: waitTime,
        capture_screenshot: captureScreenshot
      })

      clearInterval(progressInterval)
      setLoadingMessage('')
      showSuccess('Automation Started', `Session ${response.data.session_id} started successfully`)
      setShowStartModal(false)
      fetchSessions()
      fetchContainers()
    } catch (error: any) {
      console.error('Failed to start automation:', error)
      showError('Error', error.response?.data?.detail || 'Failed to start automation')
    } finally {
      setIsLoading(false)
      setLoadingMessage('')
    }
  }

  // Cleanup session
  const cleanupSession = async (sessionId: string) => {
    try {
      await api.delete(`/android-automation/sessions/${sessionId}`)
      showSuccess('Session Cleaned Up', 'Session and container cleaned up successfully')
      fetchSessions()
      fetchContainers()
    } catch (error: any) {
      console.error('Failed to cleanup session:', error)
      showError('Error', error.response?.data?.detail || 'Failed to cleanup session')
    }
  }

  // Stop container
  const stopContainer = async (containerId: string) => {
    try {
      await api.post(`/android-automation/containers/${containerId}/stop`)
      showSuccess('Container Stopped', 'Container stopped successfully')
      fetchContainers()
    } catch (error: any) {
      console.error('Failed to stop container:', error)
      showError('Error', error.response?.data?.detail || 'Failed to stop container')
    }
  }

  // Start container
  const startContainer = async (containerId: string) => {
    try {
      await api.post(`/android-automation/containers/${containerId}/start`)
      showSuccess('Container Started', 'Container started successfully')
      fetchContainers()
    } catch (error: any) {
      console.error('Failed to start container:', error)
      showError('Error', error.response?.data?.detail || 'Failed to start container')
    }
  }

  // Delete container
  const deleteContainer = async (containerId: string) => {
    if (!confirm('Are you sure you want to delete this container? This action cannot be undone.')) {
      return
    }

    try {
      await api.delete(`/android-automation/containers/${containerId}`)
      showSuccess('Container Deleted', 'Container deleted successfully')
      fetchContainers()
    } catch (error: any) {
      console.error('Failed to delete container:', error)
      showError('Error', error.response?.data?.detail || 'Failed to delete container')
    }
  }

  // View container details
  const viewContainer = async (containerId: string) => {
    try {
      // Get container details
      const containerResponse = await api.get(`/android-automation/containers`)
      const container = containerResponse.data.find((c: any) => c.container_id === containerId)
      
      if (!container) {
        showError('Error', 'Container not found')
        return
      }

      // Get container resources
      let resources = null
      try {
        const resourcesResponse = await api.get(`/android-automation/containers/${containerId}/resources`)
        resources = resourcesResponse.data
      } catch (error) {
        console.log('Could not fetch container resources:', error)
      }

      // Show container details in a modal or alert for now
      const details = {
        'Container ID': container.container_id,
        'Container Name': container.container_name,
        'Image': `${container.image_name}:${container.image_tag}`,
        'Status': container.status,
        'Created': new Date(container.created_at).toLocaleString(),
        'Started': container.started_at ? new Date(container.started_at).toLocaleString() : 'Never',
        'Stopped': container.stopped_at ? new Date(container.stopped_at).toLocaleString() : 'N/A',
        'CPU Limit': container.cpu_limit || 'Not set',
        'Memory Limit': container.memory_limit || 'Not set',
        'Host Port': container.host_port || 'Not set',
        'Container Port': container.container_port || 'Not set'
      }

      if (resources) {
        details['Current CPU Usage'] = resources.cpu_usage || 'N/A'
        details['Current Memory Usage'] = resources.memory_usage || 'N/A'
        details['Current Disk Usage'] = resources.disk_usage || 'N/A'
        details['Uptime'] = resources.uptime || 'N/A'
      }

      const detailsText = Object.entries(details)
        .map(([key, value]) => `${key}: ${value}`)
        .join('\n')

      alert(`Container Details:\n\n${detailsText}`)
      
    } catch (error: any) {
      console.error('Failed to view container:', error)
      showError('Error', error.response?.data?.detail || 'Failed to view container details')
    }
  }

  // Load data on component mount
  useEffect(() => {
    fetchPlatforms()
    fetchSessions()
    fetchContainers()
  }, [])

  // Get status badge variant
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="success"><CheckCircle className="h-3 w-3 mr-1" />Completed</Badge>
      case 'running':
        return <Badge variant="default"><Activity className="h-3 w-3 mr-1" />Running</Badge>
      case 'failed':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>
      case 'pending':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Pending</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  // Get container status badge
  const getContainerStatusBadge = (status: string) => {
    switch (status) {
      case 'running':
        return <Badge variant="success"><CheckCircle className="h-3 w-3 mr-1" />Running</Badge>
      case 'stopped':
        return <Badge variant="secondary"><Square className="h-3 w-3 mr-1" />Stopped</Badge>
      case 'error':
        return <Badge variant="destructive"><AlertCircle className="h-3 w-3 mr-1" />Error</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Android Automation</h1>
        <p className="text-muted-foreground">
          Deploy and test Android applications in containerized environments
        </p>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Start new automation sessions and manage containers
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Button onClick={() => setShowStartModal(true)}>
                <Play className="h-4 w-4 mr-2" />
                Start Automation
              </Button>
              <Button variant="outline" onClick={() => { fetchSessions(); fetchContainers(); }}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Container Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Container Status</CardTitle>
            <CardDescription>
              Monitor Android container status and resources
            </CardDescription>
          </CardHeader>
          <CardContent>
            {containers.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Server className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <h4 className="text-lg font-medium mb-2">No containers found</h4>
                <p className="text-sm">Start an automation session to create containers</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-medium text-muted-foreground">Container</th>
                      <th className="text-left p-3 font-medium text-muted-foreground">Image</th>
                      <th className="text-left p-3 font-medium text-muted-foreground">Status</th>
                      <th className="text-left p-3 font-medium text-muted-foreground">Created</th>
                      <th className="text-left p-3 font-medium text-muted-foreground">Latest Start</th>
                      <th className="text-left p-3 font-medium text-muted-foreground">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {containers.map((container) => (
                      <tr key={container.id} className="border-b hover:bg-accent/50 transition-colors">
                        <td className="p-3">
                          <div className="flex items-center gap-3">
                            <Server className="h-4 w-4 text-muted-foreground" />
                            <div>
                              <div className="font-medium">{container.container_name}</div>
                              <div className="text-sm text-muted-foreground font-mono">
                                {container.container_id.substring(0, 12)}...
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="p-3">
                          <div className="text-sm">
                            <div className="font-medium">{container.image_name}</div>
                            <div className="text-muted-foreground">{container.image_tag}</div>
                          </div>
                        </td>
                        <td className="p-3">
                          {getContainerStatusBadge(container.status)}
                        </td>
                        <td className="p-3">
                          <div className="text-sm text-muted-foreground">
                            {new Date(container.created_at).toLocaleString()}
                          </div>
                        </td>
                        <td className="p-3">
                          <div className="text-sm text-muted-foreground">
                            {container.started_at ? new Date(container.started_at).toLocaleString() : '-'}
                          </div>
                        </td>
                        <td className="p-3">
                          <div className="flex gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => viewContainer(container.container_id)}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              View
                            </Button>
                            {container.status === 'running' ? (
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => stopContainer(container.container_id)}
                              >
                                <Square className="h-4 w-4 mr-1" />
                                Stop
                              </Button>
                            ) : (
                              <>
                                <Button
                                  variant="default"
                                  size="sm"
                                  onClick={() => startContainer(container.container_id)}
                                >
                                  <Play className="h-4 w-4 mr-1" />
                                  Start
                                </Button>
                                <Button
                                  variant="destructive"
                                  size="sm"
                                  onClick={() => deleteContainer(container.container_id)}
                                >
                                  <Trash2 className="h-4 w-4 mr-1" />
                                  Delete
                                </Button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Automation Sessions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Automation Sessions</CardTitle>
            <CardDescription>
              View and manage automation execution history
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sessions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Monitor className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <h4 className="text-lg font-medium mb-2">No automation sessions</h4>
                <p className="text-sm">Start your first automation session to begin testing</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-medium text-muted-foreground">Session</th>
                      <th className="text-left p-3 font-medium text-muted-foreground">Platform</th>
                      <th className="text-left p-3 font-medium text-muted-foreground">Status</th>
                      <th className="text-left p-3 font-medium text-muted-foreground">Duration</th>
                      <th className="text-left p-3 font-medium text-muted-foreground">Screenshot</th>
                      <th className="text-left p-3 font-medium text-muted-foreground">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sessions.map((session) => {
                      const platform = platforms.find(p => p.id === session.platform_id)
                      return (
                        <tr key={session.id} className="border-b hover:bg-accent/50 transition-colors">
                          <td className="p-3">
                            <div className="flex items-center gap-3">
                              <Smartphone className="h-4 w-4 text-muted-foreground" />
                              <div>
                                <div className="font-medium">{session.session_id.substring(0, 8)}...</div>
                                <div className="text-sm text-muted-foreground">
                                  {new Date(session.start_time).toLocaleString()}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="p-3">
                            <div className="text-sm">
                              <div className="font-medium">{platform?.name || 'Unknown'}</div>
                              {session.app_package && (
                                <div className="text-muted-foreground font-mono text-xs">
                                  {session.app_package}
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="p-3">
                            {getStatusBadge(session.status)}
                          </td>
                          <td className="p-3">
                            <div className="text-sm text-muted-foreground">
                              {session.execution_time ? `${session.execution_time.toFixed(1)}s` : '-'}
                            </div>
                          </td>
                          <td className="p-3">
                            {session.screenshot_url ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => window.open(session.screenshot_url, '_blank')}
                              >
                                <Eye className="h-4 w-4" />
                              </Button>
                            ) : (
                              <span className="text-muted-foreground text-sm">-</span>
                            )}
                          </td>
                          <td className="p-3">
                            <div className="flex gap-2">
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => cleanupSession(session.session_id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Start Automation Modal */}
      <Modal
        isOpen={showStartModal}
        onClose={() => setShowStartModal(false)}
        title="Start Android Automation"
        size="lg"
      >
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Select Platform *</label>
            <Select
              value={selectedPlatform?.toString() || ''}
              onChange={(e) => setSelectedPlatform(parseInt(e.target.value))}
            >
              <option value="">Choose a platform...</option>
              {platforms
                .filter(p => p.platform_type === 'mobile_app')
                .map((platform) => (
                  <option key={platform.id} value={platform.id}>
                    {platform.display_name} ({platform.name})
                  </option>
                ))}
            </Select>
          </div>

          {/* Platform Information Display */}
          {selectedPlatform && (() => {
            const platform = platforms.find(p => p.id === selectedPlatform)
            if (!platform) return null
            
            return (
              <div className="bg-accent/50 rounded-lg p-4 space-y-2">
                <h4 className="text-sm font-medium text-foreground">Platform Configuration</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-muted-foreground">App Name:</span>
                    <div className="font-medium">{platform.app_name || 'Not specified'}</div>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Bundle ID:</span>
                    <div className="font-mono font-medium">{platform.bundle_id || 'Not specified'}</div>
                  </div>
                  <div className="col-span-2">
                    <span className="text-muted-foreground">Download URL:</span>
                    <div className="font-mono text-xs break-all">{platform.download_url || 'Not specified'}</div>
                  </div>
                </div>
                {(!platform.bundle_id || !platform.download_url) && (
                  <div className="text-xs text-yellow-600 bg-yellow-50 p-2 rounded">
                    ⚠️ This platform is missing required configuration. Please update the platform settings.
                  </div>
                )}
              </div>
            )
          })()}

          {/* Progress Indicator */}
          {isLoading && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
                <div>
                  <p className="text-sm font-medium text-blue-900">
                    {loadingMessage || 'Starting Automation...'}
                  </p>
                  <p className="text-xs text-blue-700 mt-1">
                    This may take 10-15 seconds. Please wait...
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium">Wait Time (seconds)</label>
            <Input
              type="number"
              min="5"
              max="300"
              value={waitTime}
              onChange={(e) => setWaitTime(parseInt(e.target.value))}
              placeholder="30"
            />
            <p className="text-xs text-muted-foreground">
              Time to wait for app to load before capturing screenshot
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="captureScreenshot"
              checked={captureScreenshot}
              onChange={(e) => setCaptureScreenshot(e.target.checked)}
              className="rounded border-gray-300"
            />
            <label htmlFor="captureScreenshot" className="text-sm font-medium">
              Capture Screenshot
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" onClick={() => setShowStartModal(false)}>
              Cancel
            </Button>
            <Button 
              onClick={startAutomation} 
              disabled={
                isLoading || 
                !selectedPlatform || 
                (selectedPlatform && (() => {
                  const platform = platforms.find(p => p.id === selectedPlatform)
                  return !platform?.bundle_id || !platform?.download_url
                })())
              }
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {loadingMessage || 'Starting Automation...'}
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Start Automation
                </>
              )}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default AndroidAutomation
