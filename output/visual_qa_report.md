# Corrected Final Local Edition

## Approved scope
Only the portfolio has its Explore the Dashboard blocks removed from pages 1 and 8. Live website and offline HTML keep Reset filters and the Portfolio PDF / Full dashboard PDF shortcuts in their original layout. Both PDF documents are byte-identical to the previously approved final files.

## Verified
- 86 automated tests passed in 105.19 seconds.
- 10 targeted browser checks passed: both live PDF links returned valid PDFs; all five tabs rendered; filter and Reset updated analysis; offline images, navigation and PDF target paths verified.
- No browser page errors detected.
- Action row screenshot inspected: Reset filters | Portfolio PDF | Full dashboard PDF.
- Portfolio and full dashboard PDF unchanged, confirmed by byte comparison.
- ZIP integrity checked.

## Use
Run python app.py in your existing environment. No runtime dependencies changed. For offline viewing, open output/dashboard.html; keep portfolio_summary.pdf and full_dashboard_report.pdf in the same output folder. The complete ZIP already preserves this structure. Portfolio itself has no external-file buttons and can be shared independently.

Verified on Linux/Chromium, not Windows. Offline report is static; interactive filters run in the local app.
