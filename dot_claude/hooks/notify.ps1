# Play a sound and show a Windows toast for a Claude Code hook event.
# Reads the hook's JSON payload from stdin. To check the toast content without showing it:
#   echo '{"hook_event_name":"Stop","cwd":"C:\\dev"}' | powershell -File notify.ps1 -DryRun
param([switch]$DryRun)

function ConvertTo-Preview([string]$Text, [int]$Max = 120) {
    $plain = $Text -replace '(?s)```.*?```', ' '
    $plain = $plain -replace '\[([^\]]*)\]\([^)]*\)', '$1'
    $plain = $plain -replace '(?m)^\s*(#+|>)\s*', ''
    $plain = $plain -replace '[*`|]', ''
    $plain = $plain -replace '-{3,}', ''
    $plain = ($plain -replace '\s+', ' ').Trim()
    if ($plain.Length -gt $Max) { $plain = $plain.Substring(0, $Max).TrimEnd() + '...' }
    $plain
}

# Decode stdin as UTF-8 directly; the console code page would garble non-ASCII text.
$raw = ''
if ([Console]::IsInputRedirected) {
    $reader = New-Object System.IO.StreamReader([Console]::OpenStandardInput(), [System.Text.Encoding]::UTF8)
    $raw = $reader.ReadToEnd()
}
$payload = if ($raw.Trim()) { $raw | ConvertFrom-Json } else { New-Object PSObject }

$kind = if ($payload.hook_event_name -eq 'Notification') { $payload.notification_type } else { $payload.hook_event_name }

$sounds = Join-Path $PSScriptRoot 'sounds'
$media = Join-Path $env:WINDIR 'Media'

switch ($kind) {
    'Stop' {
        $sound = Join-Path $sounds 'bell-triple.wav'
        $status = 'Finished responding'
    }
    'permission_prompt' {
        $sound = Join-Path $media 'Windows Message Nudge.wav'
        $status = 'Needs your permission'
    }
    'idle_prompt' {
        $sound = Join-Path $media 'Windows Proximity Notification.wav'
        $status = 'Waiting for your input'
    }
    default {
        $sound = $null
        $status = 'Notification'
    }
}

# Claude Code's own wording is more specific, e.g. "Claude needs your permission to use Bash".
if ($payload.message) { $status = $payload.message }

$preview = $null
if ($kind -eq 'Stop' -and $payload.last_assistant_message) {
    $preview = ConvertTo-Preview $payload.last_assistant_message
}

$cwd = $payload.cwd
$title = 'Claude Code'
if ($cwd) {
    $title += ' - ' + (Split-Path $cwd -Leaf)
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $branch = git -C $cwd branch --show-current 2>$null
        if ($branch) { $title += " ($branch)" }
    }
}

$esc = { param($s) [System.Security.SecurityElement]::Escape($s) }
$texts = @(@($title, $status, $preview) | Where-Object { $_ } | ForEach-Object { "<text>$(& $esc $_)</text>" })
if ($cwd) { $texts += "<text placement=`"attribution`">$(& $esc $cwd)</text>" }

# Silent, because the sound below plays instead.
$xml = "<toast><visual><binding template=`"ToastGeneric`">$($texts -join '')</binding></visual><audio silent=`"true`"/></toast>"

if ($DryRun) {
    try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
    $xml
    return
}

# Borrow Windows PowerShell's AppUserModelID so the toast shows without registering a custom app.
$appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'

[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$doc = New-Object Windows.Data.Xml.Dom.XmlDocument
$doc.LoadXml($xml)
$toast = New-Object Windows.UI.Notifications.ToastNotification $doc
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)

# PlaySync keeps the process alive until the sound finishes. Beep if the file is missing.
if ($sound -and (Test-Path $sound)) {
    (New-Object System.Media.SoundPlayer $sound).PlaySync()
} else {
    [console]::Beep(800, 150)
}
