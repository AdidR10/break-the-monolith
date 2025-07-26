"use client"

import { useEffect, useState } from "react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { MapPin, RefreshCw, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useAppContext } from "@/contexts/app-context"

// Fallback locations if API fails
const FALLBACK_LOCATIONS = [
  {
    id: "1",
    name: "CUET Main Gate",
    latitude: 22.4625,
    longitude: 91.9689,
    address: "CUET Main Gate, Chittagong",
    is_active: true,
  },
  {
    id: "2",
    name: "CUET Library",
    latitude: 22.4635,
    longitude: 91.9695,
    address: "CUET Central Library",
    is_active: true,
  },
  {
    id: "3",
    name: "CUET Cafeteria",
    latitude: 22.464,
    longitude: 91.97,
    address: "CUET Student Cafeteria",
    is_active: true,
  },
  {
    id: "4",
    name: "CUET Residential Area",
    latitude: 22.462,
    longitude: 91.968,
    address: "CUET Student Residential Area",
    is_active: true,
  },
  {
    id: "5",
    name: "CUET Academic Building",
    latitude: 22.463,
    longitude: 91.969,
    address: "CUET Academic Complex",
    is_active: true,
  },
  {
    id: "6",
    name: "Chittagong Medical College",
    latitude: 22.3569,
    longitude: 91.7832,
    address: "Chittagong Medical College Hospital",
    is_active: true,
  },
  {
    id: "7",
    name: "GEC More",
    latitude: 22.3792,
    longitude: 91.8159,
    address: "GEC Circle, Chittagong",
    is_active: true,
  },
  {
    id: "8",
    name: "Agrabad Commercial Area",
    latitude: 22.3384,
    longitude: 91.8317,
    address: "Agrabad Commercial Area",
    is_active: true,
  },
  {
    id: "9",
    name: "New Market",
    latitude: 22.3384,
    longitude: 91.8317,
    address: "New Market, Chittagong",
    is_active: true,
  },
  {
    id: "10",
    name: "Chittagong Railway Station",
    latitude: 22.3569,
    longitude: 91.7832,
    address: "Chittagong Railway Station",
    is_active: true,
  },
  {
    id: "11",
    name: "Shah Amanat International Airport",
    latitude: 22.2496,
    longitude: 91.8133,
    address: "Shah Amanat International Airport",
    is_active: true,
  },
  {
    id: "12",
    name: "Patenga Beach",
    latitude: 22.2352,
    longitude: 91.7914,
    address: "Patenga Sea Beach",
    is_active: true,
  },
]

interface LocationSelectorProps {
  startLocation: string
  endLocation: string
  onStartLocationChange: (location: string, coords: [number, number]) => void
  onEndLocationChange: (location: string, coords: [number, number]) => void
  disabled?: boolean
}

export default function LocationSelector({
  startLocation,
  endLocation,
  onStartLocationChange,
  onEndLocationChange,
  disabled = false,
}: LocationSelectorProps) {
  const { locations, refreshLocations, isLoading } = useAppContext()
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (locations.length === 0) {
      loadLocations()
    }
  }, [])

  const loadLocations = async () => {
    try {
      await refreshLocations()
    } catch (error) {
      console.error("Failed to load locations:", error)
      setError("Failed to load locations. Using default locations.")
    }
  }

  const handleRefresh = async () => {
    setIsRefreshing(true)
    setError("")

    try {
      await refreshLocations()
    } catch (error) {
      setError("Failed to refresh locations")
    } finally {
      setIsRefreshing(false)
    }
  }

  // Use API locations if available, otherwise fallback
  const availableLocations = locations.length > 0 ? locations : FALLBACK_LOCATIONS
  const activeLocations = availableLocations.filter((loc) => loc.is_active)

  const handleStartLocationChange = (locationName: string) => {
    const location = activeLocations.find((loc) => loc.name === locationName)
    if (location) {
      onStartLocationChange(locationName, [location.latitude, location.longitude])
    }
  }

  const handleEndLocationChange = (locationName: string) => {
    const location = activeLocations.find((loc) => loc.name === locationName)
    if (location) {
      onEndLocationChange(locationName, [location.latitude, location.longitude])
    }
  }

  if (isLoading && activeLocations.length === 0) {
    return (
      <div className="space-y-4">
        <div className="space-y-2">
          <Label>From</Label>
          <Skeleton className="h-10 w-full" />
        </div>
        <div className="space-y-2">
          <Label>To</Label>
          <Skeleton className="h-10 w-full" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="start-location">From</Label>
          {locations.length === 0 && (
            <Button variant="ghost" size="sm" onClick={handleRefresh} disabled={isRefreshing}>
              <RefreshCw className={`h-3 w-3 ${isRefreshing ? "animate-spin" : ""}`} />
            </Button>
          )}
        </div>
        <Select value={startLocation} onValueChange={handleStartLocationChange} disabled={disabled}>
          <SelectTrigger>
            <SelectValue placeholder="Select starting location" />
          </SelectTrigger>
          <SelectContent>
            {activeLocations.map((location) => (
              <SelectItem key={location.id} value={location.name}>
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-green-600" />
                  <div>
                    <div className="font-medium">{location.name}</div>
                    {location.address && <div className="text-xs text-gray-500">{location.address}</div>}
                  </div>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="end-location">To</Label>
        <Select value={endLocation} onValueChange={handleEndLocationChange} disabled={disabled}>
          <SelectTrigger>
            <SelectValue placeholder="Select destination" />
          </SelectTrigger>
          <SelectContent>
            {activeLocations.map((location) => (
              <SelectItem key={location.id} value={location.name}>
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-red-600" />
                  <div>
                    <div className="font-medium">{location.name}</div>
                    {location.address && <div className="text-xs text-gray-500">{location.address}</div>}
                  </div>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {startLocation && endLocation && startLocation === endLocation && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Pickup and destination locations cannot be the same.</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
