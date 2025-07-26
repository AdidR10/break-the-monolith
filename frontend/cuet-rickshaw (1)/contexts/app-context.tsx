"use client"

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react"
import {
  AuthService,
  PaymentService,
  RideService,
  LocationService,
  type User,
  type StudentProfile,
  type RickshawProfile,
  type Wallet,
  type Ride,
  type Location,
} from "@/lib/api-client"

interface AppContextType {
  // Auth
  user: User | null
  profile: StudentProfile | RickshawProfile | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>
  register: (userData: any) => Promise<{ success: boolean; error?: string }>
  logout: () => Promise<void>

  // Wallet
  wallet: Wallet | null
  topUpWallet: (amount: number) => Promise<{ success: boolean; error?: string }>
  refreshWallet: () => Promise<void>

  // Rides
  rides: Ride[]
  activeRide: Ride | null
  refreshRides: () => Promise<void>
  createRideRequest: (
    pickup: string,
    dropoff: string,
    pickupCoords: [number, number],
    dropoffCoords: [number, number],
  ) => Promise<{ success: boolean; error?: string }>

  // Locations
  locations: Location[]
  refreshLocations: () => Promise<void>

  // Loading states
  isLoading: boolean
  setIsLoading: (loading: boolean) => void

  // Error handling
  error: string | null
  clearError: () => void
}

const AppContext = createContext<AppContextType | undefined>(undefined)

