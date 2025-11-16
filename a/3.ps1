$requestBody = @{
    action = "notesInfo"
    version = 6
    params = @{
        notes = @(1712607760449)
    }
} | ConvertTo-Json

(Invoke-RestMethod -Uri http://localhost:8765 -Method Post -Body $requestBody).result
