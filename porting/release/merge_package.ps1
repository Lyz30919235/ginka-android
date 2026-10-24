[CmdletBinding()]
param([string]$OutputDirectory = $PSScriptRoot)

$ErrorActionPreference = 'Stop'
$taskManifestPath = Join-Path $PSScriptRoot 'release-parts.json'
$taskManifest = Get-Content -LiteralPath $taskManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$taskOutputRoot = (Get-Item -LiteralPath $OutputDirectory -ErrorAction Stop).FullName
if ([IO.Path]::GetFileName($taskManifest.original.name) -ne $taskManifest.original.name) {
    throw 'Invalid output file name.'
}
$taskTarget = Join-Path $taskOutputRoot $taskManifest.original.name
if (Test-Path -LiteralPath $taskTarget) {
    if ((Get-FileHash -LiteralPath $taskTarget -Algorithm SHA256).Hash.ToLowerInvariant() -eq $taskManifest.original.sha256) {
        Write-Output ('Already verified: ' + $taskTarget)
        exit 0
    }
    throw 'An existing output has different content; it was not overwritten.'
}

foreach ($taskPart in $taskManifest.parts) {
    if ([IO.Path]::GetFileName($taskPart.name) -ne $taskPart.name) { throw 'Invalid part file name.' }
    $taskPartPath = Join-Path $PSScriptRoot $taskPart.name
    $taskPartFile = Get-Item -LiteralPath $taskPartPath -ErrorAction Stop
    if ($taskPartFile.Length -ne $taskPart.bytes) { throw ('Wrong part size: ' + $taskPart.name) }
    if ((Get-FileHash -LiteralPath $taskPartPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskPart.sha256) {
        throw ('Part SHA256 mismatch: ' + $taskPart.name)
    }
    Write-Output ('Verified: ' + $taskPart.name)
}

$taskPartial = Join-Path $taskOutputRoot (([Guid]::NewGuid().ToString('N')) + '.merge.partial')
$taskDestination = [IO.File]::Open($taskPartial, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try {
    foreach ($taskPart in $taskManifest.parts) {
        $taskSource = [IO.File]::OpenRead((Join-Path $PSScriptRoot $taskPart.name))
        try { $taskSource.CopyTo($taskDestination, 1048576) } finally { $taskSource.Dispose() }
    }
} finally { $taskDestination.Dispose() }

if ((Get-Item -LiteralPath $taskPartial).Length -ne $taskManifest.original.bytes -or
    (Get-FileHash -LiteralPath $taskPartial -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskManifest.original.sha256) {
    throw ('Merged file failed verification; partial retained: ' + $taskPartial)
}
Move-Item -LiteralPath $taskPartial -Destination $taskTarget -ErrorAction Stop
Write-Output ('Merged and verified: ' + $taskTarget)