export function AppProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [profile, setProfile] = useState<StudentProfile | RickshawProfile | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [wallet, setWallet] = useState<Wallet | null>(null)
  const [rides, setRides] = useState<Ride[]>([])
  const [locations, setLocations] = useState<Location[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isClient, setIsClient] = useState(false)

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  // Check if we're on the client side
  useEffect(() => {
    setIsClient(true)
  }, [])

  const refreshWallet = useCallback(async (): Promise<void> => {
    try {
      const response = await PaymentService.getWallet()
      if (response.success && response.data) {
        setWallet(response.data)
      } else if (response.error && !response.error.includes("not found")) {
        console.error("Error refreshing wallet:", response.error)
      }
    } catch (error) {
      console.error("Error refreshing wallet:", error)
    }
  }, [])

  const refreshRides = useCallback(async (): Promise<void> => {
    try {
      const response = await RideService.getMyRides()
      if (response.success && response.data && Array.isArray(response.data)) {
        setRides(response.data)
      } else if (response.error) {
        console.error("Error refreshing rides:", response.error)
      }
    } catch (error) {
      console.error("Error refreshing rides:", error)
    }
  }, [])

  const refreshLocations = useCallback(async (): Promise<void> => {
    try {
      const response = await LocationService.getLocations()
      if (response.success && response.data && Array.isArray(response.data)) {
        setLocations(response.data)
      } else if (response.error) {
        console.error("Error refreshing locations:", response.error)
      }
    } catch (error) {
      console.error("Error refreshing locations:", error)
    }
  }, [])

  // Initialize auth state only on client side
  useEffect(() => {
    if (!isClient) return

    const initializeAuth = async () => {
      try {
        const userData = AuthService.getCurrentUser()
        if (userData && AuthService.isAuthenticated()) {
          setUser(userData.user)
          setProfile(userData.profile)
          setIsAuthenticated(true)

          // Load initial data in parallel
          await Promise.allSettled([refreshWallet(), refreshRides(), refreshLocations()])
        }
      } catch (error) {
        console.error("Auth initialization error:", error)
        setError("Failed to initialize authentication")
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [isClient, refreshWallet, refreshRides, refreshLocations])

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await AuthService.login({ email, password })

      if (response.success && response.data) {
        setUser(response.data.user)
        setProfile(response.data.profile)
        setIsAuthenticated(true)

        // Load user data in parallel
        await Promise.allSettled([refreshWallet(), refreshRides(), refreshLocations()])

        return { success: true }
      }

      return { success: false, error: response.error || "Login failed" }
    } catch (error: any) {
      console.error("Login error:", error)
      return { success: false, error: error.message || "Login failed" }
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (userData: any): Promise<{ success: boolean; error?: string }> => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await AuthService.register(userData)

      if (response.success && response.data) {
        setUser(response.data.user)
        setProfile(response.data.profile)
        setIsAuthenticated(true)

        // Create wallet for new user
        try {
          await PaymentService.createWallet()
        } catch (walletError) {
          console.warn("Failed to create wallet:", walletError)
        }

        // Load user data in parallel
        await Promise.allSettled([refreshWallet(), refreshRides(), refreshLocations()])

        return { success: true }
      }

      return { success: false, error: response.error || "Registration failed" }
    } catch (error: any) {
      console.error("Registration error:", error)
      return { success: false, error: error.message || "Registration failed" }
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async (): Promise<void> => {
    setIsLoading(true)

    try {
      await AuthService.logout()
    } catch (error) {
      console.error("Logout error:", error)
    } finally {
      // Clear all state regardless of API response
      setUser(null)
      setProfile(null)
      setIsAuthenticated(false)
      setWallet(null)
      setRides([])
      setError(null)
      setIsLoading(false)
    }
  }

  const topUpWallet = async (amount: number): Promise<{ success: boolean; error?: string }> => {
    if (amount <= 0) {
      return { success: false, error: "Amount must be greater than 0" }
    }

    setIsLoading(true)

    try {
      const response = await PaymentService.topUpWallet(amount)

      if (response.success) {
        await refreshWallet()
        return { success: true }
      }

      return { success: false, error: response.error || "Top-up failed" }
    } catch (error: any) {
      console.error("Top-up error:", error)
      return { success: false, error: error.message || "Top-up failed" }
    } finally {
      setIsLoading(false)
    }
  }

  const createRideRequest = async (
    pickup: string,
    dropoff: string,
    pickupCoords: [number, number],
    dropoffCoords: [number, number],
  ): Promise<{ success: boolean; error?: string }> => {
    if (!pickup || !dropoff) {
      return { success: false, error: "Please select pickup and drop-off locations" }
    }

    if (pickup === dropoff) {
      return { success: false, error: "Pickup and drop-off locations cannot be the same" }
    }

    setIsLoading(true)

    try {
      // First calculate fare
      const fareResponse = await RideService.calculateFare({
        pickup_latitude: pickupCoords[0],
        pickup_longitude: pickupCoords[1],
        drop_latitude: dropoffCoords[0],
        drop_longitude: dropoffCoords[1],
      })

      if (!fareResponse.success || !fareResponse.data) {
        return { success: false, error: fareResponse.error || "Failed to calculate fare" }
      }

      // Check wallet balance
      if (wallet && wallet.balance < fareResponse.data.total_fare) {
        return { success: false, error: "Insufficient wallet balance. Please top up your wallet." }
      }

      // Create ride request
      const requestResponse = await RideService.createRideRequest({
        pickup_location: pickup,
        pickup_latitude: pickupCoords[0],
        pickup_longitude: pickupCoords[1],
        drop_location: dropoff,
        drop_latitude: dropoffCoords[0],
        drop_longitude: dropoffCoords[1],
        estimated_fare: fareResponse.data.total_fare,
      })

      if (requestResponse.success) {
        await refreshRides()
        return { success: true }
      }

      return { success: false, error: requestResponse.error || "Failed to create ride request" }
    } catch (error: any) {
      console.error("Create ride request error:", error)
      return { success: false, error: error.message || "Failed to create ride request" }
    } finally {
      setIsLoading(false)
    }
  }

  // Get active ride - with defensive programming
  const activeRide = Array.isArray(rides) 
    ? rides.find((ride) => ["REQUESTED", "ACCEPTED", "DRIVER_ARRIVED", "STARTED"].includes(ride.status)) || null
    : null

  const contextValue: AppContextType = {
    user,
    profile,
    isAuthenticated,
    login,
    register,
    logout,
    wallet,
    topUpWallet,
    refreshWallet,
    rides,
    activeRide,
    refreshRides,
    createRideRequest,
    locations,
    refreshLocations,
    isLoading,
    setIsLoading,
    error,
    clearError,
  }

  return <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>
}

export function useAppContext() {
  const context = useContext(AppContext)
  if (context === undefined) {
    throw new Error("useAppContext must be used within an AppProvider")
  }
  return context
}
