// Run with: node tests/check_course_ranges.js
// Pure logic/HTML checks only; this does not replace a browser or DOCX render test.
const fs=require('node:fs'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
function check(ok,message){if(!ok)throw Error(message);}
for(const match of source.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))new Function(match[1]);
const helpers=source.slice(source.indexOf('function coursePeriodOptions('),source.indexOf('function courseEditor('));
const editor=source.slice(source.indexOf('function courseEditor('),source.indexOf('function guestEditor('));
const setter=source.slice(source.indexOf('function setPath('),source.indexOf('function normalizeDateAfterSelect('));
const stub=String.raw`const enc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const pad2=n=>String(n).padStart(2,'0');
const model={course:{rows:Array.from({length:10},()=>({className:'',subject:'',day:'',weekday:'',period:'1-3',parttime:'V',tutorial:'',newDay:'',newWeekday:'',newPeriod:'2-4',substitute:'',selfPay:'',schoolPay:''}))}};
let current='course';
const block=(title,content)=>content,input=()=>'',dropdown=()=>'',courseDateSelect=()=>'',courseHours=()=>null,courseDateOptions=()=>[''];`;
const api=new Function(stub+helpers+editor+setter+';return {model,coursePeriodOptions,coursePeriodSelect,courseMark,courseMarkCheckbox,courseEditor,setPath};')();
const options=api.coursePeriodOptions();
check(options.length===46,'Expected blank plus 45 single/range choices');
check(new Set(options).size===46,'Duplicate choices');
for(let a=1;a<=9;a++)for(let b=a;b<=9;b++)check(options.includes(a===b?String(a):a+'-'+b),'Missing period');
check(api.coursePeriodOptions('舊自訂值').includes('舊自訂值'),'Old draft value lost');
for(const [value,expected] of [[true,'V'],[false,''],['V','V'],['v','V'],['',''],[' ',''],['false',''],['是','V']])check(api.courseMark(value)===expected,'Wrong V normalization');
for(const key of ['parttime','tutorial']){
 api.setPath('rows.0.'+key,true);check(api.model.course.rows[0][key]==='V','Checked value is not V');
 api.setPath('rows.0.'+key,false);check(api.model.course.rows[0][key]==='','Unchecked value is not blank');
 api.setPath('rows.0.'+key,true);
}
api.setPath('isHomeroom',true);check(api.model.course.isHomeroom===true,'Unrelated checkbox changed');
const html=api.courseEditor();
check((html.match(/<td>/g)||[]).length===140,'Expected 14 cells in each of 10 rows');
check((html.match(/type="checkbox"/g)||[]).length===21,'Expected 20 course marks plus homeroom');
check(html.includes('value="1-3" selected')&&html.includes('value="2-4" selected'),'Ranges not selected');
check(!html.includes('</td>>'),'Unexpected literal markup');
const restored=JSON.parse(JSON.stringify(api.model.course));
check(restored.rows[0].period==='1-3'&&restored.rows[0].parttime==='V','Draft data did not round-trip');
check(source.includes("[10,'兼課']")&&source.includes("[12,'輔導課']")&&source.includes("replaceCellDisplay(doc,cell,label,7)"),'Both headers must be 7pt');
console.log('PASS: syntax, 45 period choices, V normalization, HTML cells, draft values; actual browser/DOCX rendering still required.');
