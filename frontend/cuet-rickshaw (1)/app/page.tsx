"use client"

import { useState, useEffect } from "react"
import { Loader2 } from "lucide-react"
import AuthPage from "@/components/auth/auth-page"
import UserDashboard from "@/components/user/user-dashboard"
import RiderDashboard from "@/components/rider/rider-dashboard"
import SettingsPage from "@/components/settings/settings-page"
import ErrorBoundary from "@/components/shared/error-boundary"
import { AppProvider, useAppContext } from "@/contexts/app-context"

export default function App() {
  return (
    <ErrorBoundary>
      <AppProvider>
        <MainApp />
      </AppProvider>
    </ErrorBoundary>
  )
}

function MainApp() {
  const { isAuthenticated, user, profile, isLoading } = useAppContext()
  const [currentPage, setCurrentPage] = useState<"auth" | "user" | "rider" | "settings">("auth")

  useEffect(() => {
    if (isAuthenticated && user) {
      const userType = user.user_type === "STUDENT" ? "user" : "rider"
      setCurrentPage(userType)
    } else {
      setCurrentPage("auth")
    }
  }, [isAuthenticated, user])

  const handleLogin = (type: "user" | "rider") => {
    setCurrentPage(type)
  }

  const handleLogout = () => {
    setCurrentPage("auth")
  }

  const navigateToSettings = () => {
    setCurrentPage("settings")
  }

  const navigateBack = () => {
    if (user) {
      const userType = user.user_type === "STUDENT" ? "user" : "rider"
      setCurrentPage(userType)
    }
  }

  // Show loading screen during initial authentication check
  if (isLoading && currentPage === "auth") {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <AuthPage onLogin={handleLogin} />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
      {currentPage === "user" && <UserDashboard onNavigateToSettings={navigateToSettings} onLogout={handleLogout} />}
      {currentPage === "rider" && <RiderDashboard onNavigateToSettings={navigateToSettings} onLogout={handleLogout} />}
      {currentPage === "settings" && <SettingsPage onNavigateBack={navigateBack} onLogout={handleLogout} />}
    </div>
  )
}
