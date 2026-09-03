# run_tests.ps1 —— 本地一键测试 + pytest-html 网页报告
#
# 功能：
#   1. 自动清理上一次生成的报告文件；
#   2. 按 pytest.ini 的 testpaths 顺序执行全部用例（冒烟 → 正向 → 反向）；
#   3. 用已安装的 pytest-html 生成自包含的单文件 HTML 报告，浏览器直接打开。
#
# 用法：
#   .\run_tests.ps1            # 跑完生成报告（不自动打开）
#   .\run_tests.ps1 -Open      # 跑完自动用浏览器打开报告
#
# 前置条件：ServeRest 已启动（docker compose up -d --wait）。

param(
    [switch]$Open
)

$ErrorActionPreference = 'Stop'

# 脚本所在目录即项目根目录，后续所有路径都基于它，避免受当前工作目录影响
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$reportFile = Join-Path $root 'pytest_report.html'

function Remove-PathIfExists([string]$Path) {
    # 只删除项目根目录下明确指定的生成物，防止误删其他内容
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

if (-not (Test-Path -LiteralPath $python)) {
    Write-Error "未找到虚拟环境 Python：$python"
    exit 1
}

Write-Host '== 清理旧报告 =='
# 旧的 pytest-html 报告，以及切换方案前遗留的 allure 目录，一并清掉
Remove-PathIfExists $reportFile
Remove-PathIfExists (Join-Path $root 'allure-results')
Remove-PathIfExists (Join-Path $root 'allure-report')

Write-Host '== 运行全部用例（冒烟 → 正向 → 反向）=='
& $python -m pytest "--html=$reportFile" --self-contained-html -q
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Host "存在失败用例（退出码 $exitCode），报告已生成，可打开查看失败详情。"
} else {
    Write-Host '全部用例通过。'
}

Write-Host "报告已生成：$reportFile"
if ($Open -and (Test-Path -LiteralPath $reportFile)) {
    Start-Process $reportFile
}

exit $exitCode
