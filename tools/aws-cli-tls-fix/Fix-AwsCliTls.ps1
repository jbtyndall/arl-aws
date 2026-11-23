<#
.SYNOPSIS
Fixes AWS CLI "self-signed certificate in certificate chain" errors caused by ARL TLS inspection.

.DESCRIPTION
ARL's firewall re-signs HTTPS traffic to AWS with ARL's own certificate authority. Windows already
trusts that authority, but AWS CLI v2 ships its own CA list and ignores the Windows certificate
store. Every call then fails with CERTIFICATE_VERIFY_FAILED.

This script:
  1. Finds the ARL Root CA in the Windows certificate stores (valid, unexpired certificates only).
  2. Builds a CA bundle made of the AWS CLI's own CA list plus the ARL Root CA.
  3. Sets the user-level AWS_CA_BUNDLE environment variable to that bundle.
  4. Tests TLS against the GovCloud and commercial STS endpoints.

TLS verification stays on. The script never disables certificate checking. It needs no
administrator rights and changes nothing outside the current user's profile. Because the bundle
keeps the AWS CLI's normal CA list, the CLI also keeps working off the ARL network.

Re-run it after the AWS CLI is upgraded or after the ARL root certificate is replaced.

.PARAMETER CertificateSubjectPattern
Text matched against certificate subjects in the Windows Trusted Root stores. Default: CN=ARL Root CA

.PARAMETER BundlePath
Where to write the combined CA bundle. Default: %USERPROFILE%\.aws\ca-bundle.pem

.PARAMETER AwsCliBundlePath
Path to the AWS CLI's own cacert.pem. Detected automatically when omitted.

.PARAMETER SkipEnvironmentVariable
Build and test the bundle but do not set AWS_CA_BUNDLE.

.PARAMETER Force
Overwrite a user-level AWS_CA_BUNDLE that already points somewhere else.

.EXAMPLE
.\Fix-AwsCliTls.ps1

Builds the bundle, sets AWS_CA_BUNDLE, and tests TLS.

.EXAMPLE
.\Fix-AwsCliTls.ps1 -WhatIf

Shows what would change without writing anything.

.OUTPUTS
None. Writes progress to the console and to fix-awscli-tls.log next to the bundle.
Exit code 0 on success, 1 on failure.

.NOTES
Supports AWS CLI v2 on Windows. Open terminals must be restarted to pick up AWS_CA_BUNDLE.
To undo: [Environment]::SetEnvironmentVariable('AWS_CA_BUNDLE', $null, 'User'), then delete the bundle file.
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$CertificateSubjectPattern = 'CN=ARL Root CA',
    [string]$BundlePath = (Join-Path $env:USERPROFILE '.aws\ca-bundle.pem'),
    [string]$AwsCliBundlePath,
    [switch]$SkipEnvironmentVariable,
    [switch]$Force
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:LogPath = Join-Path (Split-Path -Parent $BundlePath) 'fix-awscli-tls.log'

