"""Real UI/Word/Canvas regression for course readability and entry footer alignment.
Requires Python playwright and lxml. Render exported DOCX separately for visual acceptance.
"""
import argparse,base64,subprocess
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from playwright.sync_api import sync_playwright
from check_fieldtrip_preview import fill,canvas,DATA
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main';NS={'w':W}
COURSE=dict(schoolYear='115',semester='2',name='張雅婷',delegate='王小明',remark='課程調整已完成確認',submitYear='115',submitMonth='11',submitDay='6',startYear='115',startMonth='12',startDay='18',startHour='09',endYear='115',endMonth='12',endDay='20',endHour='17')
ENTRY={'rows.0.year':'115','rows.0.month':'11','rows.0.day':'6','rows.0.name':'陳小明','rows.0.plate':'ABC-1234'}

def doc(path):return E.fromstring(ZipFile(path).read('word/document.xml'))
def text(x):return ''.join(x.xpath('.//w:t/text()',namespaces=NS))
def export(page,path):
    with page.expect_download() as d:page.locator('#docx').click()
    d.value.save_as(path)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--browser',default='/usr/bin/chromium');ap.add_argument('--output-dir',default='work/course-entry-check');ap.add_argument('--baseline-ref',default='2ac8ef7a3871f073f5670f1cc58dfe1d4ae5f140');a=ap.parse_args()
    repo=Path(__file__).resolve().parents[1];out=Path(a.output_dir).resolve();out.mkdir(parents=True,exist_ok=True)
    before=subprocess.check_output(['git','show',f'{a.baseline_ref}:index.html'],cwd=repo).decode();after=(repo/'index.html').read_text()
    assert before[before.index('function wordFieldTrip('):before.index('function setRunText(')]==after[after.index('function wordFieldTrip('):after.index('function setRunText(')]
    assert before[before.index('function downloadBlob('):before.index('function wordCourse(')]==after[after.index('function downloadBlob('):after.index('function wordCourse(')]
    assert before[before.index('function forceKaiDom('):]==after[after.index('function forceKaiDom('):]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=a.browser,headless=True,args=['--no-sandbox']);page=b.new_page(accept_downloads=True)
        for label,source in [('before',before),('after',after)]:
            for form,fields in [('course',COURSE),('entry',ENTRY),('fieldtrip',DATA),('guest',{'reason':'參訪','carOwner':'林小華','plate':'ABC-1234'})]:
                page.goto('about:blank');page.set_content(source);page.locator(f'[data-form="{form}"]').click();fill(page,fields)
                if form=='course':fill(page,{'rows.0.className':'1604','rows.0.subject':'國文','rows.0.day':'12/18','rows.0.period':'8','rows.0.substitute':'陳美玲'})
                (out/f'{form}-{label}-preview.png').write_bytes(canvas(page));export(page,out/f'{form}-{label}.docx')
        for form in ('fieldtrip','guest'):
            with ZipFile(out/f'{form}-before.docx') as x,ZipFile(out/f'{form}-after.docx') as y:
                assert x.namelist()==y.namelist();assert all(x.read(k)==y.read(k) for k in x.namelist())
            assert (out/f'{form}-before-preview.png').read_bytes()==(out/f'{form}-after-preview.png').read_bytes()
        course=doc(out/'course-after.docx');baseline=doc(out/'course-before.docx')
        for value,size in [('115','36'),('　　王小明　　','24')]:
            ts=course.xpath('//w:r[w:t=$value]',namespaces=NS,value=value);assert ts
            assert ts[0].find('w:rPr/w:sz',NS).get('{'+W+'}val')==size
        remark=course.xpath('//w:p[w:r/w:t="課程調整已完成確認"]',namespaces=NS)[0]
        assert remark.find('w:pPr/w:ind',NS).get('{'+W+'}left')=='240'
        assert E.tostring(course.find('.//w:tblGrid',NS))==E.tostring(baseline.find('.//w:tblGrid',NS))
        entry=doc(out/'entry-after.docx');old_entry=doc(out/'entry-before.docx')
        footer=next(x for x in entry.findall('w:body/w:p',NS) if '美術班' in text(x))
        indent=footer.find('w:pPr/w:ind',NS);assert indent.get('{'+W+'}right')=='353'
        indent.getparent().remove(indent)
        assert E.tostring(entry,method='c14n')==E.tostring(old_entry,method='c14n'),'Entry changed beyond footer indentation'
        # Long delegate/remark and all 10 rows, using actual form controls.
        page.goto('about:blank');page.set_content(after);page.locator('[data-form="course"]').click();fill(page,COURSE)
        fill(page,{'delegate':'甲乙丙丁戊己庚辛壬癸甲乙','remark':'甲乙丙丁戊己庚辛壬癸'*5})
        for i in range(10):fill(page,{f'rows.{i}.className':'1604',f'rows.{i}.subject':'國文',f'rows.{i}.day':'12/18',f'rows.{i}.period':str(i%9+1),f'rows.{i}.substitute':'陳美玲'})
        export(page,out/'course-long.docx');(out/'course-long-preview.png').write_bytes(canvas(page))
        # Both draft forms download JSON and load their matching form/data.
        page.on('dialog',lambda d:d.accept())
        for form,key,value in [('course','delegate','王小明'),('fieldtrip','teacher2','林小華')]:
            page.locator(f'[data-form="{form}"]').click();fill(page,{key:value})
            with page.expect_download() as d:page.locator('#downloadDraft').click()
            path=out/f'{form}-draft.json';d.value.save_as(path)
            page.locator('#clear').click();page.locator('#fileDraft').set_input_files(path)
            assert page.locator(f'[data-path="{key}"]').input_value()==value
        b.close()
    print('PASS: course sizes/padding/remark indent; entry only footer indentation; fieldtrip+guest DOCX/Canvas unchanged; course+fieldtrip JSON draft roundtrip; long case exported. Render course/entry/long DOCX for visual acceptance.')
if __name__=='__main__':main()
