"""Browser/OOXML acceptance for entry remarks, 14pt text and optional signing details.
Run: python tests/check_entry_readability.py --browser /usr/bin/chromium --output-dir work/entry-check
Render the emitted DOCX files separately to verify single-page A4 output.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
from lxml import etree as E
from zipfile import ZipFile
import argparse,base64,subprocess
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';NS={'w':W}
def fill(page,key,value):
 e=page.locator(f'[data-path="{key}"]')
 if e.evaluate('(e)=>e.tagName')=='SELECT':e.select_option(value)
 else:e.fill(value)
def export(page,path):
 with page.expect_download() as d:page.locator('#docx').click()
 d.value.save_as(path)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--browser',default='/usr/bin/chromium');ap.add_argument('--output-dir',default='work/entry-check');a=ap.parse_args()
 repo=Path(__file__).resolve().parents[1];out=Path(a.output_dir).resolve();out.mkdir(parents=True,exist_ok=True)
 after=(repo/'index.html').read_text();before=subprocess.check_output(['git','show','origin/main:index.html'],cwd=repo).decode()
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=a.browser,headless=True,args=['--no-sandbox']);page=b.new_page(accept_downloads=True,viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(after);page.locator('[data-form="entry"]').click()
  export(page,out/'entry-empty.docx')
  long_note='甲乙丙丁戊己庚辛壬癸'*2+'甲乙丙丁戊';long_name='甲乙丙丁戊己庚辛壬癸甲乙丙丁戊己'
  for i in range(19):
   for k,v in {'month':'11','day':'17','name':long_name,'plate':long_note}.items():fill(page,f'rows.{i}.{k}',v)
  remark=page.locator('[data-path="rows.0.plate"]');remark.scroll_into_view_if_needed()
  assert remark.input_value()==long_note and remark.bounding_box()['width']>=280
  box=remark.bounding_box();assert box['x']>=0 and box['x']+box['width']<=390, 'Mobile remark is clipped'
  for k,v in {'handlerName':'陳小明','handlerDate':'2026-11-17','supervisorName':'林小華','supervisorDate':'2026-11-18'}.items():fill(page,k,v)
  page.wait_for_function('imgs.entry?.complete && !paintScheduled');page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
  (out/'entry-preview.png').write_bytes(base64.b64decode(page.locator('#preview').evaluate("e=>e.toDataURL().split(',')[1]")))
  page.locator('.entry-grid tbody tr').first.screenshot(path=str(out/'mobile-remarks.png'))
  export(page,out/'entry-full.docx')
  # Real draft roundtrip includes newly optional fields and every remark.
  with page.expect_download() as d:page.locator('#downloadDraft').click()
  draft=out/'draft.json';d.value.save_as(draft);page.on('dialog',lambda d:d.accept());page.locator('#clear').click();page.locator('#fileDraft').set_input_files(draft)
  page.wait_for_function("model.entry.handlerName==='陳小明'")
  assert page.locator('[data-path="handlerDate"]').input_value()=='2026-11-17'
  assert remark.input_value()==long_note
  for k in ['handlerDate','supervisorName','supervisorDate']:fill(page,k,'')
  export(page,out/'entry-handler-only.docx')
  # Legacy drafts contain only rows, with no new signing fields.
  page.locator('#fileDraft').set_input_files({'name':'legacy.json','mimeType':'application/json','buffer':b'{"form":"entry","data":{"rows":[{"year":"115","month":"11","day":"17","name":"Old","plate":"ABC-1234"}]}}'})
  page.wait_for_function("model.entry.rows[0].name==='Old'")
  export(page,out/'entry-legacy.docx')
  # Other forms export unchanged, and their Canvas pixels remain unchanged.
  for form in ['fieldtrip','course','guest']:
   images=[]
   for label,html in [('before',before),('after',after)]:
    page.goto('about:blank');page.set_content(html);page.locator(f'[data-form="{form}"]').click();page.wait_for_function('imgs[current]?.complete && !paintScheduled');page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
    images.append(page.locator('#preview').evaluate('e=>e.toDataURL()'));export(page,out/f'{form}-{label}.docx')
   assert images[0]==images[1],form+' preview changed'
   with ZipFile(out/f'{form}-before.docx') as old,ZipFile(out/f'{form}-after.docx') as new:
    assert old.namelist()==new.namelist() and all(old.read(k)==new.read(k) for k in old.namelist()),form+' DOCX changed'
  assert not errors,errors;b.close()
 for label in ['empty','full','handler-only','legacy']:
  root=E.fromstring(ZipFile(out/f'entry-{label}.docx').read('word/document.xml'));table=root.find('.//w:tbl',NS);rows=table.findall('w:tr',NS)
  assert len(rows)==20
  for row in rows[1:]:
   for run in row.findall('.//w:r',NS):
    if run.find('w:t',NS) is not None:assert run.find('w:rPr/w:sz',NS).get('{'+W+'}val')=='28'
  texts=''.join(root.xpath('//w:t/text()',namespaces=NS))
  assert '承辦人：' in texts and '單位主管：' in texts
  assert '姓名：' not in texts and '日期：' not in texts
  if label=='empty':assert '姓名：' not in texts and '日期：' not in texts
  if label=='full':assert all(x in texts for x in ['　　陳小明','　　林小華','　　115年11月17日','　　115年11月18日'])
  if label=='handler-only':assert '　　陳小明' in texts and '日期：' not in texts and '　　林小華' not in texts
 print('PASS: mobile remark input, all filled cells 14pt, optional/blank signing fields, legacy/new drafts, 19 rows, three other Word exports and Canvas unchanged; render all entry DOCX for page/overlap checks.')
if __name__=='__main__':main()
