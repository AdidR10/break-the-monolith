"use client"
import { Button } from "@/components/ui/button"
import { Settings, LogOut, Car } from "lucide-react"
import WalletComponent from "@/components/shared/wallet-component"
import RideHistory from "@/components/shared/ride-history"
import AvailableRides from "@/components/rider/available-rides"
import { useAppContext } from "@/contexts/app-context"

interface RiderDashboardProps {
  onNavigateToSettings: () => void
  onLogout: () => void
}

export default function RiderDashboard({ onNavigateToSettings, onLogout }: RiderDashboardProps) {
  const { user, logout } = useAppContext()

  const handleLogout = async () => {
    await logout()
    onLogout()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center">
                <Car className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <Button variant="ghost" className="p-0 h-auto font-semibold text-lg" onClick={onNavigateToSettings}>
                  {user ? `${user.first_name} ${user.last_name}` : "Driver"}
                </Button>
                <p className="text-sm text-gray-500">Rickshaw Driver</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={onNavigateToSettings}>
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Wallet Section */}
        <WalletComponent />

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Available Rides Section */}
          <div>
            <AvailableRides />
          </div>

          {/* Ride History */}
          <div>
            <RideHistory />
          </div>
        </div>
      </div>
    </div>
  )
}
