import { useToast } from '../components/ui/Toaster'

// Utility functions for common toast operations
export const useToastHelpers = () => {
  const { addToast } = useToast()

  const showSuccess = (title: string, description?: string) => {
    addToast({
      title,
      description,
      type: 'success',
      duration: 4000
    })
  }

  const showError = (title: string, description?: string) => {
    addToast({
      title,
      description,
      type: 'error',
      duration: 6000
    })
  }

  const showWarning = (title: string, description?: string) => {
    addToast({
      title,
      description,
      type: 'warning',
      duration: 5000
    })
  }

  const showInfo = (title: string, description?: string) => {
    addToast({
      title,
      description,
      type: 'default',
      duration: 4000
    })
  }

  return {
    showSuccess,
    showError,
    showWarning,
    showInfo,
    addToast
  }
}

// Export the hook for direct use
export { useToast } from '../components/ui/Toaster'
