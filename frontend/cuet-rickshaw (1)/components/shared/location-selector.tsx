"use client"

import { useEffect, useState } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { MapPin, RefreshCw, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useAppContext } from "@/contexts/app-context"

// Fallback locations if API fails
const FALLBACK_LOCATIONS = [
  { id: "1", name: "CUET Main Gate", latitude: 22.4625, longitude: 91.9689, address: "CUET Main Gate, Chittagong", is_active: true },
  { id: "2", name: "CUET Library", latitude: 22.4635, longitude: 91.9695, address: "CUET Central Library", is_active: true },
  { id: "3", name: "CUET Cafeteria", latitude: 22.464, longitude: 91.97, address: "CUET Student Cafeteria", is_active: true },
  { id: "4", name: "CUET Residential Area", latitude: 22.462, longitude: 91.968, address: "CUET Student Residential Area", is_active: true },
  { id: "5", name: "CUET Academic Building", latitude: 22.463, longitude: 91.969, address: "CUET Academic Complex", is_active: true },
  { id: "6", name: "Chittagong Medical College", latitude: 22.3569, longitude: 91.7832, address: "Chittagong Medical College Hospital", is_active: true },
  { id: "7", name: "GEC More", latitude: 22.3792, longitude: 91.8159, address: "GEC Circle, Chittagong", is_active: true },
  { id: "8", name: "Agrabad Commercial Area", latitude: 22.3384, longitude: 91.8317, address: "Agrabad Commercial Area", is_active: true },
  { id: "9", name: "New Market", latitude: 22.3384, longitude: 91.8317, address: "New Market, Chittagong", is_active: true },
  { id: "10", name: "Chittagong Railway Station", latitude: 22.3569, longitude: 91.7832, address: "Chittagong Railway Station", is_active: true },
  { id: "11", name: "Shah Amanat International Airport", latitude: 22.2496, longitude: 91.8133, address: "Shah Amanat International Airport", is_active: true },
  { id: "12", name: "Patenga Beach", latitude: 22.2352, longitude: 91.7914, address: "Patenga Sea Beach", is_active: true },
]

interface LocationSelectorProps {
  startLocation: string
  endLocation: string
  onStartLocationChange: (location: string, coords: [number, number]) => void
  onEndLocationChange: (location: string, coords: [number, number]) => void
  disabled?: boolean
}

function LocationInput({
  value,
  onChange,
  placeholder,
  locations,
  label,
  iconColor,
  disabled = false
}: {
  value: string
  onChange: (location: string, coords: [number, number]) => void
  placeholder: string
  locations: any[]
  label: string
  iconColor: string
  disabled?: boolean
}) {
  const [inputValue, setInputValue] = useState(value)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [filteredLocations, setFilteredLocations] = useState(locations)

  useEffect(() => {
    setInputValue(value)
  }, [value])

  useEffect(() => {
    if (inputValue) {
      const filtered = locations.filter((location) =>
        location && location.name && 
        location.name.toLowerCase().includes(inputValue.toLowerCase())
      )
      setFilteredLocations(filtered)
    } else {
      setFilteredLocations(locations.filter(loc => loc && loc.name))
    }
  }, [inputValue, locations])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    setShowSuggestions(true)
    
    // If the input exactly matches a location, auto-select it
    const exactMatch = locations.find((loc) => 
      loc && loc.name && loc.name.toLowerCase() === newValue.toLowerCase()
    )
    if (exactMatch) {
      onChange(newValue, [exactMatch.latitude, exactMatch.longitude])
    }
  }

  const handleSelect = (location: any) => {
    if (location && location.name && location.latitude && location.longitude) {
      setInputValue(location.name)
      onChange(location.name, [location.latitude, location.longitude])
      setShowSuggestions(false)
    }
  }

  const handleFocus = () => {
    setShowSuggestions(true)
  }

  const handleBlur = () => {
    // Delay hiding suggestions to allow for clicks
    setTimeout(() => setShowSuggestions(false), 150)
  }

  return (
    <div className="space-y-2 relative">
      <Label className="flex items-center gap-2">
        <MapPin className={`h-4 w-4 ${iconColor}`} />
        {label}
      </Label>
      <div className="relative">
        <Input
          value={inputValue}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          className="w-full"
        />
        
        {showSuggestions && filteredLocations.length > 0 && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-auto">
            {filteredLocations.map((location) => (
              <button
                key={location.id}
                className="w-full px-3 py-2 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none border-b border-gray-100 last:border-b-0"
                onClick={() => handleSelect(location)}
                type="button"
              >
                <div className="flex items-center gap-2">
                  <MapPin className={`h-3 w-3 ${iconColor}`} />
                  <div className="flex-1">
                    <div className="font-medium text-sm">{location.name}</div>
                    {location.address && (
                      <div className="text-xs text-gray-500">{location.address}</div>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
        
        {showSuggestions && inputValue && filteredLocations.length === 0 && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg p-3">
            <div className="text-sm text-gray-500 text-center">No locations found</div>
          </div>
        )}
      </div>
    </div>
  )
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

  // Use API locations if available, otherwise fallback - ensure always valid
  const availableLocations = Array.isArray(locations) && locations.length > 0 ? locations : FALLBACK_LOCATIONS
  const activeLocations = availableLocations.filter((loc) => loc && loc.is_active && loc.name)

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
          <AlertDescription>
            {error}
            {locations.length === 0 && (
              <Button variant="ghost" size="sm" onClick={handleRefresh} disabled={isRefreshing} className="ml-2">
                <RefreshCw className={`h-3 w-3 ${isRefreshing ? "animate-spin" : ""}`} />
                Retry
              </Button>
            )}
          </AlertDescription>
        </Alert>
      )}

      <LocationInput
        value={startLocation}
        onChange={onStartLocationChange}
        placeholder="Type starting location name (e.g., CUET Main Gate)"
        locations={activeLocations}
        label="From"
        iconColor="text-green-600"
        disabled={disabled}
      />

      <LocationInput
        value={endLocation}
        onChange={onEndLocationChange}
        placeholder="Type destination name (e.g., GEC More)"
        locations={activeLocations}
        label="To"
        iconColor="text-red-600"
        disabled={disabled}
      />

      {startLocation && endLocation && startLocation === endLocation && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Pickup and destination locations cannot be the same.</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
