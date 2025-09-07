import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'

const Platforms: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Platforms</h1>
        <p className="text-muted-foreground">
          Manage target platforms and accounts
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Platform Configuration</CardTitle>
          <CardDescription>
            Configure target platforms for scraping
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              Platform management interface will be implemented here
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Platforms
