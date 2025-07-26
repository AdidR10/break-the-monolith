"use client"

// API Configuration
const API_CONFIG = {
  USER_SERVICE: "http://localhost:8080",
  RIDE_SERVICE: "http://localhost:8081",
  LOCATION_SERVICE: "http://localhost:8082",
  PAYMENT_SERVICE: "http://localhost:8083",
  NOTIFICATION_SERVICE: "http://localhost:8084",
}

// Types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

export interface User {
  id: string
  email: string
  phone: string
  first_name: string
  last_name: string
  user_type: "STUDENT" | "RICKSHAW_DRIVER"
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
}

export interface StudentProfile {
  id: string
  user_id: string
  student_id: string
  department?: string
  batch?: string
  year?: number
  total_rides: number
  is_verified: boolean
  emergency_contact?: string
}

export interface RickshawProfile {
  id: string
  user_id: string
  rickshaw_number: string
  license_number?: string
  is_available: boolean
  current_location?: string
  current_latitude?: number
  current_longitude?: number
  total_rides: number
  rating: number
  rating_count: number
  is_verified: boolean
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  phone: string
  password: string
  first_name: string
  last_name: string
  user_type: "STUDENT" | "RICKSHAW_DRIVER"
  student_id?: string
  department?: string
  batch?: string
  year?: number
  rickshaw_number?: string
  license_number?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
  profile: StudentProfile | RickshawProfile
}

export interface Wallet {
  id: string
  user_id: string
  balance: number
  currency: string
  is_active: boolean
}

export interface Transaction {
  id: string
  ride_id?: string
  amount: number
  transaction_type: "RIDE_PAYMENT" | "WALLET_TOPUP" | "WITHDRAWAL" | "REFUND"
  status: "PENDING" | "COMPLETED" | "FAILED" | "REVERSED"
  description?: string
  created_at: string
}

export interface Ride {
  id: string
  rider_id: string
  driver_id?: string
  pickup_location: string
  pickup_latitude?: number
  pickup_longitude?: number
  drop_location: string
  drop_latitude?: number
  drop_longitude?: number
  status: "REQUESTED" | "ACCEPTED" | "DRIVER_ARRIVED" | "STARTED" | "COMPLETED" | "CANCELLED" | "PAYMENT_PENDING"
  fare_amount?: number
  base_fare?: number
  distance_km?: number
  duration_minutes?: number
  estimated_fare?: number
  requested_at: string
  accepted_at?: string
  driver_arrived_at?: string
  started_at?: string
  ended_at?: string
  cancelled_at?: string
  cancellation_reason?: string
  rider_rating?: number
  driver_rating?: number
  rider_feedback?: string
  driver_feedback?: string
  special_instructions?: string
}

export interface RideRequest {
  id: string
  rider_id: string
  pickup_location: string
  pickup_latitude: number
  pickup_longitude: number
  drop_location: string
  drop_latitude: number
  drop_longitude: number
  estimated_fare?: number
  estimated_distance?: number
  estimated_duration?: number
  max_wait_time?: number
  special_requirements?: string
  expires_at: string
  is_active: boolean
  created_at: string
}

export interface DriverOffer {
  id: string
  ride_request_id: string
  driver_id: string
  offered_fare?: number
  estimated_arrival_time?: number
  message?: string
  expires_at: string
  is_active: boolean
  is_accepted: boolean
  created_at: string
}

export interface FareCalculationRequest {
  pickup_latitude: number
  pickup_longitude: number
  drop_latitude: number
  drop_longitude: number
}

export interface FareCalculationResponse {
  base_fare: number
  distance_km: number
  estimated_duration: number
  total_fare: number
}

export interface Location {
  id: string
  name: string
  latitude: number
  longitude: number
  address?: string
  is_active: boolean
}

// Token Management
class TokenManager {
  private static readonly TOKEN_KEY = "cuet_rickshaw_token"
  private static readonly USER_KEY = "cuet_rickshaw_user"

