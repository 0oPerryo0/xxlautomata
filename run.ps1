param(
    [Parameter(Position = 0)]
    [ValidateSet("doctor", "launch", "daily", "dump-ui", "screenshot")]
    [string]$Command = "daily",

    [string]$Config = "config.json"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $Config)) {
    Copy-Item "config.example.json" $Config
    Write-Host "Created $Config from config.example.json. Edit it if package auto-detection fails."
}

switch ($Command) {
    "doctor" { python -m xxlwoofia_bot doctor --config $Config }
    "launch" { python -m xxlwoofia_bot launch --config $Config }
    "daily" { python -m xxlwoofia_bot run daily --config $Config }
    "dump-ui" { python -m xxlwoofia_bot dump-ui --config $Config }
    "screenshot" { python -m xxlwoofia_bot screenshot --config $Config }
}
