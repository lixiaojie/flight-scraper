import React from 'react'
import { useParams } from 'react-router-dom'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'

const TaskDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Task Details</h1>
        <p className="text-muted-foreground">
          View details and results for task #{id}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Task Information</CardTitle>
          <CardDescription>
            Detailed information about this scraping task
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              Task details and results will be displayed here
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default TaskDetails
