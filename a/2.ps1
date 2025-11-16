$requestBody = @{
    action = "getDecks"
    version = 6
    params = @{
        cards = @(1712783780711,1712607760452,1712688869426,1712608609451)
    }
} | ConvertTo-Json

(Invoke-RestMethod -Uri http://localhost:8765 -Method Post -Body $requestBody).result