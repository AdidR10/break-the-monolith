"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Wallet, Plus, AlertCircle, Loader2 } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useAppContext } from "@/contexts/app-context"

export default function WalletComponent() {
  const { wallet, topUpWallet, isLoading } = useAppContext()
  const [topupAmount, setTopupAmount] = useState("")
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [error, setError] = useState("")
  const [isProcessing, setIsProcessing] = useState(false)

  const handleTopup = async () => {
    const amount = Number.parseFloat(topupAmount)

    if (isNaN(amount) || amount <= 0) {
      setError("Please enter a valid amount greater than 0")
      return
    }

    if (amount > 10000) {
      setError("Maximum top-up amount is ৳10,000")
      return
    }

    setError("")
    setIsProcessing(true)

    try {
      const result = await topUpWallet(amount)

      if (result.success) {
        setTopupAmount("")
        setIsDialogOpen(false)
      } else {
        setError(result.error || "Top-up failed. Please try again.")
      }
    } catch (error) {
      setError("An unexpected error occurred. Please try again.")
    } finally {
      setIsProcessing(false)
    }
  }

  const handleAmountChange = (value: string) => {
    // Only allow numbers and decimal point
    const sanitized = value.replace(/[^0-9.]/g, "")

    // Prevent multiple decimal points
    const parts = sanitized.split(".")
    if (parts.length > 2) {
      return
    }

    // Limit decimal places to 2
    if (parts[1] && parts[1].length > 2) {
      return
    }

    setTopupAmount(sanitized)
    setError("")
  }

  const quickAmounts = [50, 100, 200, 500, 1000]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wallet className="h-5 w-5 text-green-600" />
          Wallet Balance
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-3xl font-bold text-green-600">৳{wallet ? wallet.balance.toFixed(2) : "0.00"}</p>
            <p className="text-sm text-gray-500">Available Balance</p>
            {wallet && !wallet.is_active && <p className="text-sm text-red-500 mt-1">Wallet is inactive</p>}
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-green-600 hover:bg-green-700" disabled={wallet && !wallet.is_active}>
                <Plus className="h-4 w-4 mr-2" />
                Top Up
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Top Up Wallet</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="amount">Amount (BDT)</Label>
                  <Input
                    id="amount"
                    type="text"
                    placeholder="Enter amount"
                    value={topupAmount}
                    onChange={(e) => handleAmountChange(e.target.value)}
                    disabled={isProcessing}
                  />
                </div>

                {/* Quick amount buttons */}
                <div className="space-y-2">
                  <Label>Quick amounts:</Label>
                  <div className="flex flex-wrap gap-2">
                    {quickAmounts.map((amount) => (
                      <Button
                        key={amount}
                        variant="outline"
                        size="sm"
                        onClick={() => setTopupAmount(amount.toString())}
                        disabled={isProcessing}
                      >
                        ৳{amount}
                      </Button>
                    ))}
                  </div>
                </div>

                <Button onClick={handleTopup} className="w-full" disabled={isProcessing || isLoading || !topupAmount}>
                  {isProcessing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    "Add Money"
                  )}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardContent>
    </Card>
  )
}
