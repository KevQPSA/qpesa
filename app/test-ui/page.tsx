"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export default function TestUI() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [response, setResponse] = useState<string | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleApiCall = async (endpoint: string, method = "GET", body?: any) => {
    setLoading(true)
    setResponse(null)
    try {
      const headers: HeadersInit = {
        "Content-Type": "application/json",
      }
      if (token) {
        headers["Authorization"] = `Bearer ${token}`
      }

      const res = await fetch(`${BACKEND_URL}${endpoint}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      })

      const data = await res.json()
      setResponse(JSON.stringify(data, null, 2))

      if (endpoint === "/api/v1/auth/login" && data.access_token) {
        setToken(data.access_token)
      }
    } catch (error: any) {
      setResponse(`Error: ${error.message || "An unknown error occurred"}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-4xl font-bold mb-8 text-center">Backend Test UI</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
        {/* Health & Readiness */}
        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Button onClick={() => handleApiCall("/health")} disabled={loading}>
              {loading ? "Loading..." : "Check Health"}
            </Button>
            <Button onClick={() => handleApiCall("/ready")} disabled={loading}>
              {loading ? "Loading..." : "Check Readiness"}
            </Button>
          </CardContent>
        </Card>

        {/* Registration */}
        <Card>
          <CardHeader>
            <CardTitle>Register User</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div>
              <Label htmlFor="register-email">Email</Label>
              <Input
                id="register-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
              />
            </div>
            <div>
              <Label htmlFor="register-password">Password</Label>
              <Input
                id="register-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="password"
              />
            </div>
            <Button
              onClick={() => handleApiCall("/api/v1/auth/register", "POST", { email, password, user_type: "personal" })}
              disabled={loading || !email || !password}
            >
              {loading ? "Loading..." : "Register Personal User"}
            </Button>
            <Button
              onClick={() => handleApiCall("/api/v1/auth/register", "POST", { email, password, user_type: "merchant" })}
              disabled={loading || !email || !password}
            >
              {loading ? "Loading..." : "Register Merchant User"}
            </Button>
          </CardContent>
        </Card>

        {/* Login */}
        <Card>
          <CardHeader>
            <CardTitle>Login User</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div>
              <Label htmlFor="login-email">Email</Label>
              <Input
                id="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="user@example.com"
              />
            </div>
            <div>
              <Label htmlFor="login-password">Password</Label>
              <Input
                id="login-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="password"
              />
            </div>
            <Button
              onClick={() => handleApiCall("/api/v1/auth/login", "POST", { username: email, password })}
              disabled={loading || !email || !password}
            >
              {loading ? "Loading..." : "Login"}
            </Button>
            {token && (
              <div className="text-sm text-green-600 break-all">
                Logged in! Token: <span className="font-mono text-xs">{token.substring(0, 30)}...</span>
              </div>
            )}
            <Button onClick={() => setToken(null)} variant="outline" disabled={!token}>
              Clear Token
            </Button>
          </CardContent>
        </Card>

        {/* Example Authenticated Endpoint (Placeholder) */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Authenticated Endpoint (Example)</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">
              This button will attempt to call an authenticated endpoint. You must be logged in for it to succeed.
              (Replace `/api/v1/wallets/me` with an actual endpoint once implemented).
            </p>
            <Button onClick={() => handleApiCall("/api/v1/wallets/me", "GET")} disabled={loading || !token}>
              {loading ? "Loading..." : "Fetch My Wallet (Requires Login)"}
            </Button>
          </CardContent>
        </Card>

        {/* API Response Display */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>API Response</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              readOnly
              value={response || "No response yet."}
              className="min-h-[200px] font-mono text-sm bg-gray-50"
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
