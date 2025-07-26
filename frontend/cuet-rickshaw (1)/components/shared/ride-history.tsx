"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { History, MapPin, Star, Clock, RefreshCw } from "lucide-react"
import { useAppContext } from "@/contexts/app-context"

export default function RideHistory() {
  const { rides, refreshRides, isLoading } = useAppContext()

  const completedRides = rides
    .filter((ride) => ["COMPLETED", "CANCELLED"].includes(ride.status))
    .sort((a, b) => new Date(b.requested_at).getTime() - new Date(a.requested_at).getTime())

  const getStatusColor = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return "bg-green-100 text-green-800 border-green-200"
      case "CANCELLED":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString)
      return date.toLocaleString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    } catch (error) {
      return dateString
    }
  }

  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime || !endTime) return null

    try {
      const start = new Date(startTime)
      const end = new Date(endTime)
      const diffMs = end.getTime() - start.getTime()
      const diffMins = Math.round(diffMs / (1000 * 60))

      if (diffMins < 60) {
        return `${diffMins} min`
      } else {
        const hours = Math.floor(diffMins / 60)
        const mins = diffMins % 60
        return `${hours}h ${mins}m`
      }
    } catch (error) {
      return null
    }
  }

  const handleRefresh = async () => {
    await refreshRides()
  }

  if (isLoading && rides.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5 text-blue-600" />
            Ride History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="border rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-6 w-20" />
                  <Skeleton className="h-4 w-32" />
                </div>
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-full" />
                </div>
                <div className="flex items-center justify-between">
                  <Skeleton className="h-6 w-16" />
                  <Skeleton className="h-4 w-12" />
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
            <History className="h-5 w-5 text-blue-600" />
            Ride History
          </div>
          <Button variant="ghost" size="sm" onClick={handleRefresh} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {completedRides.length === 0 ? (
            <div className="text-center py-8">
              <History className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No ride history yet</p>
              <p className="text-sm text-gray-400 mt-1">Your completed rides will appear here</p>
            </div>
          ) : (
            completedRides.map((ride) => (
              <div key={ride.id} className="border rounded-lg p-4 space-y-3 hover:shadow-sm transition-shadow">
                <div className="flex items-center justify-between">
                  <Badge className={getStatusColor(ride.status)}>
                    {ride.status.charAt(0).toUpperCase() + ride.status.slice(1)}
                  </Badge>
                  <div className="flex items-center gap-1 text-sm text-gray-500">
                    <Clock className="h-3 w-3" />
                    {formatDate(ride.requested_at)}
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

                <div className="flex items-center justify-between">
                  <span className="font-semibold text-green-600">
                    ৳{Number(ride.fare_amount || ride.estimated_fare || 0).toFixed(2)}
                  </span>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    {ride.distance_km && <span>{ride.distance_km} km</span>}
                    {formatDuration(ride.started_at, ride.ended_at) && (
                      <span>{formatDuration(ride.started_at, ride.ended_at)}</span>
                    )}
                    {(ride.driver_rating || ride.rider_rating) && (
                      <div className="flex items-center gap-1">
                        <Star className="h-4 w-4 text-yellow-500" />
                        <span>{ride.driver_rating || ride.rider_rating}</span>
                      </div>
                    )}
                  </div>
                </div>

                {ride.cancellation_reason && (
                  <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
                    <strong>Cancelled:</strong> {ride.cancellation_reason.replace("_", " ").toLowerCase()}
                  </div>
                )}

                {(ride.rider_feedback || ride.driver_feedback) && (
                  <div className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                    <strong>Feedback:</strong> {ride.rider_feedback || ride.driver_feedback}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
