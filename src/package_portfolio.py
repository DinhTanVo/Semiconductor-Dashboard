"""Package the final review documents; no cross-file buttons are included."""
from pathlib import Path
import zipfile
from reporting.config import settings as c

def package():
    target=c.OUTPUT/'Final_Review_Documents.zip'
    files={'Portfolio.pdf':c.OUTPUT/'portfolio_summary.pdf','Dashboard.html':c.OUTPUT/'dashboard.html','Full_Dashboard_Report.pdf':c.OUTPUT/'full_dashboard_report.pdf'}
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for name,path in files.items():z.write(path,name)
    return target
if __name__=='__main__':print(package())
