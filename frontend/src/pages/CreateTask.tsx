import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  Plane, 
  Calendar, 
  Users, 
  ArrowRight,
  Clock,
  Repeat
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Select } from '../components/ui/Select'

const CreateTask: React.FC = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    departure_city: '',
    arrival_city: '',
    travel_date: '',
    num_travelers: 1,
    cabin_class: 'economy',
    validity: 'scheduled',
    frequency: 'one-time'
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Implement task creation
    console.log('Creating task:', formData)
    navigate('/tasks')
  }

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Create New Task</h1>
        <p className="text-muted-foreground">
          Set up a new flight scraping task
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Task Configuration</CardTitle>
            <CardDescription>
              Configure your flight search parameters
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Flight Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Departure City</label>
                  <div className="relative">
                    <Plane className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="e.g., New York"
                      value={formData.departure_city}
                      onChange={(e) => handleInputChange('departure_city', e.target.value)}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Arrival City</label>
                  <div className="relative">
                    <Plane className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="e.g., Los Angeles"
                      value={formData.arrival_city}
                      onChange={(e) => handleInputChange('arrival_city', e.target.value)}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>
              </div>

              {/* Travel Date */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Travel Date</label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="date"
                    value={formData.travel_date}
                    onChange={(e) => handleInputChange('travel_date', e.target.value)}
                    className="pl-10"
                    required
                  />
                </div>
              </div>

              {/* Travelers and Cabin Class */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Number of Travelers</label>
                  <div className="relative">
                    <Users className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="number"
                      min="1"
                      max="9"
                      value={formData.num_travelers}
                      onChange={(e) => handleInputChange('num_travelers', parseInt(e.target.value))}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Cabin Class</label>
                  <Select
                    value={formData.cabin_class}
                    onChange={(e) => handleInputChange('cabin_class', e.target.value)}
                    required
                  >
                    <option value="economy">Economy</option>
                    <option value="premium_economy">Premium Economy</option>
                    <option value="business">Business</option>
                    <option value="first">First Class</option>
                  </Select>
                </div>
              </div>

              {/* Validity */}
              <div className="space-y-3">
                <label className="text-sm font-medium">Validity</label>
                <div className="flex gap-4">
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="validity"
                      value="scheduled"
                      checked={formData.validity === 'scheduled'}
                      onChange={(e) => handleInputChange('validity', e.target.value)}
                      className="text-primary"
                    />
                    <span className="text-sm">Scheduled</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="validity"
                      value="instant"
                      checked={formData.validity === 'instant'}
                      onChange={(e) => handleInputChange('validity', e.target.value)}
                      className="text-primary"
                    />
                    <span className="text-sm">Instant</span>
                  </label>
                </div>
              </div>

              {/* Frequency */}
              <div className="space-y-3">
                <label className="text-sm font-medium">Frequency</label>
                <div className="flex gap-4">
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="frequency"
                      value="one-time"
                      checked={formData.frequency === 'one-time'}
                      onChange={(e) => handleInputChange('frequency', e.target.value)}
                      className="text-primary"
                    />
                    <span className="text-sm">One-time</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="radio"
                      name="frequency"
                      value="recurring"
                      checked={formData.frequency === 'recurring'}
                      onChange={(e) => handleInputChange('frequency', e.target.value)}
                      className="text-primary"
                    />
                    <span className="text-sm">Recurring</span>
                  </label>
                </div>
              </div>

              {/* Submit Button */}
              <div className="flex justify-end gap-3 pt-6">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate('/tasks')}
                >
                  Cancel
                </Button>
                <Button type="submit">
                  <ArrowRight className="h-4 w-4 mr-2" />
                  Create Task
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

export default CreateTask
