<#
  本地 SSH 隧道：把云服务器上的管理界面映射到本机 127.0.0.1
  用法：
      powershell -ExecutionPolicy Bypass -File .\tunnel.ps1 -Server <服务器IP>
  说明：私钥不包含在本仓库中，请使用自己的 SSH 密钥。
#>
param(
  [Parameter(Mandatory = $true)]
  [string]$Server,
  [string]$User = "root",
  [int]$SshPort = 22,
  [string]$KeyPath = "$HOME\.ssh\id_ed25519"
)

if (-not (Test-Path $KeyPath)) { Write-Error "找不到密钥：$KeyPath"; exit 1 }

Write-Host ""
Write-Host "正在建立 SSH 隧道（关闭此窗口即断开）..." -ForegroundColor Cyan
Write-Host "  AstrBot 管理面板 : http://127.0.0.1:6185" -ForegroundColor Green
Write-Host "  QQ 扫码桌面      : http://127.0.0.1:6081/vnc.html" -ForegroundColor Green
Write-Host "  SnowLuma 面板    : http://127.0.0.1:5099" -ForegroundColor Green
Write-Host ""

ssh -N -i $KeyPath -p $SshPort `
  -o StrictHostKeyChecking=accept-new `
  -o ServerAliveInterval=30 `
  -o ExitOnForwardFailure=yes `
  -L 6185:127.0.0.1:6185 `
  -L 6081:127.0.0.1:6081 `
  -L 5099:127.0.0.1:5099 `
  "$User@$Server"