  static setToken(token: string): void {
    try {
      sessionStorage.setItem(this.TOKEN_KEY, token)
      localStorage.setItem(this.TOKEN_KEY, token)
    } catch (error) {
      console.warn("Failed to store token:", error)
    }
  }

  static getToken(): string | null {
    try {
      return sessionStorage.getItem(this.TOKEN_KEY) || localStorage.getItem(this.TOKEN_KEY)
    } catch (error) {
      console.warn("Failed to retrieve token:", error)
      return null
    }
  }

  static removeToken(): void {
    try {
      sessionStorage.removeItem(this.TOKEN_KEY)
      localStorage.removeItem(this.TOKEN_KEY)
      sessionStorage.removeItem(this.USER_KEY)
      localStorage.removeItem(this.USER_KEY)
    } catch (error) {
      console.warn("Failed to remove token:", error)
    }
  }

  static setUser(user: User, profile: StudentProfile | RickshawProfile): void {
    try {
      const userData = { user, profile }
      const userDataString = JSON.stringify(userData)
      sessionStorage.setItem(this.USER_KEY, userDataString)
      localStorage.setItem(this.USER_KEY, userDataString)
    } catch (error) {
      console.warn("Failed to store user data:", error)
    }
  }

  static getUser(): { user: User; profile: StudentProfile | RickshawProfile } | null {
    try {
      const userData = sessionStorage.getItem(this.USER_KEY) || localStorage.getItem(this.USER_KEY)
      return userData ? JSON.parse(userData) : null
    } catch (error) {
      console.warn("Failed to retrieve user data:", error)
      return null
    }
  }
}

// HTTP Client
class HttpClient {
  private async request<T>(url: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    try {
      const token = TokenManager.getToken()

      const headers: HeadersInit = {
        "Content-Type": "application/json",
        ...options.headers,
      }

      if (token) {
        headers.Authorization = `Bearer ${token}`
      }

      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout

      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      let data: any
      const contentType = response.headers.get("content-type")

      if (contentType && contentType.includes("application/json")) {
        data = await response.json()
      } else {
        data = await response.text()
      }

      if (!response.ok) {
        if (response.status === 401) {
          TokenManager.removeToken()
          // Don't redirect here, let the component handle it
        }

        return {
          success: false,
          error: data?.detail || data?.message || data || `HTTP ${response.status}: ${response.statusText}`,
        }
      }

      return {
        success: true,
        data,
      }
    } catch (error: any) {
      console.error("API Request Error:", error)

      if (error.name === "AbortError") {
        return {
          success: false,
          error: "Request timeout. Please try again.",
        }
      }

      return {
        success: false,
        error: error.message || "Network error occurred. Please check your connection.",
      }
    }
  }

  async get<T>(url: string): Promise<ApiResponse<T>> {
    return this.request<T>(url, { method: "GET" })
  }

  async post<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(url, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async put<T>(url: string, data?: any): Promise<ApiResponse<T>> {
    return this.request<T>(url, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    })
  }

  async delete<T>(url: string): Promise<ApiResponse<T>> {
    return this.request<T>(url, { method: "DELETE" })
  }
}

const httpClient = new HttpClient()

// API Services
export class AuthService {
  static async login(credentials: LoginRequest): Promise<ApiResponse<AuthResponse>> {
    const response = await httpClient.post<AuthResponse>(`${API_CONFIG.USER_SERVICE}/api/v1/auth/login`, credentials)

    if (response.success && response.data) {
      TokenManager.setToken(response.data.access_token)
      TokenManager.setUser(response.data.user, response.data.profile)
    }

    return response
  }

  static async register(userData: RegisterRequest): Promise<ApiResponse<AuthResponse>> {
    const response = await httpClient.post<AuthResponse>(`${API_CONFIG.USER_SERVICE}/api/v1/auth/register`, userData)

    if (response.success && response.data) {
      TokenManager.setToken(response.data.access_token)
      TokenManager.setUser(response.data.user, response.data.profile)
    }

    return response
  }

