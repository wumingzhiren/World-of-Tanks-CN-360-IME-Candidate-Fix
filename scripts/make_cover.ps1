Add-Type -AssemblyName System.Drawing
$ErrorActionPreference = 'Stop'

$src = Join-Path $PSScriptRoot '..\docs\images\candidate-window-1to1.png'
$dst = Join-Path $PSScriptRoot '..\docs\images\cover-wbpimg.jpg'

$img = [System.Drawing.Image]::FromFile($src)
# 直接 1:1 转 jpg，不加任何文字/边框/拼版
$bmp = New-Object System.Drawing.Bitmap($img.Width, $img.Height)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$g.Clear([System.Drawing.Color]::White)
$g.DrawImage($img, 0, 0, $img.Width, $img.Height)
$g.Dispose()

$enc = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
$ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, 96L)
$bmp.Save($dst, $enc, $ep)

Write-Output ("size " + $bmp.Width + "x" + $bmp.Height + "  bytes " + (Get-Item $dst).Length)
$bmp.Dispose()
$img.Dispose()
