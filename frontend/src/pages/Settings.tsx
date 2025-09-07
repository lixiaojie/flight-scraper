import React, { useState } from 'react'
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

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'apps' | 'websites'>('apps')
  const [showAccountModal, setShowAccountModal] = useState(false)
  const [editingAccount, setEditingAccount] = useState<any>(null)

  // Mock data
  const [platforms] = useState([
    { id: 1, name: 'Expedia', type: 'website', baseUrl: 'https://expedia.com', isActive: true },
    { id: 2, name: 'Kayak', type: 'website', baseUrl: 'https://kayak.com', isActive: true },
    { id: 3, name: 'Expedia App', type: 'app', bundleId: 'com.expedia.app', isActive: false },
  ])

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
            <CardDescription>
              Configure platforms for flight data scraping
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Tabs */}
            <div className="flex space-x-1 mb-6">
              <button
                onClick={() => setActiveTab('apps')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'apps'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Smartphone className="h-4 w-4 mr-2 inline" />
                Apps
              </button>
              <button
                onClick={() => setActiveTab('websites')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === 'websites'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Globe className="h-4 w-4 mr-2 inline" />
                Websites
              </button>
            </div>

            {/* Apps Tab */}
            {activeTab === 'apps' && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Bundle ID</label>
                  <Input placeholder="e.g., com.expedia.app" />
                </div>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add App Platform
                </Button>
              </div>
            )}

            {/* Websites Tab */}
            {activeTab === 'websites' && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Base URL</label>
                  <Input placeholder="e.g., https://expedia.com" />
                </div>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Website Platform
                </Button>
              </div>
            )}

            {/* Platform List */}
            <div className="mt-6 space-y-3">
              <h3 className="text-sm font-medium">Configured Platforms</h3>
              {platforms
                .filter(p => p.type === activeTab)
                .map((platform) => (
                  <div key={platform.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {platform.type === 'app' ? (
                        <Smartphone className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <Globe className="h-4 w-4 text-muted-foreground" />
                      )}
                      <div>
                        <div className="font-medium">{platform.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {platform.type === 'app' ? platform.bundleId : platform.baseUrl}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={platform.isActive ? 'success' : 'secondary'}>
                        {platform.isActive ? 'Active' : 'Inactive'}
                      </Badge>
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
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
    </div>
  )
}

export default Settings