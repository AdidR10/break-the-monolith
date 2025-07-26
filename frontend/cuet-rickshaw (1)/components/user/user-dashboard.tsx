"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { User, Settings, LogOut, MapPin, Navigation } from "lucide-react"
import WalletComponent from "@/components/shared/wallet-component"
import RideHistory from "@/components/shared/ride-history"
import RideRequest from "@/components/user/ride-request"
import { useAppContext } from "@/contexts/app-context"

interface UserDashboardProps {
  onNavigateToSettings: () => void
  onLogout: () => void
}

export default function UserDashboard({ onNavigateToSettings, onLogout }: UserDashboardProps) {
  const { user, profile, activeRide, logout } = useAppContext()

  const handleLogout = async () => {
    await logout()
    onLogout()
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "ACCEPTED":
        return "default"
      case "DRIVER_ARRIVED":
        return "secondary"
      case "STARTED":
        return "secondary"
      default:
        return "outline"
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                <User className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <Button variant="ghost" className="p-0 h-auto font-semibold text-lg" onClick={onNavigateToSettings}>
                  {user ? `${user.first_name} ${user.last_name}` : "User"}
                </Button>
                <p className="text-sm text-gray-500">Student</p>
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
          {/* Ride Request Section */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Navigation className="h-5 w-5 text-blue-600" />
                  Request a Ride
                </CardTitle>
              </CardHeader>
              <CardContent>
                {activeRide ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-semibold">Current Ride</h3>
                        <Badge variant={getStatusBadgeVariant(activeRide.status)}>
                          {activeRide.status.replace("_", " ")}
                        </Badge>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-green-600" />
                          <span>From: {activeRide.pickup_location}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-red-600" />
                          <span>To: {activeRide.drop_location}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Fare: ৳{activeRide.fare_amount || activeRide.estimated_fare}</span>
                          <span>Requested: {formatDate(activeRide.requested_at)}</span>
                        </div>
                      </div>

                      {activeRide.status === "ACCEPTED" && activeRide.driver_id && (
                        <div className="mt-4 p-3 bg-white rounded border">
                          <h4 className="font-semibold mb-2">Rider Information</h4>
                          <div className="space-y-1 text-sm">
                            <p>
                              <strong>Status:</strong> Driver Assigned
                            </p>
                            <p>
                              <strong>Driver ID:</strong> {activeRide.driver_id}
                            </p>
                            {activeRide.accepted_at && (
                              <p>
                                <strong>Accepted At:</strong> {formatDate(activeRide.accepted_at)}
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <RideRequest />
                )}
              </CardContent>
            </Card>
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
