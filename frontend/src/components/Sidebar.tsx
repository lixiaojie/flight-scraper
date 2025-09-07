import React from 'react'
import { NavLink } from 'react-router-dom'
import { 
  Home, 
  ClipboardList, 
  Settings, 
  Globe,
  BarChart3,
  Plus
} from 'lucide-react'
import { cn } from '../lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Tasks', href: '/tasks', icon: ClipboardList },
  { name: 'Create Task', href: '/tasks/create', icon: Plus },
  { name: 'Platforms', href: '/platforms', icon: Globe },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/settings', icon: Settings },
]

const Sidebar: React.FC = () => {
  return (
    <div className="w-64 bg-card border-r border-border flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-border">
        <h1 className="text-xl font-bold text-foreground">
          Flight Scraper
        </h1>
        <p className="text-sm text-muted-foreground">
          Data Collection Tool
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                )
              }
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </NavLink>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-border">
        <div className="text-xs text-muted-foreground">
          Version 1.0.0
        </div>
      </div>
    </div>
  )
}

export default Sidebar
