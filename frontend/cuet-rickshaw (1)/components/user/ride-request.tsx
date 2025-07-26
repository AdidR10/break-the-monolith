"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { AlertCircle, Calculator, Navigation, Loader2 } from "lucide-react"
import LocationSelector from "@/components/shared/location-selector"
import { useAppContext } from "@/contexts/app-context"
import { RideService } from "@/lib/api-client"

export default function RideRequest() {
  const { createRideRequest, wallet, isLoading } = useAppContext()
  const [startLocation, setStartLocation] = useState("")
  const [endLocation, setEndLocation] = useState("")
  const [startCoords, setStartCoords] = useState<[number, number] | null>(null)
  const [endCoords, setEndCoords] = useState<[number, number] | null>(null)
  const [fare, setFare] = useState<{
    base_fare: number
    distance_km: number
    estimated_duration: number
    total_fare: number
  } | null>(null)
  const [error, setError] = useState("")
  const [isCalculating, setIsCalculating] = useState(false)
  const [isRequesting, setIsRequesting] = useState(false)

  const handleStartLocationChange = (location: string, coords: [number, number]) => {
    setStartLocation(location)
    setStartCoords(coords)
    setFare(null) // Reset fare when location changes
    setError("")
  }

  const handleEndLocationChange = (location: string, coords: [number, number]) => {
    setEndLocation(location)
    setEndCoords(coords)
    setFare(null) // Reset fare when location changes
    setError("")
  }

  const handleCalculateFare = async () => {
    if (!startCoords || !endCoords) {
      setError("Please select both pickup and drop locations")
      return
    }

    if (startLocation === endLocation) {
      setError("Pickup and drop locations cannot be the same")
      return
    }

    setIsCalculating(true)
    setError("")

    try {
      const response = await RideService.calculateFare({
        pickup_latitude: startCoords[0],
        pickup_longitude: startCoords[1],
        drop_latitude: endCoords[0],
        drop_longitude: endCoords[1],
      })

      if (response.success && response.data) {
        setFare(response.data)
      } else {
        setError(response.error || "Failed to calculate fare. Please try again.")
      }
    } catch (error) {
      setError("Failed to calculate fare. Please try again.")
    } finally {
      setIsCalculating(false)
    }
  }

  const handleRequestRide = async () => {
    if (!startLocation || !endLocation || !startCoords || !endCoords || !fare) {
      setError("Please complete all fields and calculate fare first")
      return
    }

    if (!wallet || wallet.balance < fare.total_fare) {
      setError("Insufficient wallet balance. Please top up your wallet.")
      return
    }

    setError("")
    setIsRequesting(true)

    try {
      const result = await createRideRequest(startLocation, endLocation, startCoords, endCoords)

      if (result.success) {
        // Reset form
        setStartLocation("")
        setEndLocation("")
        setStartCoords(null)
        setEndCoords(null)
        setFare(null)
      } else {
        setError(result.error || "Failed to create ride request. Please try again.")
      }
    } catch (error) {
      setError("An unexpected error occurred. Please try again.")
    } finally {
      setIsRequesting(false)
    }
  }

  const canCalculateFare = startLocation && endLocation && startLocation !== endLocation && startCoords && endCoords
  const canRequestRide = fare && wallet && wallet.balance >= fare.total_fare

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <LocationSelector
        startLocation={startLocation}
        endLocation={endLocation}
        onStartLocationChange={handleStartLocationChange}
        onEndLocationChange={handleEndLocationChange}
        disabled={isRequesting}
      />

      {canCalculateFare && !fare && (
        <Button
          onClick={handleCalculateFare}
          variant="outline"
          className="w-full bg-transparent"
          disabled={isCalculating}
        >
          {isCalculating ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Calculating...
            </>
          ) : (
            <>
              <Calculator className="h-4 w-4 mr-2" />
              Calculate Fare
            </>
          )}
        </Button>
      )}

      {isCalculating && (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center space-y-3">
              <Skeleton className="h-8 w-32 mx-auto" />
              <Skeleton className="h-4 w-48 mx-auto" />
              <Skeleton className="h-10 w-full" />
            </div>
          </CardContent>
        </Card>
      )}

      {fare && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-2">Estimated Fare</p>
                <p className="text-3xl font-bold text-green-600">৳{fare.total_fare.toFixed(2)}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-gray-600">Distance</p>
                  <p className="font-semibold">{fare.distance_km.toFixed(1)} km</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-gray-600">Duration</p>
                  <p className="font-semibold">{fare.estimated_duration} min</p>
                </div>
              </div>

              <div className="text-xs text-gray-500 space-y-1">
                <div className="flex justify-between">
                  <span>Base fare:</span>
                  <span>৳{fare.base_fare.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Distance charge:</span>
                  <span>৳{(fare.total_fare - fare.base_fare).toFixed(2)}</span>
                </div>
              </div>

              {wallet && wallet.balance < fare.total_fare && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Insufficient balance. You need ৳{(fare.total_fare - wallet.balance).toFixed(2)} more.
                  </AlertDescription>
                </Alert>
              )}

              <Button
                onClick={handleRequestRide}
                className="w-full bg-blue-600 hover:bg-blue-700"
                disabled={!canRequestRide || isRequesting || isLoading}
              >
                {isRequesting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Requesting Ride...
                  </>
                ) : (
                  <>
                    <Navigation className="h-4 w-4 mr-2" />
                    Request Ride
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
