import React, { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Select } from '../components/ui/Select'
import { useToastHelpers } from '../lib/toast'
import { api } from '../lib/api'
import { 
  Monitor, 
  Play, 
  Square, 
  RefreshCw, 
  Maximize2, 
  MousePointer, 
  Smartphone,
  Wifi,
  WifiOff,
  Volume2,
  VolumeX,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react'

interface AndroidContainer {
  id: number
  container_id: string
  container_name: string
  image_name: string
  image_tag: string
  status: string
  created_at: string
  started_at: string | null
  stopped_at: string | null
  host_port: number | null
  container_port: number | null
}

interface ContainerResources {
  container_id: string
  cpu_usage: string
  memory_usage: string
  disk_usage: string
  network_usage: string
  uptime: string
  status: string
}

const AndroidInterface: React.FC = () => {
  const { showSuccess, showError, showWarning } = useToastHelpers()
  const [containers, setContainers] = useState<AndroidContainer[]>([])
  const [selectedContainer, setSelectedContainer] = useState<AndroidContainer | null>(null)
  const [containerResources, setContainerResources] = useState<ContainerResources | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamUrl, setStreamUrl] = useState<string>('')
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [loading, setLoading] = useState(false)
  const [emulatorStatus, setEmulatorStatus] = useState<'checking' | 'starting' | 'ready' | 'error'>('checking')
  const [startupProgress, setStartupProgress] = useState(0)
  
  const iframeRef = useRef<HTMLIFrameElement>(null)

  // Fetch containers
  const fetchContainers = async () => {
    try {
      const response = await api.get('/android-automation/containers')
      // Sort containers by creation date in reverse chronological order (newest first)
      const sortedContainers = response.data.sort((a: any, b: any) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
      setContainers(sortedContainers)
    } catch (error: any) {
      console.error('Failed to fetch containers:', error)
      showError('Error', 'Failed to fetch containers')
    }
  }

  // Fetch container resources
  const fetchContainerResources = async (containerId: string) => {
    try {
      const response = await api.get(`/android-automation/containers/${containerId}/resources`)
      setContainerResources(response.data)
    } catch (error: any) {
      console.error('Failed to fetch container resources:', error)
    }
  }

  // Start container
  const startContainer = async (containerId: string) => {
    try {
      await api.post(`/android-automation/containers/${containerId}/start`)
      showSuccess('Container Started', 'Container started successfully')
      fetchContainers()
      if (selectedContainer?.container_id === containerId) {
        fetchContainerResources(containerId)
      }
    } catch (error: any) {
      console.error('Failed to start container:', error)
      showError('Error', error.response?.data?.detail || 'Failed to start container')
    }
  }

  // Stop container
  const stopContainer = async (containerId: string) => {
    try {
      await api.post(`/android-automation/containers/${containerId}/stop`)
      showSuccess('Container Stopped', 'Container stopped successfully')
      fetchContainers()
      if (selectedContainer?.container_id === containerId) {
        fetchContainerResources(containerId)
        setIsStreaming(false)
        setIsConnected(false)
      }
    } catch (error: any) {
      console.error('Failed to stop container:', error)
      showError('Error', error.response?.data?.detail || 'Failed to stop container')
    }
  }

  // Check Android emulator status
  const checkEmulatorStatus = async () => {
    try {
      const response = await fetch('http://localhost:6080', { method: 'HEAD' })
      if (response.ok) {
        setEmulatorStatus('ready')
        setStartupProgress(100)
        return true
      } else {
        setEmulatorStatus('starting')
        setStartupProgress(Math.min(startupProgress + 10, 90))
        return false
      }
    } catch (error) {
      setEmulatorStatus('starting')
      setStartupProgress(Math.min(startupProgress + 5, 80))
      return false
    }
  }

  // Start streaming
  const startStreaming = async () => {
    setLoading(true)
    setEmulatorStatus('checking')
    setStartupProgress(0)
    
    try {
      // Try to connect to real VNC stream
      const vncUrl = `http://localhost:6080`
      
      console.log('Testing VNC connection to:', vncUrl)
      const response = await fetch(vncUrl, { method: 'HEAD' })
      console.log('VNC response status:', response.status)
      
      if (response.ok) {
        setStreamUrl(vncUrl)
        setIsStreaming(true)
        setIsConnected(true)
        setEmulatorStatus('ready')
        setStartupProgress(100)
        showSuccess('Stream Started', 'Connected to real Android VNC interface')
        console.log('Successfully connected to VNC')
      } else {
        throw new Error(`VNC returned status ${response.status}`)
      }
    } catch (error: any) {
      console.error('Failed to start streaming:', error)
      setEmulatorStatus('error')
      showError('Error', 'Android emulator is not ready. Please wait for it to fully boot (2-5 minutes)')
    } finally {
      setLoading(false)
    }
  }

  // Stop streaming
  const stopStreaming = () => {
    setIsStreaming(false)
    setIsConnected(false)
    setStreamUrl('')
    showWarning('Stream Stopped', 'Android interface streaming stopped')
  }

  // Toggle fullscreen
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      iframeRef.current?.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  // Handle container selection
  const handleContainerSelect = (containerId: string) => {
    const container = containers.find(c => c.container_id === containerId)
    setSelectedContainer(container || null)
    if (container) {
      fetchContainerResources(container.container_id)
      if (isStreaming) {
        stopStreaming()
      }
    }
  }

  // Handle interaction with Android interface
  const handleAndroidInteraction = (action: string, data?: any) => {
    if (!selectedContainer || !isConnected) return

    console.log(`Android interaction: ${action}`, data)
    
    // Handle different types of interactions
    switch (action) {
      case 'click':
        showSuccess('Click Detected', `Clicked at (${data.x}, ${data.y})`)
        break
      case 'touch':
        if (data.duration < 200) {
          showSuccess('Tap Detected', `Tapped at (${data.x}, ${data.y})`)
        } else {
          const direction = Math.abs(data.deltaX) > Math.abs(data.deltaY) 
            ? (data.deltaX > 0 ? 'right' : 'left')
            : (data.deltaY > 0 ? 'down' : 'up')
          showSuccess('Swipe Detected', `Swiped ${direction} (${Math.abs(data.deltaX + data.deltaY)}px)`)
        }
        break
      case 'open-app':
        showSuccess('App Opening', `Opening ${data.app}...`)
        break
      case 'show-menu':
        showSuccess('Menu Action', 'Context menu activated')
        break
      default:
        showSuccess('Interaction Sent', `Android ${action} command sent successfully`)
    }
  }

  // Listen for messages from the Android interface iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'android-interaction') {
        handleAndroidInteraction(event.data.action, event.data)
      }
    }

    window.addEventListener('message', handleMessage)
    return () => window.removeEventListener('message', handleMessage)
  }, [selectedContainer, isConnected])

  // Auto-check emulator status
  useEffect(() => {
    if (emulatorStatus === 'starting') {
      const interval = setInterval(async () => {
        const isReady = await checkEmulatorStatus()
        if (isReady) {
          clearInterval(interval)
        }
      }, 5000) // Check every 5 seconds

      return () => clearInterval(interval)
    }
  }, [emulatorStatus, startupProgress])

  // Load data on component mount
  useEffect(() => {
    fetchContainers()
  }, [])

  // Update resources periodically
  useEffect(() => {
    if (!selectedContainer) return

    const interval = setInterval(() => {
      fetchContainerResources(selectedContainer.container_id)
    }, 5000) // Update every 5 seconds

    return () => clearInterval(interval)
  }, [selectedContainer])

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Android Interface</h1>
          <p className="text-muted-foreground">
            Visual interaction with Android containers
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isConnected ? (
            <Badge variant="success" className="flex items-center gap-1">
              <Wifi className="h-3 w-3" />
              Connected
            </Badge>
          ) : (
            <Badge variant="secondary" className="flex items-center gap-1">
              <WifiOff className="h-3 w-3" />
              Disconnected
            </Badge>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Container Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Smartphone className="h-5 w-5" />
              Container Selection
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Select Container
              </label>
              <Select
                value={selectedContainer?.container_id || ''}
                onChange={(e) => handleContainerSelect(e.target.value)}
              >
                <option value="">Choose a container...</option>
                {containers.map((container) => (
                  <option key={container.container_id} value={container.container_id}>
                    {container.container_name} ({container.status})
                  </option>
                ))}
              </Select>
            </div>

            {selectedContainer && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Status:</span>
                  <Badge 
                    variant={selectedContainer.status === 'running' ? 'success' : 'secondary'}
                  >
                    {selectedContainer.status}
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Image:</span>
                  <span className="text-sm text-muted-foreground">
                    {selectedContainer.image_name}:{selectedContainer.image_tag}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Port:</span>
                  <span className="text-sm text-muted-foreground">
                    {selectedContainer.host_port || 'Not set'}
                  </span>
                </div>

                <div className="flex gap-2">
                  {selectedContainer.status === 'running' ? (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => stopContainer(selectedContainer.container_id)}
                    >
                      <Square className="h-4 w-4 mr-1" />
                      Stop
                    </Button>
                  ) : (
                    <Button
                      variant="default"
                      size="sm"
                      onClick={() => startContainer(selectedContainer.container_id)}
                    >
                      <Play className="h-4 w-4 mr-1" />
                      Start
                    </Button>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Resource Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Monitor className="h-5 w-5" />
              Resource Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            {containerResources ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">CPU Usage:</span>
                  <span className="text-sm">{containerResources.cpu_usage}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Memory:</span>
                  <span className="text-sm">{containerResources.memory_usage}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Disk:</span>
                  <span className="text-sm">{containerResources.disk_usage}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Network:</span>
                  <span className="text-sm">{containerResources.network_usage}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Uptime:</span>
                  <span className="text-sm">{containerResources.uptime}</span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Select a container to view resource usage
              </p>
            )}
          </CardContent>
        </Card>

        {/* Stream Controls */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Monitor className="h-5 w-5" />
              Stream Controls
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              {!isStreaming ? (
                <Button
                  onClick={startStreaming}
                  disabled={loading}
                  className="flex-1"
                >
                  <Play className="h-4 w-4 mr-1" />
                  {loading ? 'Starting...' : 'Connect to Android'}
                </Button>
              ) : (
                <Button
                  variant="destructive"
                  onClick={stopStreaming}
                  className="flex-1"
                >
                  <Square className="h-4 w-4 mr-1" />
                  Disconnect
                </Button>
              )}
            </div>
            
            <div className="text-sm text-muted-foreground">
              <p>• <strong>Real Android:</strong> Connect to actual Android emulator (port 6080)</p>
              <p className="text-xs text-yellow-600 mt-2">
                ⚠️ Note: Android emulator may take 2-5 minutes to fully boot
              </p>
            </div>

            {/* Startup Progress */}
            {emulatorStatus !== 'ready' && (
              <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  {emulatorStatus === 'checking' && <Clock className="h-4 w-4 text-blue-600 animate-spin" />}
                  {emulatorStatus === 'starting' && <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />}
                  {emulatorStatus === 'error' && <AlertCircle className="h-4 w-4 text-red-600" />}
                  <span className="text-sm font-medium">
                    {emulatorStatus === 'checking' && 'Checking Android emulator...'}
                    {emulatorStatus === 'starting' && 'Android emulator is starting...'}
                    {emulatorStatus === 'error' && 'Android emulator not ready'}
                  </span>
                </div>
                
                {emulatorStatus === 'starting' && (
                  <div className="space-y-2">
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${startupProgress}%` }}
                      ></div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Progress: {startupProgress}% - This may take 2-5 minutes
                    </div>
                  </div>
                )}
                
                {emulatorStatus === 'error' && (
                  <div className="text-xs text-red-600">
                    The Android emulator is not ready. Please wait a few minutes and try again.
                  </div>
                )}
              </div>
            )}

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={toggleFullscreen}
                disabled={!isStreaming}
              >
                <Maximize2 className="h-4 w-4 mr-1" />
                Fullscreen
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsMuted(!isMuted)}
                disabled={!isStreaming}
              >
                {isMuted ? (
                  <VolumeX className="h-4 w-4 mr-1" />
                ) : (
                  <Volume2 className="h-4 w-4 mr-1" />
                )}
                {isMuted ? 'Unmute' : 'Mute'}
              </Button>
            </div>

            {streamUrl && (
              <div className="text-xs text-muted-foreground">
                Stream URL: {streamUrl}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Android Interface Display */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            Android Interface
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {isStreaming ? (
              <div className="relative">
                {/* Real VNC connection */}
                <iframe
                  ref={iframeRef}
                  src={streamUrl}
                  className="w-full max-w-4xl mx-auto rounded-lg border"
                  style={{ 
                    aspectRatio: '16/9',
                    height: '600px',
                    border: '2px solid #e2e8f0'
                  }}
                  title="Android VNC Interface"
                />

                {/* Stream Status Overlay */}
                <div className="absolute top-4 left-4 bg-black/50 text-white px-2 py-1 rounded text-sm">
                  <MousePointer className="h-4 w-4 inline mr-1" />
                  Real Android VNC - Click to interact
                </div>
                
                {/* Connection Info */}
                <div className="absolute top-4 right-4 bg-green-500/80 text-white px-2 py-1 rounded text-sm">
                  <Wifi className="h-4 w-4 inline mr-1" />
                  Connected
                </div>

                {/* Stream URL Info */}
                <div className="absolute bottom-4 left-4 bg-black/50 text-white px-2 py-1 rounded text-xs">
                  Real Android Emulator
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Monitor className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">No Stream Active</h3>
                <p className="text-muted-foreground mb-4">
                  Connect to Android emulator to view the interface
                </p>
                <Button
                  onClick={startStreaming}
                  disabled={loading}
                >
                  <Play className="h-4 w-4 mr-1" />
                  {loading ? 'Connecting...' : 'Connect to Android'}
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default AndroidInterface
