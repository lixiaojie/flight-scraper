import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Moon, Sun, LogOut, User, Home, ClipboardList, Settings, Smartphone, Monitor } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'
import { Button } from './ui/Button'
import { cn } from '../lib/utils'

const Header: React.FC = () => {
  const { theme, toggleTheme } = useTheme()
  const { user, logout } = useAuth()
  const location = useLocation()

  const navigation = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Task Management', href: '/tasks', icon: ClipboardList },
    { name: 'Android Automation', href: '/android-automation', icon: Smartphone },
    { name: 'Android Interface', href: '/android-interface', icon: Monitor },
    { name: 'System Config', href: '/settings', icon: Settings },
  ]

  return (
    <header className="h-16 border-b border-border bg-background flex items-center justify-between px-6">
      <div className="flex items-center gap-8">
        <h2 className="text-lg font-semibold text-foreground">
          Flight Scraper
        </h2>
        
        {/* Navigation Links */}
        <nav className="flex items-center space-x-6">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.href || 
              (item.href !== '/' && location.pathname.startsWith(item.href))
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors hover:underline',
                  isActive
                    ? 'text-primary bg-primary/10'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                <Icon className="h-4 w-4" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>

      <div className="flex items-center gap-4">
        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          className="h-9 w-9"
        >
          {theme === 'light' ? (
            <Moon className="h-4 w-4" />
          ) : (
            <Sun className="h-4 w-4" />
          )}
        </Button>

        {/* User Menu */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-accent">
            <User className="h-4 w-4" />
            <span className="text-sm font-medium">{user?.username}</span>
          </div>
          
          <Button
            variant="ghost"
            size="icon"
            onClick={logout}
            className="h-9 w-9"
            title="Logout"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}

export default Header