  static async logout(): Promise<ApiResponse> {
    const response = await httpClient.post(`${API_CONFIG.USER_SERVICE}/api/v1/auth/logout`)
    TokenManager.removeToken()
    return response
  }

  static getCurrentUser(): { user: User; profile: StudentProfile | RickshawProfile } | null {
    return TokenManager.getUser()
  }

  static isAuthenticated(): boolean {
    return !!TokenManager.getToken()
  }
}

export class UserService {
  static async getProfile(): Promise<ApiResponse<{ user: User; profile: StudentProfile | RickshawProfile }>> {
    return httpClient.get(`${API_CONFIG.USER_SERVICE}/api/v1/users/me`)
  }

  static async updateProfile(data: Partial<User>): Promise<ApiResponse<User>> {
    return httpClient.put(`${API_CONFIG.USER_SERVICE}/api/v1/users/me`, data)
  }

  static async updateStudentProfile(data: Partial<StudentProfile>): Promise<ApiResponse<StudentProfile>> {
    return httpClient.put(`${API_CONFIG.USER_SERVICE}/api/v1/student/profile`, data)
  }

  static async updateRickshawProfile(data: Partial<RickshawProfile>): Promise<ApiResponse<RickshawProfile>> {
    return httpClient.put(`${API_CONFIG.USER_SERVICE}/api/v1/rickshaw/profile`, data)
  }

  static async updateAvailability(isAvailable: boolean): Promise<ApiResponse> {
    return httpClient.put(`${API_CONFIG.USER_SERVICE}/api/v1/rickshaw/availability`, { is_available: isAvailable })
  }
}

export class PaymentService {
  static async getWallet(): Promise<ApiResponse<Wallet>> {
    const user = TokenManager.getUser()
    if (!user) {
      return { success: false, error: "User not authenticated" }
    }

    return httpClient.get(`${API_CONFIG.PAYMENT_SERVICE}/api/v1/wallets/${user.user.id}`)
  }

  static async createWallet(): Promise<ApiResponse<Wallet>> {
    return httpClient.post(`${API_CONFIG.PAYMENT_SERVICE}/api/v1/wallets`)
  }

  static async topUpWallet(amount: number): Promise<ApiResponse<Transaction>> {
    const user = TokenManager.getUser()
    if (!user) {
      return { success: false, error: "User not authenticated" }
    }

    return httpClient.post(`${API_CONFIG.PAYMENT_SERVICE}/api/v1/transactions`, {
      to_user_id: user.user.id,
      amount,
      transaction_type: "WALLET_TOPUP",
      description: "Wallet top-up",
    })
  }

  static async getTransactionHistory(): Promise<ApiResponse<Transaction[]>> {
    const user = TokenManager.getUser()
    if (!user) {
      return { success: false, error: "User not authenticated" }
    }

    return httpClient.get(`${API_CONFIG.PAYMENT_SERVICE}/api/v1/transactions/user/${user.user.id}`)
  }
}

export class LocationService {
  static async getLocations(): Promise<ApiResponse<Location[]>> {
    return httpClient.get(`${API_CONFIG.LOCATION_SERVICE}/api/v1/locations`)
  }

  static async createLocation(location: Omit<Location, "id">): Promise<ApiResponse<Location>> {
    return httpClient.post(`${API_CONFIG.LOCATION_SERVICE}/api/v1/locations`, location)
  }

  static async searchLocations(query: string): Promise<ApiResponse<Location[]>> {
    return httpClient.get(`${API_CONFIG.LOCATION_SERVICE}/api/v1/locations/search?q=${encodeURIComponent(query)}`)
  }
}

export class RideService {
  static async calculateFare(request: FareCalculationRequest): Promise<ApiResponse<FareCalculationResponse>> {
    return httpClient.post(`${API_CONFIG.RIDE_SERVICE}/api/v1/fare/calculate`, request)
  }

