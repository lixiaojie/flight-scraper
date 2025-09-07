import React from 'react'
import { Outlet } from 'react-router-dom'
import Header from './Header'

interface LayoutProps {
  children?: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="flex h-screen bg-background flex-col overflow-hidden">
      <Header />
      <main className="flex-1 overflow-auto">
        {children || <Outlet />}
      </main>
    </div>
  )
}

export default Layout
