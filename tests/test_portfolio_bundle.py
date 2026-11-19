from pathlib import Path
import hashlib,zipfile
import fitz
from reporting.config import settings as c
def test_eight_pages_and_approved_sections():
 d=fitz.open(c.OUTPUT/'portfolio_summary.pdf')
 assert len(d)==8
 assert 'TECHNOLOGY STACK' in d[6].get_text()
 assert 'APPLIED ENGINEERING KNOWLEDGE' in d[7].get_text()
 assert len(d.get_toc())==8
def test_no_cross_file_buttons_or_links():
 d=fitz.open(c.OUTPUT/'portfolio_summary.pdf')
 for p in d:
  assert not p.get_links()
  for text in ['Explore the Dashboard','Open Offline Dashboard','View Full Dashboard PDF','Keep the companion files together']:
   assert text not in p.get_text()
def test_pdf_text_in_bounds():
 d=fitz.open(c.OUTPUT/'portfolio_summary.pdf')
 for p in d:
  for b in p.get_text('blocks'):
   assert b[0]>=0 and b[1]>=0 and b[2]<=p.rect.width+1 and b[3]<=p.rect.height+1
def test_live_and_offline_keep_report_links():
 from app import shell
 from bs4 import BeautifulSoup
 for html in [shell(),(c.OUTPUT/'dashboard.html').read_text(),(c.OUTPUT/'preview_report.html').read_text()]:
  soup=BeautifulSoup(html,'html.parser')
  links=[a['href'] for a in soup.select('a[href$=".pdf"]')]
  assert any(x.endswith('portfolio_summary.pdf') for x in links)
  assert any(x.endswith('full_dashboard_report.pdf') for x in links)
  assert not soup.select('a[href^="file:"]')
 soup=BeautifulSoup(shell(),'html.parser')
 actions=soup.select_one('.actions')
 assert actions.select_one('button[data-action="reset"]')
 assert len(actions.select('a[href$=".pdf"]'))==2
