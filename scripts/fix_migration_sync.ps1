#
# fix_migration_sync.ps1
# Fixes Alembic migration sync issues when database state doesn't match migration history
#
# Usage: .\scripts\fix_migration_sync.ps1 [-DryRun]
#

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Blue }
function Write-Success { param($msg) Write-Host "[SUCCESS] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Check if we're in the right directory
if (-not (Test-Path "alembic.ini")) {
    Write-Error "alembic.ini not found. Please run this script from the project root."
    exit 1
}

# Check/activate virtual environment
if (-not $env:VIRTUAL_ENV) {
    Write-Warn "Virtual environment not activated. Attempting to activate..."
    if (Test-Path "venv\Scripts\Activate.ps1") {
        & .\venv\Scripts\Activate.ps1
    } else {
        Write-Error "Could not find virtual environment. Please activate it manually."
        exit 1
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Alembic Migration Sync Fix Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Warn "DRY RUN MODE - No changes will be made"
    Write-Host ""
}

# Step 1: Show current migration state
Write-Info "Step 1: Checking current migration state..."
Write-Host ""
alembic current
Write-Host ""

# Step 2: Show migration history
Write-Info "Step 2: Showing migration history..."
Write-Host ""
alembic history --indicate-current
Write-Host ""

# Step 3: Check for tables that might already exist
Write-Info "Step 3: Known migrations that may need stamping..."
Write-Host ""

$migrationsToCheck = @(
    @{ Id = "i3j4k5l6m7n8"; Description = "interview_questions table" }
    @{ Id = "j4k5l6m7n8o9"; Description = "industry_category column" }
)

foreach ($migration in $migrationsToCheck) {
    Write-Host "  - $($migration.Id): $($migration.Description)"
}
Write-Host ""

# Step 4: Interactive stamping
Write-Info "Step 4: Migration stamping..."
Write-Host ""

$stampMigrations = Read-Host "Do you need to stamp any migrations? (y/n)"

if ($stampMigrations -eq "y" -or $stampMigrations -eq "Y") {
    Write-Host ""
    Write-Info "Enter migration IDs to stamp (comma-separated, e.g., 'i3j4k5l6m7n8,j4k5l6m7n8o9'):"
    $input = Read-Host "Migration IDs"
    
    if ($input) {
        $stamps = $input -split "," | ForEach-Object { $_.Trim() }
        
        foreach ($stamp in $stamps) {
            if ($stamp) {
                if ($DryRun) {
                    Write-Info "[DRY RUN] Would stamp: $stamp"
                } else {
                    Write-Info "Stamping migration: $stamp"
                    alembic stamp $stamp
                    if ($LASTEXITCODE -eq 0) {
                        Write-Success "Stamped: $stamp"
                    } else {
                        Write-Error "Failed to stamp: $stamp"
                        exit 1
                    }
                }
            }
        }
    }
}
Write-Host ""

# Step 5: Run upgrade
Write-Info "Step 5: Running alembic upgrade head..."
Write-Host ""

if ($DryRun) {
    Write-Info "[DRY RUN] Would run: alembic upgrade head"
    Write-Info "Showing SQL that would be executed:"
    alembic upgrade head --sql 2>$null
} else {
    $proceed = Read-Host "Proceed with 'alembic upgrade head'? (y/n)"
    if ($proceed -eq "y" -or $proceed -eq "Y") {
        alembic upgrade head
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Migrations applied successfully!"
        } else {
            Write-Error "Migration failed!"
            exit 1
        }
    } else {
        Write-Warn "Skipped upgrade. You can run it manually: alembic upgrade head"
    }
}
Write-Host ""

# Step 6: Verify final state
Write-Info "Step 6: Verifying final migration state..."
Write-Host ""
alembic current
Write-Host ""

# Summary
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if ($DryRun) {
    Write-Warn "DRY RUN completed. No changes were made."
} else {
    Write-Success "Migration sync fix completed!"
}

Write-Host ""
Write-Info "Next steps:"
Write-Host "  1. Restart your application"
Write-Host "  2. Test alert creation"
Write-Host "  3. Monitor logs for any errors"
Write-Host ""
