"use client"

import type React from "react"
import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Car, Users, AlertCircle, Eye, EyeOff } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useAppContext } from "@/contexts/app-context"

interface AuthPageProps {
  onLogin: (type: "user" | "rider") => void
}

interface LoginFormData {
  email: string
  password: string
}

interface RegisterFormData {
  first_name: string
  last_name: string
  email: string
  phone: string
  password: string
  confirmPassword: string
  user_type: string
  student_id: string
  department: string
  batch: string
  year: string
  rickshaw_number: string
  license_number: string
}

export default function AuthPage({ onLogin }: AuthPageProps) {
  const { login, register, isLoading } = useAppContext()
  const [activeTab, setActiveTab] = useState("login")
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [error, setError] = useState("")

  const [loginData, setLoginData] = useState<LoginFormData>({
    email: "",
    password: "",
  })

  const [registerData, setRegisterData] = useState<RegisterFormData>({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    password: "",
    confirmPassword: "",
    user_type: "",
    student_id: "",
    department: "",
    batch: "",
    year: "",
    rickshaw_number: "",
    license_number: "",
  })

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  const validatePhone = (phone: string): boolean => {
    const phoneRegex = /^(\+880|880|0)?1[3-9]\d{8}$/
    return phoneRegex.test(phone.replace(/[\s-]/g, ""))
  }

  const validatePassword = (password: string): boolean => {
    return password.length >= 6
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    // Validation
    if (!loginData.email || !loginData.password) {
      setError("Please fill in all fields")
      return
    }

    if (!validateEmail(loginData.email)) {
      setError("Please enter a valid email address")
      return
    }

    const result = await login(loginData.email, loginData.password)

    if (result.success) {
      // The context will handle setting user type and navigation
      const userData = JSON.parse(sessionStorage.getItem("cuet_rickshaw_user") || "{}")
      const userType = userData.user?.user_type === "STUDENT" ? "user" : "rider"
      onLogin(userType)
    } else {
      setError(result.error || "Login failed")
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    // Validation
    if (
      !registerData.first_name ||
      !registerData.last_name ||
      !registerData.email ||
      !registerData.phone ||
      !registerData.password ||
      !registerData.user_type
    ) {
      setError("Please fill in all required fields")
      return
    }

    if (!validateEmail(registerData.email)) {
      setError("Please enter a valid email address")
      return
    }

    if (!validatePhone(registerData.phone)) {
      setError("Please enter a valid phone number")
      return
    }

    if (!validatePassword(registerData.password)) {
      setError("Password must be at least 6 characters long")
      return
    }

    if (registerData.password !== registerData.confirmPassword) {
      setError("Passwords do not match")
      return
    }

    // User type specific validation
    if (registerData.user_type === "STUDENT" && !registerData.student_id) {
      setError("Student ID is required for students")
      return
    }

    if (registerData.user_type === "RICKSHAW_DRIVER" && !registerData.rickshaw_number) {
      setError("Rickshaw number is required for drivers")
      return
    }

    // Prepare registration data
    const userData = {
      first_name: registerData.first_name.trim(),
      last_name: registerData.last_name.trim(),
      email: registerData.email.trim().toLowerCase(),
      phone: registerData.phone.replace(/[\s-]/g, ""),
      password: registerData.password,
      user_type: registerData.user_type as "STUDENT" | "RICKSHAW_DRIVER",
      ...(registerData.user_type === "STUDENT" && {
        student_id: registerData.student_id.trim(),
        department: registerData.department.trim() || undefined,
        batch: registerData.batch.trim() || undefined,
        year: registerData.year ? Number.parseInt(registerData.year) : undefined,
      }),
      ...(registerData.user_type === "RICKSHAW_DRIVER" && {
        rickshaw_number: registerData.rickshaw_number.trim(),
        license_number: registerData.license_number.trim() || undefined,
      }),
    }

    const result = await register(userData)

    if (result.success) {
      const userType = registerData.user_type === "STUDENT" ? "user" : "rider"
      onLogin(userType)
    } else {
      setError(result.error || "Registration failed")
    }
  }

  const resetForm = () => {
    setError("")
    setLoginData({ email: "", password: "" })
    setRegisterData({
      first_name: "",
      last_name: "",
      email: "",
      phone: "",
      password: "",
      confirmPassword: "",
      user_type: "",
      student_id: "",
      department: "",
      batch: "",
      year: "",
      rickshaw_number: "",
      license_number: "",
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <Car className="h-8 w-8 text-blue-600" />
            <CardTitle className="text-2xl font-bold text-blue-800">CUET Rickshaw</CardTitle>
          </div>
          <CardDescription>Your campus ride sharing solution</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <Tabs
            value={activeTab}
            onValueChange={(value) => {
              setActiveTab(value)
              resetForm()
            }}
            className="w-full"
          >
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Login</TabsTrigger>
              <TabsTrigger value="register">Register</TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="login-email">Email</Label>
                  <Input
                    id="login-email"
                    type="email"
                    placeholder="your.email@cuet.ac.bd"
                    value={loginData.email}
                    onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                    required
                    autoComplete="email"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="login-password">Password</Label>
                  <div className="relative">
                    <Input
                      id="login-password"
                      type={showPassword ? "text" : "password"}
                      value={loginData.password}
                      onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                      required
                      autoComplete="current-password"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
                <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700" disabled={isLoading}>
                  {isLoading ? "Logging in..." : "Login"}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="register">
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-2">
                    <Label htmlFor="register-firstname">First Name *</Label>
                    <Input
                      id="register-firstname"
                      placeholder="John"
                      value={registerData.first_name}
                      onChange={(e) => setRegisterData({ ...registerData, first_name: e.target.value })}
                      required
                      autoComplete="given-name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-lastname">Last Name *</Label>
                    <Input
                      id="register-lastname"
                      placeholder="Doe"
                      value={registerData.last_name}
                      onChange={(e) => setRegisterData({ ...registerData, last_name: e.target.value })}
                      required
                      autoComplete="family-name"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-email">Email *</Label>
                  <Input
                    id="register-email"
                    type="email"
                    placeholder="your.email@cuet.ac.bd"
                    value={registerData.email}
                    onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
                    required
                    autoComplete="email"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-phone">Phone Number *</Label>
                  <Input
                    id="register-phone"
                    placeholder="+880 1712-345678"
                    value={registerData.phone}
                    onChange={(e) => setRegisterData({ ...registerData, phone: e.target.value })}
                    required
                    autoComplete="tel"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-password">Password *</Label>
                  <div className="relative">
                    <Input
                      id="register-password"
                      type={showPassword ? "text" : "password"}
                      value={registerData.password}
                      onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
                      required
                      autoComplete="new-password"
                      minLength={6}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-confirm-password">Confirm Password *</Label>
                  <div className="relative">
                    <Input
                      id="register-confirm-password"
                      type={showConfirmPassword ? "text" : "password"}
                      value={registerData.confirmPassword}
                      onChange={(e) => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
                      required
                      autoComplete="new-password"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="register-usertype">I am a *</Label>
                  <Select onValueChange={(value) => setRegisterData({ ...registerData, user_type: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select your role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="STUDENT">
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4" />
                          Student
                        </div>
                      </SelectItem>
                      <SelectItem value="RICKSHAW_DRIVER">
                        <div className="flex items-center gap-2">
                          <Car className="h-4 w-4" />
                          Rickshaw Driver
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Student-specific fields */}
                {registerData.user_type === "STUDENT" && (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="student-id">Student ID *</Label>
                      <Input
                        id="student-id"
                        placeholder="1904001"
                        value={registerData.student_id}
                        onChange={(e) => setRegisterData({ ...registerData, student_id: e.target.value })}
                        required
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="space-y-2">
                        <Label htmlFor="department">Department</Label>
                        <Input
                          id="department"
                          placeholder="CSE"
                          value={registerData.department}
                          onChange={(e) => setRegisterData({ ...registerData, department: e.target.value })}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="batch">Batch</Label>
                        <Input
                          id="batch"
                          placeholder="19"
                          value={registerData.batch}
                          onChange={(e) => setRegisterData({ ...registerData, batch: e.target.value })}
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="year">Year</Label>
                      <Input
                        id="year"
                        type="number"
                        placeholder="2019"
                        min="2000"
                        max="2030"
                        value={registerData.year}
                        onChange={(e) => setRegisterData({ ...registerData, year: e.target.value })}
                      />
                    </div>
                  </>
                )}

                {/* Rickshaw driver-specific fields */}
                {registerData.user_type === "RICKSHAW_DRIVER" && (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="rickshaw-number">Rickshaw Number *</Label>
                      <Input
                        id="rickshaw-number"
                        placeholder="CTG-1234"
                        value={registerData.rickshaw_number}
                        onChange={(e) => setRegisterData({ ...registerData, rickshaw_number: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="license-number">License Number</Label>
                      <Input
                        id="license-number"
                        placeholder="DL123456789"
                        value={registerData.license_number}
                        onChange={(e) => setRegisterData({ ...registerData, license_number: e.target.value })}
                      />
                    </div>
                  </>
                )}

                <Button type="submit" className="w-full bg-green-600 hover:bg-green-700" disabled={isLoading}>
                  {isLoading ? "Registering..." : "Register"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
