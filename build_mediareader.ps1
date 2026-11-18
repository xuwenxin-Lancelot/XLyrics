$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$vswhere = 'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
$compiler = & $vswhere -latest -products '*' -find 'VC\Tools\MSVC\**\bin\Hostx64\x64\cl.exe' | Select-Object -First 1
if (-not $compiler) { throw 'C++ compiler not found' }
Write-Output "Compiler: $compiler"
$msvc = Split-Path (Split-Path (Split-Path (Split-Path $compiler)))
$sdk = 'C:\Program Files (x86)\Windows Kits\10'
$version = Get-ChildItem -LiteralPath (Join-Path $sdk 'Include') -Directory | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty Name
Write-Output "SDK version: $version"
$env:INCLUDE = @((Join-Path $msvc 'include'), (Join-Path $sdk "Include\$version\ucrt"),
    (Join-Path $sdk "Include\$version\shared"), (Join-Path $sdk "Include\$version\um"),
    (Join-Path $sdk "Include\$version\winrt"), (Join-Path $sdk "Include\$version\cppwinrt")) -join ';'
$env:LIB = @((Join-Path $msvc 'lib\x64'), (Join-Path $sdk "Lib\$version\um\x64"), (Join-Path $sdk "Lib\$version\ucrt\x64")) -join ';'
Push-Location -LiteralPath $project
try {
    & $compiler /nologo /utf-8 /std:c++20 /EHsc /O2 /MT /DUNICODE /D_UNICODE MediaReader.cpp /link /OUT:MediaReader.exe windowsapp.lib user32.lib 2>&1 | Select-Object -Last 15
    if ($LASTEXITCODE -ne 0) { throw 'MediaReader compile failed' }
    Write-Output 'MediaReader.exe built'
    & $compiler /nologo /utf-8 /TC /O2 /MT /LD qrc_decode.c third_party\qq_des\des.c /link /OUT:QrcDecode.dll 2>&1 | Select-Object -Last 15
    if ($LASTEXITCODE -ne 0) { throw 'QrcDecode compile failed' }
    Write-Output 'QrcDecode.dll built'
    & $compiler /nologo /std:c++20 /EHsc /O2 /MT /LD /DUNICODE /D_UNICODE RoundedBackdrop.cpp /link /OUT:RoundedBackdrop.dll windowsapp.lib dwmapi.lib user32.lib CoreMessaging.lib 2>&1 | Select-Object -Last 15
    if ($LASTEXITCODE -ne 0) { throw 'RoundedBackdrop compile failed' }
    Write-Output 'RoundedBackdrop.dll built'
} finally { Pop-Location }
