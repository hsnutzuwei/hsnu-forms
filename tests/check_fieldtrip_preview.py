"""Check field-trip Canvas changes without changing any Word outputs or other previews.
Requires playwright + lxml; --baseline-ref is the reviewed Word-only PR commit.
Screenshots are the actual Canvas bitmaps at their native resolution.
"""
import argparse
import base64
import subprocess
from pathlib import Path
from zipfile import ZipFile
from playwright.sync_api import sync_playwright

DATA = dict(className='16049',subject='美術',teacher='陳小明',teacher2='林小華',
            place='臺北市立美術館',purpose='參觀',year='115',month='11',day='12',
            startHour='08',endHour='18',appYear='115',appMonth='11',appDay='6')


def fill(page,data):
    for key,value in data.items():
        el=page.locator(f'[data-path="{key}"]')
        if el.evaluate('(e)=>e.tagName')=='SELECT':el.select_option(value)
        else:el.fill(value)


def settled(page):
    page.wait_for_function('imgs[current]?.complete && !paintScheduled')
    page.evaluate('document.fonts.ready')
    page.evaluate('new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')


def canvas(page):
    settled(page)
    return base64.b64decode(page.locator('#preview').evaluate("e=>e.toDataURL('image/png').split(',')[1]"))


def download(page,path):
    with page.expect_download() as d:page.locator('#docx').click()
    d.value.save_as(path)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--browser',default='/usr/bin/chromium')
    ap.add_argument('--baseline-ref',default='3cfe0f7660d8d59426872e06c8f4392b7cf38e98')
    ap.add_argument('--output-dir',default='work/preview-check')
    args=ap.parse_args()
    repo=Path(__file__).resolve().parents[1]
    out=Path(args.output_dir).resolve();out.mkdir(parents=True,exist_ok=True)
    before=subprocess.check_output(['git','show',f'{args.baseline_ref}:index.html'],cwd=repo).decode()
    after=(repo/'index.html').read_text()
    # The export code, embedded template/image data, draft handlers and editor stay exact.
    def outside_preview(s):
        start=s.index('// Field-trip preview only.') if '// Field-trip preview only.' in s else s.index('function painter(')
        return s[:start]+s[s.index('function paint(){',start):]
    assert outside_preview(before)==outside_preview(after)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=args.browser,headless=True,args=['--no-sandbox'])
        page=b.new_page(accept_downloads=True,viewport={'width':1600,'height':1100})
        for label,source in [('before',before),('after',after)]:
            page.goto('about:blank');page.set_content(source)
            fill(page,DATA)
            for i,v in enumerate(['國文','英文','數學','美術','物理','化學','歷史','地理','班會']):
                fill(page,{f'periods.{i}.schedule':v,f'periods.{i}.adjust':'調課' if i in (2,3) else ''})
            image=canvas(page);(out/f'preview-{label}.png').write_bytes(image)
            download(page,out/f'fieldtrip-{label}.docx')
            for form in ('course','guest','entry'):
                page.locator(f'[data-form="{form}"]').click()
                (out/f'{form}-{label}.png').write_bytes(canvas(page))
                download(page,out/f'{form}-{label}.docx')
        for form in ('fieldtrip','course','guest','entry'):
            with ZipFile(out/f'{form}-before.docx') as a,ZipFile(out/f'{form}-after.docx') as c:
                assert a.namelist()==c.namelist()
                assert all(a.read(k)==c.read(k) for k in a.namelist()),form
            if form!='fieldtrip':
                assert (out/f'{form}-before.png').read_bytes()==(out/f'{form}-after.png').read_bytes(),form
        page.locator('[data-form="fieldtrip"]').click()
        # Missing Kai uses installed CJK fallbacks; verify actual text drawing, not CSS alone.
        page.evaluate('''() => {
          window.previewCalls=[];
          const old=CanvasRenderingContext2D.prototype.fillText;
          CanvasRenderingContext2D.prototype.fillText=function(text,x,y,...args){
            window.previewCalls.push({text,font:this.font,x,y});return old.call(this,text,x,y,...args);
          };
          paint();
        }''')
        calls=page.evaluate('previewCalls')
        assert calls and all('DFKai-SB' in x['font'] for x in calls)
        assert any(x['text']=='四' for x in calls)
        assert len([x for x in calls if x['text']=='115'])==4
        assert all(x['x']>=0 and x['y']>=0 for x in calls)
        # Long inputs must remain visible; no old 5/9/16-character truncation.
        fill(page,{'teacher':'甲乙丙丁戊己庚辛壬癸甲乙','teacher2':'子丑寅卯辰巳午未申酉戌亥',
                   'place':'甲乙丙丁戊己庚辛壬癸甲乙'*3,
                   'periods.0.schedule':'甲乙丙丁戊己庚辛壬癸甲乙丙丁戊己庚辛',
                   'purpose':'其他','purposeOther':'甲乙丙丁戊己庚辛壬癸'*2})
        (out/'preview-long.png').write_bytes(canvas(page))
        # Loading a local test alias proves Canvas respects first-choice font and repaints.
        # This is not a test of the actual Windows DFKai-SB glyphs.
        initial=canvas(page)
        page.evaluate('''async () => {
          window.repaintCount=0;const old=paintFieldTripPreview;
          paintFieldTripPreview=function(ctx){window.repaintCount++;return old(ctx)};
          const face=new FontFace('DFKai-SB','local("Noto Sans CJK TC")');
          document.fonts.add(face);await face.load();await document.fonts.ready;
        }''')
        page.wait_for_function('repaintCount>0')
        assert canvas(page)!=initial,'Loaded first-choice font did not affect Canvas'
        # Save/load path and state remain functional.
        with page.expect_download() as d:page.locator('#downloadDraft').click()
        draft=out/'draft.json';d.value.save_as(draft)
        page.on('dialog',lambda d:d.accept())
        page.locator('#clear').click();page.locator('#fileDraft').set_input_files(draft)
        assert page.locator('[data-path="teacher2"]').input_value()=='子丑寅卯辰巳午未申酉戌亥'
        b.close()
    print('PASS: four DOCX packages unchanged, three other Canvas previews pixel-identical, fallback drawing, first-choice font loading/repaint, long input, draft roundtrip.')
    print('Native Windows Kai is not installed here; verify actual DFKai-SB appearance on Windows.')

if __name__=='__main__':main()