<#
.SYNOPSIS
Writes a timestamped message to the console and the log file.
.PARAMETER Level
INFO, WARN, or ERROR.
.PARAMETER Message
The text to log.
#>
function Write-LogMessage {
    param(
        [Parameter(Mandatory)][ValidateSet('INFO', 'WARN', 'ERROR')][string]$Level,
        [Parameter(Mandatory)][string]$Message
    )
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $line = "[$timestamp] [$Level]" + (' ' * (6 - $Level.Length)) + $Message
    $color = @{ INFO = 'Gray'; WARN = 'Yellow'; ERROR = 'Red' }[$Level]
    Write-Host $line -ForegroundColor $color
    if (-not $WhatIfPreference) {
        try {
            $logDirectory = Split-Path -Parent $script:LogPath
            if (-not (Test-Path -LiteralPath $logDirectory)) { New-Item -ItemType Directory -Path $logDirectory | Out-Null }
            Add-Content -LiteralPath $script:LogPath -Value $line
        }
        catch {
            Write-Host "Could not write to log file: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

<#
.SYNOPSIS
Locates the AWS CLI v2's built-in CA list (cacert.pem).
.PARAMETER OverridePath
Explicit path to use before the default locations.
.OUTPUTS
System.String. Full path to cacert.pem.
.EXCEPTION
Throws when the file cannot be found.
#>
function Get-AwsCliCaListPath {
    param([string]$OverridePath)
    $relativePath = 'awscli\botocore\cacert.pem'
    $candidates = @()
    if ($OverridePath) { $candidates += $OverridePath }
    $candidates += (Join-Path $env:ProgramFiles ('Amazon\AWSCLIV2\' + $relativePath))
    $awsCommand = Get-Command aws -ErrorAction SilentlyContinue
    if ($awsCommand) { $candidates += (Join-Path (Split-Path -Parent $awsCommand.Source) $relativePath) }
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    throw "Could not find the AWS CLI v2 CA list (cacert.pem). Is AWS CLI v2 installed? Checked: $($candidates -join '; ')"
}

<#
.SYNOPSIS
Finds valid, unexpired certificates in the Windows Trusted Root stores that match a subject pattern.
.PARAMETER SubjectPattern
Text to match against the certificate subject.
.OUTPUTS
System.Security.Cryptography.X509Certificates.X509Certificate2[]. Duplicates (same thumbprint) are removed.
.EXCEPTION
Throws when no valid certificate matches.
#>
function Get-MatchingRootCertificate {
    param([Parameter(Mandatory)][string]$SubjectPattern)
    $now = Get-Date
    $found = @{}
    foreach ($location in 'LocalMachine', 'CurrentUser') {
        $store = New-Object System.Security.Cryptography.X509Certificates.X509Store('Root', $location)
        try {
            $store.Open('ReadOnly')
            foreach ($certificate in $store.Certificates) {
                $isMatch = $certificate.Subject -like "*$SubjectPattern*"
                $isValidNow = ($certificate.NotBefore -lt $now) -and ($certificate.NotAfter -gt $now)
                if ($isMatch -and $isValidNow) { $found[$certificate.Thumbprint] = $certificate }
            }
        }
        finally { $store.Close() }
    }
    if ($found.Count -eq 0) {
        throw "No valid certificate matching '$SubjectPattern' found in the Windows Trusted Root stores. Is this machine managed by ARL ITS?"
    }
    return @($found.Values)
}

<#
.SYNOPSIS
Converts a certificate to PEM text.
.PARAMETER Certificate
The certificate to convert.
.OUTPUTS
System.String. PEM-encoded certificate with LF line endings.
#>
function ConvertTo-PemText {
    param([Parameter(Mandatory)][System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate)
    $base64 = [Convert]::ToBase64String($Certificate.RawData)
    $lines = [regex]::Matches($base64, '.{1,64}') | ForEach-Object { $_.Value }
    return "-----BEGIN CERTIFICATE-----`n" + ($lines -join "`n") + "`n-----END CERTIFICATE-----"
}

<#
.SYNOPSIS
Tests TLS to AWS STS endpoints using a CA bundle, without needing credentials.
.DESCRIPTION
Sends an unsigned request. AWS rejects it with an authentication error, which proves the TLS
handshake succeeded. Only SSL validation errors count as failures.
.PARAMETER CaBundlePath
CA bundle to use for the test.
.OUTPUTS
System.Boolean. True when all reachable endpoints passed, False when any failed TLS validation,
and $null when the test could not run.
#>
function Test-AwsTlsConnection {
    param([Parameter(Mandatory)][string]$CaBundlePath)
    if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
        Write-LogMessage -Level WARN -Message 'The aws command is not on PATH. Skipping the connection test.'
        return $null
    }
    $previousBundle = $env:AWS_CA_BUNDLE
    $previousPreference = $ErrorActionPreference
    $env:AWS_CA_BUNDLE = $CaBundlePath
    $ErrorActionPreference = 'Continue'
    $allPassed = $true
    try {
        foreach ($region in 'us-gov-west-1', 'us-east-1') {
            $output = (& aws sts get-caller-identity --no-sign-request --region $region 2>&1 | Out-String).Trim()
            if ($output -match 'SSL validation failed|CERTIFICATE_VERIFY_FAILED') {
                Write-LogMessage -Level ERROR -Message "TLS validation FAILED for sts.$region.amazonaws.com."
                $allPassed = $false
            }
            elseif ($output -match 'Could not connect|timed out|Connect timeout') {
                Write-LogMessage -Level WARN -Message "Could not reach sts.$region.amazonaws.com (network issue, not a certificate issue)."
            }
            else {
                Write-LogMessage -Level INFO -Message "TLS validation OK for sts.$region.amazonaws.com."
            }
        }
    }
    finally {
        $ErrorActionPreference = $previousPreference
        $env:AWS_CA_BUNDLE = $previousBundle
    }
    return $allPassed
}

try {
    Write-LogMessage -Level INFO -Message "Starting AWS CLI TLS fix. User=$env:USERNAME Computer=$env:COMPUTERNAME"

    $cliCaListPath = Get-AwsCliCaListPath -OverridePath $AwsCliBundlePath
    $certificates = @(Get-MatchingRootCertificate -SubjectPattern $CertificateSubjectPattern)
    foreach ($certificate in $certificates) {
        Write-LogMessage -Level INFO -Message "Found certificate. Subject=$($certificate.Subject) Thumbprint=$($certificate.Thumbprint) Expires=$($certificate.NotAfter.ToString('yyyy-MM-dd'))"
    }

    $cliCaText = [IO.File]::ReadAllText($cliCaListPath).TrimEnd()
    $pemBlocks = foreach ($certificate in $certificates) { "# Added by Fix-AwsCliTls.ps1: $($certificate.Subject) $($certificate.Thumbprint)`n" + (ConvertTo-PemText -Certificate $certificate) }
    $bundleText = $cliCaText + "`n`n" + ($pemBlocks -join "`n`n") + "`n"
    $bundleCertificateCount = ([regex]::Matches($bundleText, 'BEGIN CERTIFICATE')).Count
    $cliCertificateCount = ([regex]::Matches($cliCaText, 'BEGIN CERTIFICATE')).Count

    if ($PSCmdlet.ShouldProcess($BundlePath, 'Write CA bundle')) {
        $bundleDirectory = Split-Path -Parent $BundlePath
        if (-not (Test-Path -LiteralPath $bundleDirectory)) { New-Item -ItemType Directory -Path $bundleDirectory | Out-Null }
        if (Test-Path -LiteralPath $BundlePath) {
            $backupPath = "$BundlePath.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
            Copy-Item -LiteralPath $BundlePath -Destination $backupPath
            Write-LogMessage -Level INFO -Message "Backed up the existing CA bundle. Backup=$backupPath"
        }
        [IO.File]::WriteAllText($BundlePath, $bundleText, (New-Object System.Text.ASCIIEncoding))
        Write-LogMessage -Level INFO -Message "Wrote the CA bundle. Path=$BundlePath Certificates=$bundleCertificateCount (AWS CLI list $cliCertificateCount + $($certificates.Count) from Windows) Source=$cliCaListPath"
    }

    if (-not $SkipEnvironmentVariable) {
        $currentValue = [Environment]::GetEnvironmentVariable('AWS_CA_BUNDLE', 'User')
        if ($currentValue -and ($currentValue -ne $BundlePath) -and -not $Force) {
            Write-LogMessage -Level WARN -Message "AWS_CA_BUNDLE is already set to '$currentValue'. Not changing it. Re-run with -Force to replace it."
        }
        elseif ($currentValue -eq $BundlePath) {
            Write-LogMessage -Level INFO -Message 'AWS_CA_BUNDLE already points at the bundle. No change needed.'
        }
        elseif ($PSCmdlet.ShouldProcess('User environment variable AWS_CA_BUNDLE', "Set to $BundlePath")) {
            [Environment]::SetEnvironmentVariable('AWS_CA_BUNDLE', $BundlePath, 'User')
            $oldValue = if ($currentValue) { $currentValue } else { '(unset)' }
            Write-LogMessage -Level INFO -Message "Set the user environment variable AWS_CA_BUNDLE. Changes=AWS_CA_BUNDLE: $oldValue -> $BundlePath"
        }
    }

    if (-not $WhatIfPreference) {
        $testResult = Test-AwsTlsConnection -CaBundlePath $BundlePath
        if ($testResult -eq $false) {
            Write-LogMessage -Level ERROR -Message 'The connection test failed. The ARL root certificate may not be the one your firewall presents. Contact ARL ITS.'
            exit 1
        }
        Write-LogMessage -Level INFO -Message 'Done. Close and reopen any open terminals (and VS Code) so they pick up AWS_CA_BUNDLE.'
    }
    exit 0
}
catch {
    Write-LogMessage -Level ERROR -Message $_.Exception.Message
    exit 1
}
