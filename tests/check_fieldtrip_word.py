"""Integration check: real browser inputs/downloads, OOXML invariants and other-form regression.
Requires: pip install playwright lxml. Use --browser for a system Chromium.
The generated DOCX files must also be rendered and visually inspected.
"""
import argparse
import base64
import io
import re
import subprocess
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from playwright.sync_api import sync_playwright

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}

def xml(path):
    return E.fromstring(ZipFile(path).read('word/document.xml'))

def fill(page, data):
    for key, value in data.items():
        el = page.locator(f'[data-path="{key}"]')
        if el.evaluate('(e)=>e.tagName') == 'SELECT':
            el.select_option(value)
        else:
            el.fill(value)

def export(page, path):
    with page.expect_download() as download:
        page.locator('#docx').click()
    download.value.save_as(path)
    return xml(path)

def text(node):
    return ''.join(node.xpath('.//w:t/text()', namespaces=NS))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser')
    parser.add_argument('--output-dir', default='work/fieldtrip-check')
    parser.add_argument('--baseline-ref', default='main')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    source = (repo / 'index.html').read_text()
    baseline = subprocess.check_output(['git', 'show', f'{args.baseline_ref}:index.html'], cwd=repo).decode()
    # Only the fieldtrip template and fieldtrip export functions may differ.
    def unrelated(s):
        start = s.index('// Field-trip preview only.') if '// Field-trip preview only.' in s else s.index('function painter(')
        s = s[:start] + s[s.index('function paint(){', start):]
        s = re.sub(r'(fieldDoc["\']?\s*:\s*["\'])[^"\']+', r'\1TEMPLATE', s, count=1)
        start = s.index('// Field-trip only:') if '// Field-trip only:' in s else s.index('function wordFieldTrip(')
        return s[:start] + s[s.index('function setRunText(', start):]
    assert unrelated(source) == unrelated(baseline), 'Unrelated application code changed'
    template = base64.b64decode(re.search(r'fieldDoc["\']?\s*:\s*["\']([^"\']+)', source)[1])
    original = E.fromstring(ZipFile(io.BytesIO(template)).read('word/document.xml'))
    (out / 'template.docx').write_bytes(template)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=args.browser, args=['--no-sandbox'])
        page = browser.new_page(accept_downloads=True)
        page.set_content(source)
        data = dict(className='16049', subject='美術', teacher='陳小明', teacher2='林小華',
                    place='臺北市立美術館', purpose='參觀', year='115', month='11', day='12',
                    startHour='08', endHour='18', appYear='115', appMonth='11', appDay='6')
        fill(page, data)
        for i, course in enumerate(['國文','英文','數學','美術','物理','化學','歷史','地理','班會']):
            fill(page, {f'periods.{i}.schedule': course, f'periods.{i}.adjust': '調課' if i in (2,3) else ''})
        sample = export(page, out / 'sample.docx')
        tables = sample.findall('.//w:tbl', NS)
        assert len(tables) == 18
        for base in (0,4):
            for row in tables[base].findall('w:tr', NS):
                assert not text(row.findall('w:tc', NS)[0]), 'Signature cell is not blank'
            assert '16049' == text(tables[base+1].findall('w:tr/w:tc', NS)[2])
            assert text(tables[base+3]) == data['place']
        # Identical paired cells, including teacher columns, timetable and date/time.
        for left, right in [(i,i+4) for i in range(4)] + [(i,i+5) for i in range(8,13)]:
            assert text(tables[left]) == text(tables[right])
        assert sample.find('.//w:pgSz', NS).attrib == original.find('.//w:pgSz', NS).attrib
        assert len(sample.findall('.//{urn:schemas-microsoft-com:vml}shape')) == len(original.findall('.//{urn:schemas-microsoft-com:vml}shape'))
        weekdays = [x for x in sample.findall('.//w:txbxContent', NS) if text(x).startswith('︵週')]
        assert weekdays and all('四' in text(x) for x in weekdays)
        assert all('115年11月6日' in text(x) for x in sample.findall('.//w:txbxContent', NS) if text(x).startswith('申請日期'))
        # Draft save/load uses the unchanged UI path.
        with page.expect_download() as download:
            page.locator('#downloadDraft').click()
        draft = out / 'draft.json'
        download.value.save_as(draft)
        page.on('dialog', lambda dialog: dialog.accept())
        page.locator('#clear').click()
        page.locator('#fileDraft').set_input_files(draft)
        assert page.locator('[data-path="teacher2"]').input_value() == '林小華'
        # All six purpose options; single teacher, zero hour, and maximum-length content.
        for i,purpose in enumerate(['參觀','訪問','研討會','實驗操作','相關環境教育','其他']):
            fill(page, {'purpose': purpose, 'teacher2': '', 'startHour': '00', 'endHour': '23'})
            if purpose == '其他':
                fill(page, {'className':'123456789012','subject':'甲乙丙丁戊己庚辛壬癸甲乙',
                            'teacher':'甲乙丙丁戊己庚辛壬癸甲乙','teacher2':'子丑寅卯辰巳午未申酉戌亥',
                            'place':'甲乙丙丁戊己庚辛壬癸甲乙'*3, 'purposeOther':'甲乙丙丁戊己庚辛壬癸'*2,
                            'periods.0.schedule':'甲乙丙丁戊己庚辛壬癸甲乙丙丁戊己庚辛'})
            result = export(page, out / f'purpose-{i+1}.docx')
            boxes = [text(x) for x in result.findall('.//w:txbxContent', NS)]
            assert sum(x == '■'+purpose for x in boxes) >= 2
            assert sum('■' in x for x in boxes) == sum(x == '■'+purpose for x in boxes)
        # Other three exports must match the baseline package part-for-part.
        for form in ('course','guest','entry'):
            paths = []
            for label,html in [('before',baseline),('after',source)]:
                page.goto('about:blank')
                page.set_content(html)
                page.locator(f'[data-form="{form}"]').click()
                path = out / f'{form}-{label}.docx'
                export(page,path)
                paths.append(path)
            a,b = map(ZipFile,paths)
            assert a.namelist() == b.namelist()
            assert all(a.read(k) == b.read(k) for k in a.namelist()), form
        assert 'https://hsnu-campus-map.vercel.app/' in source
        browser.close()
    print('PASS: real UI downloads; paired data; blank signatures; original page size; all purposes; draft roundtrip; unrelated source and three DOCX packages unchanged.')
    print('Render template.docx, sample.docx and purpose-6.docx for visual acceptance.')

if __name__ == '__main__':
    main()
