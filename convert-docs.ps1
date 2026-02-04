# Paciolus Documentation Converter
Write-Host "Paciolus Documentation Converter" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Hardcoded path since we confirmed it exists
$pandocPath = "C:\Program Files\Pandoc\pandoc.exe"

if (-not (Test-Path $pandocPath)) {
    Write-Host "ERROR: Pandoc not found at: $pandocPath" -ForegroundColor Red
    exit 1
}

Write-Host "Using Pandoc at: $pandocPath" -ForegroundColor Green
Write-Host ""

# Get all markdown files
$files = Get-ChildItem -Path "docs" -Recurse -Filter "*.md"
Write-Host "Found $($files.Count) markdown files to convert" -ForegroundColor White
Write-Host ""

$success = 0
$failed = 0
$current = 0

foreach ($file in $files) {
    $current++
    $output = $file.FullName -replace '\.md$', '.docx'
    $name = $file.Name
    
    Write-Host "[$current/$($files.Count)] Converting: $name" -ForegroundColor Cyan
    
    # Use Invoke-Expression or direct call with &
    & $pandocPath $file.FullName -o $output --standalone --from markdown --to docx --toc --toc-depth=3 --highlight-style=tango
    
    if (Test-Path $output) {
        Write-Host "  Success: $($file.BaseName).docx" -ForegroundColor Green
        $success++
    }
    else {
        Write-Host "  Failed!" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "=================================" -ForegroundColor Green
Write-Host "Conversion Complete!" -ForegroundColor Green
Write-Host "Successful: $success / $($files.Count)" -ForegroundColor White
if ($failed -gt 0) {
    Write-Host "Failed: $failed" -ForegroundColor Red
}
Write-Host "=================================" -ForegroundColor Green
Write-Host ""
Write-Host "All .docx files are in the docs folder next to the .md files" -ForegroundColor White
