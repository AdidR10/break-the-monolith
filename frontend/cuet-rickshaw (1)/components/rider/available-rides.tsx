"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { MapPin, Clock, DollarSign, AlertCircle, RefreshCw, Loader2, Navigation } from "lucide-react"
import { useAppContext } from "@/contexts/app-context"
import { RideService, type RideRequest } from "@/lib/api-client"

export default function AvailableRides() {
  const { wallet, isLoading, refreshRides } = useAppContext()
  const [availableRides, setAvailableRides] = useState<RideRequest[]>([])
  const [error, setError] = useState("")
  const [acceptingRide, setAcceptingRide] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)

  useEffect(() => {
    loadAvailableRides()

    // Refresh every 30 seconds
    const interval = setInterval(loadAvailableRides, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadAvailableRides = async () => {
    try {
      const response = await RideService.getActiveRideRequests()
      if (response.success && response.data) {
        setAvailableRides(response.data)
        setError("")
      } else if (response.error) {
        setError(response.error)
      }
    } catch (error) {
      console.error("Error loading available rides:", error)
      setError("Failed to load available rides")
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await loadAvailableRides()
    setIsRefreshing(false)
  }

  const handleAcceptRide = async (rideRequestId: string, estimatedFare?: number) => {
    setAcceptingRide(rideRequestId)
    setError("")

    try {
      // Create an offer for the ride request
      const offerResponse = await RideService.createRideOffer(rideRequestId, {
        offered_fare: estimatedFare,
        estimated_arrival_time: Math.floor(Math.random() * 10) + 5, // 5-15 minutes
        message: "I can pick you up!",
      })

      if (offerResponse.success && offerResponse.data) {
        // Accept the offer immediately (in a real app, the user would accept)
        const acceptResponse = await RideService.acceptRideOffer(offerResponse.data.id)

        if (acceptResponse.success) {
          // Remove the accepted ride from available rides
          setAvailableRides((prev) => prev.filter((ride) => ride.id !== rideRequestId))

          // Refresh rides to show in history
          await refreshRides()

          // Show success message
          console.log(`Ride accepted! Fare: ৳${estimatedFare ? Number(estimatedFare).toFixed(2) : "TBD"}`)
        } else {
          setError(acceptResponse.error || "Failed to accept ride offer")
        }
      } else {
        setError(offerResponse.error || "Failed to create ride offer")
      }
    } catch (error) {
      setError("Failed to accept ride. Please try again.")
    } finally {
      setAcceptingRide(null)
    }
  }

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / (1000 * 60))

      if (diffMins < 1) return "Just now"
      if (diffMins < 60) return `${diffMins} min ago`
      if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hr ago`

      return date.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    } catch (error) {
      return dateString
    }
  }

  const isRideExpired = (expiresAt: string) => {
    try {
      return new Date(expiresAt) < new Date()
    } catch {
      return false
    }
  }

  const activeRides = availableRides.filter((ride) => ride.is_active && !isRideExpired(ride.expires_at))

  if (isLoading && activeRides.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Navigation className="h-5 w-5 text-green-600" />
            Available Rides
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-6 w-24" />
                  <Skeleton className="h-4 w-20" />
                </div>
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-full" />
                </div>
                <div className="flex items-center justify-between">
                  <Skeleton className="h-6 w-16" />
                  <Skeleton className="h-9 w-24" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Navigation className="h-5 w-5 text-green-600" />
            Available Rides
          </div>
          <Button variant="ghost" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-4">
          {activeRides.length === 0 ? (
            <div className="text-center py-8">
              <Navigation className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No rides available at the moment</p>
              <p className="text-sm text-gray-400 mt-1">New ride requests will appear here</p>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                className="mt-4 bg-transparent"
                disabled={isRefreshing}
              >
                {isRefreshing ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-2" />
                )}
                Refresh
              </Button>
            </div>
          ) : (
            activeRides.map((ride) => (
              <div key={ride.id} className="border rounded-lg p-4 space-y-3 hover:shadow-sm transition-shadow">
                <div className="flex items-center justify-between">
                  <Badge variant="secondary" className="bg-green-100 text-green-800">
                    New Request
                  </Badge>
                  <div className="flex items-center gap-1 text-sm text-gray-500">
                    <Clock className="h-4 w-4" />
                    {formatDate(ride.created_at)}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-start gap-2 text-sm">
                    <MapPin className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="font-medium">From:</span> {ride.pickup_location}
                    </div>
                  </div>
                  <div className="flex items-start gap-2 text-sm">
                    <MapPin className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="font-medium">To:</span> {ride.drop_location}
                    </div>
                  </div>
                </div>

                {ride.estimated_distance && (
                  <div className="text-sm text-gray-600">
                    <span className="font-medium">Distance:</span> {Number(ride.estimated_distance).toFixed(1)} km
                    {ride.estimated_duration && (
                      <span className="ml-3">
                        <span className="font-medium">Duration:</span> ~{ride.estimated_duration} min
                      </span>
                    )}
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <DollarSign className="h-4 w-4 text-green-600" />
                    <span className="font-semibold text-green-600">৳{ride.estimated_fare ? Number(ride.estimated_fare).toFixed(2) : "TBD"}</span>
                  </div>
                  <Button
                    onClick={() => handleAcceptRide(ride.id, ride.estimated_fare)}
                    className="bg-green-600 hover:bg-green-700"
                    disabled={acceptingRide === ride.id || isLoading}
                  >
                    {acceptingRide === ride.id ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Accepting...
                      </>
                    ) : (
                      "Accept Ride"
                    )}
                  </Button>
                </div>

                {ride.special_requirements && (
                  <div className="text-sm text-gray-600 bg-blue-50 p-2 rounded border-l-4 border-blue-200">
                    <strong>Special Requirements:</strong> {ride.special_requirements}
                  </div>
                )}

                {ride.max_wait_time && (
                  <div className="text-xs text-gray-500">Max wait time: {ride.max_wait_time} minutes</div>
                )}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
