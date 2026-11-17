from pathlib import Path
from playwright.sync_api import sync_playwright
import base64,subprocess,json
from zipfile import ZipFile
from openpyxl import load_workbook
repo=Path(__file__).resolve().parents[1];out=Path(__import__('sys').argv[1] if len(__import__('sys').argv)>1 else '/tmp/receipt-check');out.mkdir(parents=True,exist_ok=True);html=(repo/'index.html').read_text()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page(accept_downloads=True,viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html);page.locator('[data-form="receipt"]').click()
 for key,value in dict(reason='美術班專題講座',name='測試講師',title='教授',topic='藝術與生活',activityDate='2026-11-17',startTime='13:00',endTime='15:00',units='2',assistant='1000',attendance='2500',car='1200',train='300',hsr='1500',lodging='2000',idNumber='A123456789',address='臺北市大安區測試路一號',account='001234567890').items():page.locator(f'[data-path="{key}"]').fill(value)
 page.locator('[data-path="bankCode"]').select_option('004');page.locator('[data-path="branchCode"]').select_option(index=1)
 page.wait_for_function('imgs.receipt.complete && !paintScheduled')
 (out/'preview.png').write_bytes(base64.b64decode(page.locator('#preview').evaluate("e=>e.toDataURL().split(',')[1]")))
 with page.expect_download() as d:page.locator('#docx').click()
 d.value.save_as(out/'filled.xlsx')
 with page.expect_download() as d:page.locator('#downloadDraft').click()
 d.value.save_as(out/'draft.json');page.on('dialog',lambda d:d.accept());page.locator('#clear').click();page.locator('#fileDraft').set_input_files(out/'draft.json');assert page.locator('[data-path="account"]').input_value()=='001234567890'
 page.locator('[data-path="notesMode"]').select_option('自行輸入');page.locator('[data-path="notes"]').fill('上下同步備註測試')
 with page.expect_download() as d:page.locator('#docx').click()
 d.value.save_as(out/'manual.xlsx')
 before=subprocess.check_output(['git','show','origin/main:index.html'],cwd=repo).decode()
 for form in ['fieldtrip','course','guest','entry']:
  previews=[];packages=[]
  for text in [before,html]:
   page.goto('about:blank');page.set_content(text);page.locator(f'[data-form="{form}"]').click();page.wait_for_function('imgs[current].complete && !paintScheduled');page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');previews.append(page.locator('#preview').evaluate('e=>e.toDataURL()'))
   with page.expect_download() as d:page.locator('#docx').click()
   path=out/f'{form}-{len(packages)}.docx';d.value.save_as(path)
   with ZipFile(path) as z:packages.append({k:z.read(k) for k in z.namelist()})
  assert previews[0]==previews[1],form+' preview changed';assert packages[0]==packages[1],form+' Word changed'
 assert not errors,errors;b.close()
w=load_workbook(out/'filled.xlsx',data_only=True).active
for upper,lower,n in [('E3','E23',4000),('E4','E24',1000),('E5','E25',2500),('E6','E26',1200),('E7','E27',300),('E8','E28',1500),('E9','E29',2000),('E10','E30',12500)]:assert w[upper].value==w[lower].value==n,(upper,w[upper].value)
assert w['I25'].value=='001234567890';assert w['B21'].value=='測試講師';assert w['C21'].value in [None,''];assert w['G3'].value==w['G27'].value
for c in ['C21','E21','G21','G25','I25']:assert w[c].fill.fgColor.rgb=='FFFFFFCC'
w=load_workbook(out/'manual.xlsx',data_only=True).active;assert w['G3'].value==w['G27'].value=='備註:上下同步備註測試'
print('PASS receipt calculations, synchronization, bank selection, leading zeros, yellow cells, draft roundtrip; all four existing Word packages and previews unchanged')
