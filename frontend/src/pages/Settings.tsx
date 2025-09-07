import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Globe, 
  Smartphone, 
  Settings as SettingsIcon,
  Plus,
  Edit,
  Trash2,
  RotateCcw,
  Clock,
  Monitor,
  Camera
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'
import { Badge } from '../components/ui/Badge'
import { Modal } from '../components/ui/Modal'
import { useToastHelpers } from '../lib/toast'
import api, { endpoints } from '../lib/api'

const Settings: React.FC = () => {
  const [showAccountModal, setShowAccountModal] = useState(false)
  const [editingAccount, setEditingAccount] = useState<any>(null)
  const [showPlatformModal, setShowPlatformModal] = useState(false)
  const [editingPlatform, setEditingPlatform] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const { showSuccess, showError } = useToastHelpers()
  
  // Platform form state
  const [platformForm, setPlatformForm] = useState({
    name: '',
    displayName: '',
    type: 'app' as 'app' | 'website',
    bundleId: '',
    appName: '',
    downloadUrl: '',
    baseUrl: ''
  })

  // Platforms state - will be fetched from API
  const [platforms, setPlatforms] = useState<any[]>([])

  // Fetch platforms from API
  const fetchPlatforms = async () => {
    try {
      setIsLoading(true)
      const response = await api.get(endpoints.platforms.list)
      
      // Map API response to frontend format
      const mappedPlatforms = response.data.map((platform: any) => ({
        ...platform,
        type: platform.platform_type === 'mobile_app' ? 'app' : 'website',
        // Map snake_case to camelCase for frontend compatibility
        appName: platform.app_name,
        bundleId: platform.bundle_id,
        downloadUrl: platform.download_url,
        baseUrl: platform.base_url,
        isActive: platform.is_active
      }))
      setPlatforms(mappedPlatforms)
    } catch (error) {
      console.error('Failed to fetch platforms:', error)
      showError('Error', 'Failed to load platforms')
    } finally {
      setIsLoading(false)
    }
  }

  // Load platforms on component mount
  useEffect(() => {
    fetchPlatforms()
  }, [])

  const [accounts] = useState([
    { id: 1, accountId: 'user1', platform: 'Expedia', maxQueries: 100, rotationMode: 'single' },
    { id: 2, accountId: 'user2', platform: 'Kayak', maxQueries: 50, rotationMode: 'rotate' },
  ])

  const [queryRules, setQueryRules] = useState({
    minInterval: 5,
    maxInterval: 15,
    queryMethod: 'apps'
  })

  const handleAddAccount = () => {
    setEditingAccount(null)
    setShowAccountModal(true)
  }

  const handleEditAccount = (account: any) => {
    setEditingAccount(account)
    setShowAccountModal(true)
  }

  const handleAddPlatform = () => {
    setPlatformForm({
      name: '',
      displayName: '',
      type: 'app', // Default to app, user can change in modal
      bundleId: '',
      appName: '',
      downloadUrl: '',
      baseUrl: ''
    })
    setEditingPlatform(null)
    setShowPlatformModal(true)
  }

  const handleEditPlatform = (platform: any) => {
    setPlatformForm({
      name: platform.name,
      displayName: platform.name,
      type: platform.type,
      bundleId: platform.bundleId || '',
      appName: platform.appName || '',
      downloadUrl: platform.downloadUrl || '',
      baseUrl: platform.baseUrl || ''
    })
    setEditingPlatform(platform)
    setShowPlatformModal(true)
  }

  const handlePlatformFormChange = (field: string, value: string) => {
    setPlatformForm(prev => ({ ...prev, [field]: value }))
  }

  // Check if platform name is already taken
  const isNameTaken = (name: string) => {
    if (!name.trim()) return false
    return platforms.some(p => 
      p.name.toLowerCase() === name.toLowerCase() && 
      (!editingPlatform || p.id !== editingPlatform.id)
    )
  }

  const handleDeletePlatform = async (platformId: number) => {
    const platform = platforms.find(p => p.id === platformId)
    if (platform && window.confirm(`Are you sure you want to delete the platform "${platform.name}"?`)) {
      try {
        setIsLoading(true)
        await api.delete(endpoints.platforms.delete(platformId))
        showSuccess('Platform Deleted', `Platform "${platform.name}" has been deleted successfully`)
        // Refresh platforms list
        await fetchPlatforms()
      } catch (error: any) {
        console.error('Delete platform failed:', error)
        showError('Error', error.response?.data?.detail || 'Failed to delete platform')
      } finally {
        setIsLoading(false)
      }
    }
  }

  const handlePlatformSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate required fields
    if (!platformForm.name.trim()) {
      showError('Validation Error', 'Platform name is required')
      return
    }
    
    // Check for duplicate names (excluding current platform if editing)
    const existingPlatform = platforms.find(p => 
      p.name.toLowerCase() === platformForm.name.toLowerCase() && 
      (!editingPlatform || p.id !== editingPlatform.id)
    )
    if (existingPlatform) {
      showError('Validation Error', `A platform with the name "${platformForm.name}" already exists. Please choose a different name.`)
      return
    }
    
    if (platformForm.type === 'app' && !platformForm.bundleId.trim()) {
      showError('Validation Error', 'Bundle ID is required for mobile apps')
      return
    }
    
    if (platformForm.type === 'website' && !platformForm.baseUrl.trim()) {
      showError('Validation Error', 'Base URL is required for websites')
      return
    }

    try {
      setIsLoading(true)
      
      // Prepare platform data for API
      const platformData = {
        name: platformForm.name,
        display_name: platformForm.displayName || platformForm.name,
        platform_type: platformForm.type === 'app' ? 'mobile_app' : 'web',
        base_url: platformForm.type === 'website' ? platformForm.baseUrl : null,
        bundle_id: platformForm.type === 'app' ? platformForm.bundleId : null,
        app_name: platformForm.type === 'app' ? platformForm.appName : null,
        download_url: platformForm.type === 'app' ? platformForm.downloadUrl : null,
        is_active: true
      }

      if (editingPlatform) {
        // Update existing platform
        await api.put(endpoints.platforms.update(editingPlatform.id), platformData)
        showSuccess('Platform Updated', `Platform "${platformForm.name}" has been updated successfully`)
      } else {
        // Create new platform
        await api.post(endpoints.platforms.create, platformData)
        showSuccess('Platform Added', `Platform "${platformForm.name}" has been added successfully`)
      }

      // Refresh platforms list
      await fetchPlatforms()

      // Reset form and close modal
      setPlatformForm({
        name: '',
        displayName: '',
        type: 'app', // Default to app
        bundleId: '',
        appName: '',
        downloadUrl: '',
        baseUrl: ''
      })
      setShowPlatformModal(false)
      setEditingPlatform(null)

    } catch (error: any) {
      console.error('Platform operation failed:', error)
      
      // Handle specific error cases
      let errorMessage = 'Failed to save platform'
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (detail.includes && detail.includes('duplicate key')) {
          errorMessage = `A platform with the name "${platformForm.name}" already exists. Please choose a different name.`
        } else {
          errorMessage = 'Validation error: ' + JSON.stringify(detail)
        }
      } else if (error.response?.status === 422) {
        errorMessage = 'Validation error: Please check all required fields'
      } else if (error.response?.status === 409) {
        errorMessage = `A platform with the name "${platformForm.name}" already exists. Please choose a different name.`
      }
      
      showError('Error', errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">System Configuration</h1>
        <p className="text-muted-foreground">
          Configure target platforms, accounts, and query rules
        </p>
      </div>

      {/* Target Platform Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Target Platform Settings</CardTitle>
          </CardHeader>
                <CardContent>
                  {/* Add Platform Button */}
                  <div className="space-y-4 mb-6">
                    <div className="text-sm text-muted-foreground">
                      Configure platforms for flight data scraping (mobile apps and websites)
                    </div>
                    <Button onClick={handleAddPlatform}>
                      <Plus className="h-4 w-4 mr-2" />
                      Add Platform
                    </Button>
                  </div>

            {/* Platform List */}
            <div className="mt-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-medium">Configured Platforms</h3>
                <div className="flex gap-2">
                  <Badge variant="outline">
                    {platforms.filter(p => p.type === 'app').length} Apps
                  </Badge>
                  <Badge variant="outline">
                    {platforms.filter(p => p.type === 'website').length} Websites
                  </Badge>
                  <Badge variant="outline">
                    {platforms.length} Total
                  </Badge>
                </div>
              </div>

              {isLoading ? (
                <div className="text-center py-8 text-muted-foreground">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
                  <p>Loading platforms...</p>
                </div>
              ) : platforms.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <div className="mb-4">
                    <SettingsIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  </div>
                  <h4 className="text-lg font-medium mb-2">No platforms configured</h4>
                  <p className="text-sm mb-4">Add your first platform to get started</p>
                  <Button onClick={handleAddPlatform}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Platform
                  </Button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-3 font-medium text-muted-foreground">Platform</th>
                        <th className="text-left p-3 font-medium text-muted-foreground">Type</th>
                        <th className="text-left p-3 font-medium text-muted-foreground">Identifier</th>
                        <th className="text-left p-3 font-medium text-muted-foreground">Status</th>
                        <th className="text-left p-3 font-medium text-muted-foreground">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {platforms.map((platform) => (
                          <tr key={platform.id} className="border-b hover:bg-accent/50 transition-colors">
                            <td className="p-3">
                              <div className="flex items-center gap-3">
                                {platform.type === 'app' ? (
                                  <Smartphone className="h-4 w-4 text-muted-foreground" />
                                ) : (
                                  <Globe className="h-4 w-4 text-muted-foreground" />
                                )}
                                <div>
                                  <div className="font-medium">{platform.name}</div>
                                  {platform.appName && (
                                    <div className="text-sm text-muted-foreground">App: {platform.appName}</div>
                                  )}
                                </div>
                              </div>
                            </td>
                            <td className="p-3">
                              <Badge variant="outline">
                                {platform.type === 'app' ? 'Mobile App' : 'Website'}
                              </Badge>
                            </td>
                            <td className="p-3">
                              <div className="text-sm">
                                {platform.type === 'app' ? (
                                  <div className="space-y-1">
                                    <div className="font-mono text-xs">{platform.bundleId}</div>
                                    {platform.downloadUrl && (
                                      <div className="text-xs text-muted-foreground truncate max-w-xs">
                                        {platform.downloadUrl}
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <div className="text-xs text-muted-foreground truncate max-w-xs">
                                    {platform.baseUrl}
                                  </div>
                                )}
                              </div>
                            </td>
                            <td className="p-3">
                              <Badge variant={platform.isActive ? 'success' : 'secondary'}>
                                {platform.isActive ? 'Active' : 'Inactive'}
                              </Badge>
                            </td>
                            <td className="p-3">
                              <div className="flex gap-2">
                                <Button variant="outline" size="sm" onClick={() => handleEditPlatform(platform)}>
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button 
                                  variant="destructive" 
                                  size="sm" 
                                  onClick={() => handleDeletePlatform(platform.id)}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Account Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Account Settings</CardTitle>
            <CardDescription>
              Manage platform accounts and credentials
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-sm font-medium">Platform Accounts</h3>
              <Button onClick={handleAddAccount}>
                <Plus className="h-4 w-4 mr-2" />
                Add Account
              </Button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-3 font-medium text-muted-foreground">Account ID</th>
                    <th className="text-left p-3 font-medium text-muted-foreground">Platform</th>
                    <th className="text-left p-3 font-medium text-muted-foreground">Max Queries</th>
                    <th className="text-left p-3 font-medium text-muted-foreground">Rotation Mode</th>
                    <th className="text-left p-3 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {accounts.map((account) => (
                    <tr key={account.id} className="border-b hover:bg-accent/50 transition-colors">
                      <td className="p-3">
                        <span className="font-medium">{account.accountId}</span>
                      </td>
                      <td className="p-3">
                        <Badge variant="outline">{account.platform}</Badge>
                      </td>
                      <td className="p-3">
                        <span className="text-sm">{account.maxQueries}</span>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <RotateCcw className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm capitalize">{account.rotationMode}</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <Button variant="outline" size="sm" onClick={() => handleEditAccount(account)}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Rotation Toggle */}
            <div className="mt-6 p-4 border rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">Account Rotation</h4>
                  <p className="text-sm text-muted-foreground">
                    Toggle between single account and rotating accounts
                  </p>
                </div>
                <label className="flex items-center space-x-2">
                  <input type="checkbox" className="text-primary" />
                  <span className="text-sm">Rotate accounts</span>
                </label>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Query Rules */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Query Rules</CardTitle>
            <CardDescription>
              Configure scraping intervals and methods
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Interval Settings */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Min Interval (seconds)</label>
                  <div className="relative">
                    <Clock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="number"
                      value={queryRules.minInterval}
                      onChange={(e) => setQueryRules(prev => ({ ...prev, minInterval: parseInt(e.target.value) }))}
                      className="pl-10"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Max Interval (seconds)</label>
                  <div className="relative">
                    <Clock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="number"
                      value={queryRules.maxInterval}
                      onChange={(e) => setQueryRules(prev => ({ ...prev, maxInterval: parseInt(e.target.value) }))}
                      className="pl-10"
                    />
                  </div>
                </div>
              </div>

              {/* Query Method */}
              <div className="space-y-3">
                <label className="text-sm font-medium">Query Method</label>
                <div className="flex gap-4">
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="queryMethod"
                      value="apps"
                      checked={queryRules.queryMethod === 'apps'}
                      onChange={(e) => setQueryRules(prev => ({ ...prev, queryMethod: e.target.value }))}
                      className="text-primary"
                    />
                    <div className="flex items-center gap-2">
                      <Smartphone className="h-4 w-4" />
                      <span className="text-sm">Apps (Screenshots + OCR)</span>
                    </div>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="queryMethod"
                      value="websites"
                      checked={queryRules.queryMethod === 'websites'}
                      onChange={(e) => setQueryRules(prev => ({ ...prev, queryMethod: e.target.value }))}
                      className="text-primary"
                    />
                    <div className="flex items-center gap-2">
                      <Monitor className="h-4 w-4" />
                      <span className="text-sm">Websites (DOM parsing)</span>
                    </div>
                  </label>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Account Modal */}
      <Modal
        isOpen={showAccountModal}
        onClose={() => setShowAccountModal(false)}
        title={editingAccount ? 'Edit Account' : 'Add New Account'}
      >
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Username</label>
            <Input placeholder="Enter username" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Password</label>
            <Input type="password" placeholder="Enter password" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Platform</label>
            <Select>
              <option value="expedia">Expedia</option>
              <option value="kayak">Kayak</option>
              <option value="booking">Booking.com</option>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Max Queries</label>
            <Input type="number" placeholder="100" />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button variant="outline" onClick={() => setShowAccountModal(false)}>
              Cancel
            </Button>
            <Button>
              {editingAccount ? 'Update Account' : 'Add Account'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Platform Modal */}
      <Modal
        isOpen={showPlatformModal}
        onClose={() => setShowPlatformModal(false)}
        title={editingPlatform ? 'Edit Platform' : 'Add New Platform'}
        size="lg"
      >
        <form onSubmit={handlePlatformSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Platform Name</label>
              <Input 
                placeholder="e.g., 12306" 
                value={platformForm.name}
                onChange={(e) => handlePlatformFormChange('name', e.target.value)}
                className={isNameTaken(platformForm.name) ? 'border-red-500 focus:border-red-500' : ''}
                required
              />
              {isNameTaken(platformForm.name) && (
                <p className="text-sm text-red-500">
                  This name is already taken. Please choose a different name.
                </p>
              )}
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Display Name</label>
              <Input 
                placeholder="e.g., 12306 Railway" 
                value={platformForm.displayName}
                onChange={(e) => handlePlatformFormChange('displayName', e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Platform Type *</label>
            <Select 
              value={platformForm.type}
              onChange={(e) => handlePlatformFormChange('type', e.target.value)}
            >
              <option value="app">Mobile App</option>
              <option value="website">Website</option>
            </Select>
          </div>

          {platformForm.type === 'app' ? (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">Bundle ID *</label>
                <Input 
                  placeholder="e.g., com.chinarailway.globalticketing" 
                  value={platformForm.bundleId}
                  onChange={(e) => handlePlatformFormChange('bundleId', e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">App Name</label>
                <Input 
                  placeholder="e.g., 12306" 
                  value={platformForm.appName}
                  onChange={(e) => handlePlatformFormChange('appName', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Download URL</label>
                <Input 
                  placeholder="e.g., https://dynamic.12306.cn/otn/appdownload/12306v5.9.4.5.apk" 
                  value={platformForm.downloadUrl}
                  onChange={(e) => handlePlatformFormChange('downloadUrl', e.target.value)}
                />
              </div>
            </>
          ) : (
            <div className="space-y-2">
              <label className="text-sm font-medium">Base URL *</label>
              <Input 
                placeholder="e.g., https://expedia.com" 
                value={platformForm.baseUrl}
                onChange={(e) => handlePlatformFormChange('baseUrl', e.target.value)}
                required
              />
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowPlatformModal(false)}>
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={isLoading || isNameTaken(platformForm.name)}
            >
              {isLoading ? 'Saving...' : (editingPlatform ? 'Update Platform' : 'Add Platform')}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default Settings