import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'
import Layout from './components/Layout'
import Home from './pages/Home'
import Tasks from './pages/Tasks'
import TaskDetails from './pages/TaskDetails'
import CreateTask from './pages/CreateTask'
import Platforms from './pages/Platforms'
import Settings from './pages/Settings'
import MobileAutomation from './pages/MobileAutomation'
import AndroidInterface from './pages/AndroidInterface'
import Login from './pages/Login'
import ProtectedRoute from './components/ProtectedRoute'
import { Toaster, ToastProvider } from './components/ui/Toaster'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <Router>
              <div className="min-h-screen bg-background">
                <Routes>
                  <Route path="/login" element={<Login />} />
                  <Route
                    path="/*"
                    element={
                      <ProtectedRoute>
                        <Layout>
                          <Routes>
                            <Route path="/" element={<Home />} />
                            <Route path="/tasks" element={<Tasks />} />
                            <Route path="/tasks/create" element={<CreateTask />} />
                                   <Route path="/tasks/:id" element={<TaskDetails />} />
                                   <Route path="/platforms" element={<Platforms />} />
                                   <Route path="/settings" element={<Settings />} />
                                   <Route path="/mobile-automation" element={<MobileAutomation />} />
                                   <Route path="/android-interface" element={<AndroidInterface />} />
                          </Routes>
                        </Layout>
                      </ProtectedRoute>
                    }
                  />
                </Routes>
                <Toaster />
              </div>
            </Router>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

export default App