  static async getNearbyDrivers(
    latitude: number,
    longitude: number,
    radius = 5,
  ): Promise<ApiResponse<RickshawProfile[]>> {
    return httpClient.get(
      `${API_CONFIG.RIDE_SERVICE}/api/v1/drivers/nearby?latitude=${latitude}&longitude=${longitude}&radius=${radius}`,
    )
  }

  static async createRideRequest(request: {
    pickup_location: string
    pickup_latitude: number
    pickup_longitude: number
    drop_location: string
    drop_latitude: number
    drop_longitude: number
    estimated_fare?: number
    special_requirements?: string
  }): Promise<ApiResponse<RideRequest>> {
    return httpClient.post(`${API_CONFIG.RIDE_SERVICE}/api/v1/requests`, request)
  }

  static async getActiveRideRequests(): Promise<ApiResponse<RideRequest[]>> {
    return httpClient.get(`${API_CONFIG.RIDE_SERVICE}/api/v1/requests/active`)
  }

  static async getRideRequest(requestId: string): Promise<ApiResponse<RideRequest>> {
    return httpClient.get(`${API_CONFIG.RIDE_SERVICE}/api/v1/requests/${requestId}`)
  }

  static async createRideOffer(
    requestId: string,
    offer: {
      offered_fare?: number
      estimated_arrival_time?: number
      message?: string
    },
  ): Promise<ApiResponse<DriverOffer>> {
    return httpClient.post(`${API_CONFIG.RIDE_SERVICE}/api/v1/offers`, {
      ride_request_id: requestId,
      ...offer,
    })
  }

  static async acceptRideOffer(offerId: string): Promise<ApiResponse<Ride>> {
    return httpClient.post(`${API_CONFIG.RIDE_SERVICE}/api/v1/offers/${offerId}/accept`)
  }

  static async getMyRides(): Promise<ApiResponse<Ride[]>> {
    return httpClient.get(`${API_CONFIG.RIDE_SERVICE}/api/v1/rides/my`)
  }

  static async getRide(rideId: string): Promise<ApiResponse<Ride>> {
    return httpClient.get(`${API_CONFIG.RIDE_SERVICE}/api/v1/rides/${rideId}`)
  }

  static async updateRideStatus(rideId: string, status: string): Promise<ApiResponse<Ride>> {
    return httpClient.put(`${API_CONFIG.RIDE_SERVICE}/api/v1/rides/${rideId}/status`, { status })
  }

  static async cancelRide(rideId: string, reason: string): Promise<ApiResponse<Ride>> {
    return httpClient.post(`${API_CONFIG.RIDE_SERVICE}/api/v1/rides/${rideId}/cancel`, {
      cancellation_reason: reason,
    })
  }

  static async rateRide(rideId: string, rating: number, feedback?: string): Promise<ApiResponse<Ride>> {
    return httpClient.post(`${API_CONFIG.RIDE_SERVICE}/api/v1/rides/${rideId}/rate`, {
      rating,
      feedback,
    })
  }
}

export class NotificationService {
  static async sendNotification(userId: string, message: string, type?: string): Promise<ApiResponse> {
    return httpClient.post(`${API_CONFIG.NOTIFICATION_SERVICE}/api/v1/notifications`, {
      user_id: userId,
      message,
      type,
    })
  }

  static async getUserNotifications(userId: string): Promise<ApiResponse<any[]>> {
    return httpClient.get(`${API_CONFIG.NOTIFICATION_SERVICE}/api/v1/notifications/${userId}`)
  }

  static async markNotificationAsRead(notificationId: string): Promise<ApiResponse> {
    return httpClient.put(`${API_CONFIG.NOTIFICATION_SERVICE}/api/v1/notifications/${notificationId}/read`)
  }

  static async getNotificationStats(): Promise<ApiResponse<any>> {
    return httpClient.get(`${API_CONFIG.NOTIFICATION_SERVICE}/api/v1/notifications/stats`)
  }
}

export { TokenManager }
