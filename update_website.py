#!/usr/bin/env python3
"""Update Dovan's dark GitHub Pages website from the structured LaTeX CV.

Python 3.9+; no packages to install.

    python update_website.py CV.tex --site ./my-website
    python update_website.py CV.tex --site ./my-website --pdf CV.pdf
    python update_website.py CV.tex --site ./my-website --dry-run

Place this script in the website folder to omit --site.
Input is the restructured CV with \\cvsection, \\cventry,
\\cvplainentry, and \\StudyTopics commands, as supplied in our chat.
The older free-form CV layout is not supported: use the restructured version.

LaTeX is parsed, never executed. PDF alone cannot reliably reconstruct entries;
if passed a PDF, this script looks for a .tex file with the same base name.
A supplied PDF is copied as the downloadable CV, not compiled or extracted.

Updates index.html and cv-download.js; optionally copies the PDF.
Preserves CSS, JavaScript, the contact/hero header, and your other documents.
The CV PDF is separate from documents.js, which holds all other documents.
Every run backs up files it changes to .cv-backups/<timestamp>/.
This script does not run git or publish anything. Push changes yourself.

The .tex file is authoritative: removed entries disappear from the website.
Extracurricular is always omitted. Keep section/entry titles and descriptions
stable to retain their anchors. Existing anchors are reused when matching entries.
Unsupported commands raise an error before any website file is changed.
"""
import argparse
import datetime as dt
import hashlib
import json
import html
from html.parser import HTMLParser
import re
import shutil
import sys
from pathlib import Path


def comments(text):
    lines = []
    for line in text.splitlines():
        for i, c in enumerate(line):
            if c == '%' and (len(line[:i]) - len(line[:i].rstrip('\\'))) % 2 == 0:
                line = line[:i]
                break
        lines.append(line)
    return '\n'.join(lines)


def group(text, pos, opening='{', closing='}'):
    while pos < len(text) and text[pos].isspace():
        pos += 1
    if pos >= len(text) or text[pos] != opening:
        raise ValueError('Expected ' + opening + ' near: ' + text[pos:pos+70])
    start = pos + 1
    depth = 1
    pos += 1
    while pos < len(text):
        if text[pos] == '\\':
            pos += 2
            continue
        if text[pos] == opening:
            depth += 1
        elif text[pos] == closing:
            depth -= 1
            if depth == 0:
                return text[start:pos], pos+1
        pos += 1
    raise ValueError('Unclosed group near: ' + text[start:start+60])


def args(text, pos, count):
    values = []
    for _ in range(count):
        value, pos = group(text, pos)
        values.append(value)
    return values, pos


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, data):
        self.parts.append(data)


def plain(markup):
    p = TextOnly(); p.feed(markup)
    return re.sub(r'\s+', ' ', ''.join(p.parts)).strip()


def slug(text):
    s = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return s or 'entry'


def key(*parts):
    return re.sub(r'[^a-z0-9]', '', ' '.join(parts).lower().replace('june','jun').replace('sept','sep'))


SECTION_IDS = {
    'researchinterests':'research-interests', 'researchinterest':'research-interests',
    'academichistory':'education', 'education':'education',
    'researchexperience':'professional-experience', 'professionalexperience':'professional-experience',
    'researchexperienceandprojects':'professional-experience',
    'publicationsandpresentations':'publications', 'academicawards':'awards',
    'teachingandmentoringexperience':'teaching', 'teachingandmentoring':'teaching',
    'technicalskills':'skills', 'projects':'projects', 'academicprojects':'projects',
    'workshopsconferencesandschools':'events', 'studiedtopics':'studied-topics',
    'onlinecourses':'courses', 'certifications':'certifications', 'languages':'languages',
}


class Existing(HTMLParser):
    """Recover stable article anchors from the supplied website."""
    def __init__(self):
        super().__init__(); self.records=[]; self.current=None; self.capture=None; self.skip=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='article':
            self.current={'id':a.get('id'), 'title':'', 'date':'', 'desc':''}
        if not self.current: return
        if tag=='h3': self.capture='title'
        if 'date' in a.get('class','').split(): self.capture='date'
        if tag=='p' and 'context' in a.get('class','').split(): self.capture='desc'
        if 'permalink' in a.get('class','').split(): self.skip=True
    def handle_endtag(self, tag):
        if tag=='a': self.skip=False
        if tag in ('h3','p','span'): self.capture=None
        if tag=='article' and self.current:
            self.records.append(self.current); self.current=None
    def handle_data(self, data):
        if self.current and self.capture and not self.skip:
            self.current[self.capture]+=data


class Renderer:
    def __init__(self, records):
        self.records=records
        self.used=set()
        self.count=0
    def entry(self, values, bullets=True):
        title,date,desc=values[:3]
        title,date,desc=map(self.render,(title,date,desc))
        ident=None
        for record in self.records:
            if (record['id'] not in self.used and key(record['title'],record['date'],record['desc']) == key(plain(title),plain(date),plain(desc))):
                ident=record['id']; break
        if not ident:
            # A date or description edit should not break a unique entry's link.
            candidates=[r for r in self.records if r['id'] not in self.used
                        and key(r['title'],r['desc']) == key(plain(title),plain(desc))]
            if len(candidates)==1:
                ident=candidates[0]['id']
            else:
                candidates=[r for r in self.records if r['id'] not in self.used
                            and key(r['title']) == key(plain(title))]
                if len(candidates)==1:
                    ident=candidates[0]['id']
        if not ident:
            ident=slug(plain(title))
            # Distinguish multiple roles with the same title.
            if ident in self.used:
                ident+='-'+hashlib.sha256(key(plain(title),plain(date),plain(desc)).encode()).hexdigest()[:8]
        if ident in self.used:
            raise ValueError('Duplicate CV entry: '+plain(title))
        self.used.add(ident);self.count+=1
        result=f'<article class="entry" id="{ident}"><div class="entry-heading"><h3>{title} <a class="permalink" href="#{ident}" aria-label="Link to this entry">#</a></h3><span class="date">{date}</span></div>'
        if desc.strip(): result+=f'<p class="context">{desc}</p>'
        if bullets:
            detail=values[3].strip()
            if detail:
                result+=self.render('\\begin{itemize}'+detail+'\\end{itemize}')
        return result+'</article>'

    def render(self,text):
        out=[];i=0
        while i<len(text):
            c=text[i]
            if c=='{':
                value,i=group(text,i);out.append(self.render(value));continue
            if c=='}': raise ValueError('Unexpected closing brace in CV text')
            if c=='$':
                end=i+1
                while end<len(text) and (text[end]!='$' or text[end-1]=='\\'):end+=1
                if end==len(text):raise ValueError('Unclosed inline math')
                out.append('<span class="math">'+self.render(text[i+1:end])+'</span>');i=end+1;continue
            if c in '^_':
                i+=1
                if i<len(text) and text[i]=='{':value,i=group(text,i)
                else:value=text[i:i+1];i+=1
                tag='sup' if c=='^' else 'sub'
                out.append(f'<{tag}>{self.render(value)}</{tag}>');continue
            if c!='\\':
                if c=='~':out.append('&nbsp;')
                elif text[i:i+3]=='---':out.append('—');i+=3;continue
                elif text[i:i+2]=='--':out.append('–');i+=2;continue
                else:out.append(html.escape(c))
                i+=1;continue
            i+=1
            if i>=len(text):raise ValueError('Trailing backslash')
            if not text[i].isalpha():
                c=text[i];i+=1
                if c=='\\':
                    out.append('<br>')
                    if i<len(text) and text[i]=='[':_,i=group(text,i,'[',']')
                elif c in '&%_#$ {}':out.append(html.escape(c))
                elif c in ',;!:':out.append(' ')
                else:raise ValueError('Unsupported LaTeX escape: \\'+c)
                continue
            m=re.match(r'[A-Za-z]+',text[i:]);cmd=m[0];i+=len(cmd)
            if cmd in ('cventry','cvplainentry','AcademicAward'):
                v,i=args(text,i,4 if cmd=='cventry' else 3)
                out.append(self.entry(v,cmd=='cventry'))
            elif cmd=='StudyTopics':
                v,i=args(text,i,2)
                out.append('<div class="topic"><h3>'+self.render(v[0])+'</h3><p>'+self.render(v[1])+'</p></div>')
            elif cmd in ('textbf','emph','textit','textnormal','textrm','texttt','mbox','mathrm','mathbf'):
                v,i=group(text,i)
                tag={'textbf':'strong','mathbf':'strong','emph':'em','textit':'em','texttt':'code'}.get(cmd,'span')
                out.append(f'<{tag}>'+self.render(v)+f'</{tag}>')
            elif cmd=='textcolor':
                v,i=args(text,i,2);out.append(self.render(v[1]))
            elif cmd in ('href','url'):
                v,i=args(text,i,2 if cmd=='href' else 1)
                url=re.sub(r'\\([#%&_])',r'\1',v[0]).strip()
                if re.match(r'(?i)(javascript|data|vbscript):',url):raise ValueError('Unsafe URL scheme')
                label=self.render(v[1]) if cmd=='href' else html.escape(url)
                out.append('<a href="'+html.escape(url,quote=True)+'">'+label+'</a>')
            elif cmd=='begin':
                env,i=group(text,i)
                if env in ('tabular','tabularx'):
                    _,i=args(text,i,2 if env=='tabularx' else 1)
                elif env in ('table','minipage'):
                    while i<len(text) and text[i].isspace():i+=1
                    if i<len(text) and text[i]=='[':_,i=group(text,i,'[',']')
                    if env=='minipage':_,i=group(text,i)
                endtag='\\end{'+env+'}'
                # Find the matching end, including nested environments.
                depth=1;start=i;end=None
                pattern=re.compile(r'\\(begin|end)\{'+re.escape(env)+r'\}')
                for match in pattern.finditer(text,i):
                    depth+=1 if match[1]=='begin' else -1
                    if depth==0:end=match.start();i=match.end();break
                if end is None:raise ValueError('Unclosed environment: '+env)
                content=text[start:end]
                if env=='itemize':
                    parts=self.split_items(content)
                    if not parts and content.strip():raise ValueError('Use \\item inside the fourth cventry argument')
                    out.append('<ul>'+''.join('<li>'+self.render(p)+'</li>' for p in parts)+'</ul>')
                elif env in ('tabular','tabularx'):
                    rows=re.split(r'\\\\(?:\[[^\]]*\])?',content)
                    rendered=[]
                    for row in rows:
                        if not row.strip():continue
                        cells=re.split(r'(?<!\\)&',row)
                        rendered.append('<tr>'+''.join('<td>'+self.render(cell)+'</td>' for cell in cells)+'</tr>')
                    out.append('<div style="overflow-x:auto"><table style="width:100%;text-align:left;border-spacing:0 8px">'+''.join(rendered)+'</table></div>')
                elif env in ('table','minipage','quote','center'):
                    out.append(self.render(content))
                else:raise ValueError('Unsupported environment: '+env)
            elif cmd in ('vspace','hspace','addvspace','Needspace'):
                if i<len(text) and text[i]=='*':i+=1
                _,i=group(text,i)
            elif cmd in ('noindent','centering','raggedleft','raggedright','hfill','hrule','newpage','clearpage','bfseries','large','Large','small','footnotesize','normalsize','hline','toprule','midrule','bottomrule'):
                out.append(' ')
            elif cmd in ('par','smallskip','medskip','bigskip'):
                out.append('<br><br>')
            elif cmd in ('LaTeX','TeX'):
                out.append(cmd)
            elif cmd in {'Xi','xi','pi','gamma','Gamma','Lambda','lambda','mu','nu','tau','Delta','delta','alpha','beta','theta','sigma','Sigma','Omega','omega','rightarrow','to','pm','times','bar'}:
                symbols={'Xi':'Ξ','xi':'ξ','pi':'π','gamma':'γ','Gamma':'Γ','Lambda':'Λ','lambda':'λ','mu':'μ','nu':'ν','tau':'τ','Delta':'Δ','delta':'δ','alpha':'α','beta':'β','theta':'θ','sigma':'σ','Sigma':'Σ','Omega':'Ω','omega':'ω','rightarrow':'→','to':'→','pm':'±','times':'×'}
                if cmd=='bar':
                    v,i=group(text,i);out.append('<span style="text-decoration:overline">'+self.render(v)+'</span>')
                else:out.append(symbols[cmd])
            else:raise ValueError('Unsupported LaTeX command: \\'+cmd+' (no website changes made)')
        return ''.join(out)

    @staticmethod
    def split_items(text):
        starts=[];depth=0
        for m in re.finditer(r'\\begin\{itemize\}|\\end\{itemize\}|\\item\b',text):
            if m[0].startswith('\\begin'):depth+=1
            elif m[0].startswith('\\end'):depth-=1
            elif depth==0:starts.append((m.start(),m.end()))
        if starts and text[:starts[0][0]].strip():raise ValueError('Text before first \\item')
        return [text[end:(starts[n+1][0] if n+1<len(starts) else len(text))] for n,(_,end) in enumerate(starts)]


def read_sections(source):
    text=comments(source)
    start=text.find('\\begin{document}')
    if start>=0:text=text[start+len('\\begin{document}'):]
    text=text.split('\\end{document}')[0]
    matches=list(re.finditer(r'\\cvsection\b',text))
    if not matches:
        raise ValueError('No \\cvsection commands found. Use the restructured CV from our chat (not the older free-form layout).')
    result=[]
    for n,m in enumerate(matches):
        title,pos=group(text,m.end())
        end=matches[n+1].start() if n+1<len(matches) else len(text)
        result.append((title,text[pos:end]))
    return result


def atomic_write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.cv-sync.tmp')
    try:
        temp.write_bytes(data);temp.replace(path)
    finally:
        if temp.exists():temp.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source',type=Path,help='Your structured .tex CV (or a PDF with matching .tex beside it)')
    parser.add_argument('--site',type=Path,default=Path(__file__).resolve().parent,help='Website folder containing index.html')
    parser.add_argument('--pdf',type=Path,help='Optional compiled PDF to publish as the downloadable CV')
    parser.add_argument('--dry-run',action='store_true',help='Validate and report without changing files')
    opt=parser.parse_args()
    source=opt.source.resolve();site=opt.site.resolve();pdf=opt.pdf.resolve() if opt.pdf else None
    if source.suffix.lower()=='.pdf':
        pdf=pdf or source;source=source.with_suffix('.tex')
        if not source.is_file():raise ValueError('PDF-only import is not supported. Export/download the .tex source and put it beside the PDF with the same base name.')
    if not source.is_file():raise ValueError('Source not found: '+str(source))
    if pdf and (not pdf.is_file() or not pdf.read_bytes().startswith(b'%PDF-')):
        raise ValueError('The supplied PDF is missing or is not a PDF file.')
    index=site/'index.html'
    if not index.is_file():raise ValueError('index.html not found in '+str(site))
    page=index.read_text(encoding='utf-8')
    existing=Existing();existing.feed(page)
    renderer=Renderer(existing.records)
    sections=[];used=set();skipped=[]
    for raw_title,content in read_sections(source.read_text(encoding='utf-8-sig')):
        title=plain(renderer.render(raw_title))
        k=key(title)
        if k in ('extracurricular','extracurricularactivities','documents'):
            skipped.append(title);continue
        ident=SECTION_IDS.get(k,slug(title))
        if ident in used:raise ValueError('Duplicate section ID: '+ident)
        used.add(ident)
        rendered=renderer.render(content).strip()
        sections.append((ident,title,rendered))
    if not sections or renderer.count==0:
        raise ValueError('No CV entries found. Expected \\cventry or \\cvplainentry.')
    section_matches=list(re.finditer(r'<section\b[^>]*>.*?</section>',page,re.S))
    if not section_matches:raise ValueError('Website has no section elements to update')
    docs=next((m[0] for m in section_matches if re.search(r'\bid=[\"\']documents[\"\']',m[0])),None)
    if not docs:raise ValueError('Expected the Documents section from the supplied website')
    # Remove only our previous dedicated link. The custom document list is preserved.
    docs=re.sub(r'<a\b[^>]*\bid="cv-sync-download"[^>]*>.*?</a>','',docs,flags=re.S)
    docs=re.sub(r'<header class="section-title"><span>\d+</span>', '<header class="section-title"><img class="section-logo" src="seo-assets/brand.jpg" alt="" width="32" height="32">', docs,count=1)
    download_pdf=bool(pdf) or (site/'documents/dovan-darazi-cv.pdf').is_file()
    cv_config={'title':'Curriculum vitae','description':'Complete CV · PDF','file':'documents/dovan-darazi-cv.pdf'} if download_pdf else None
    cv_markup='<a class="document" href="documents/dovan-darazi-cv.pdf" download><span><strong>Curriculum vitae</strong><small>Complete CV · PDF</small></span><span>Download ↓</span></a>' if download_pdf else ''
    docs=re.sub(r'<div id="cv-download">.*?</div>',lambda _: '<div id="cv-download">'+cv_markup+'</div>',docs,flags=re.S)
    html_sections='\n'.join(f'<section id="{ident}" aria-labelledby="title-{ident}"><header class="section-title"><img class="section-logo" src="seo-assets/brand.jpg" alt="" width="32" height="32"><h2 id="title-{ident}">{html.escape(title)}</h2><a class="permalink" href="#{ident}" aria-label="Link to section">#</a></header>{body}</section>' for n,(ident,title,body) in enumerate(sections,1))
    first,last=section_matches[0].start(),section_matches[-1].end()
    page=page[:first]+html_sections+'\n'+docs+page[last:]
    nav=''.join(f'<a href="#{ident}">{html.escape(title)}</a>' for ident,title,_ in sections)+'<a href="#documents">Documents</a>'
    page,n=re.subn(r'(<nav\b[^>]*>).*?(</nav>)',lambda m:m[1]+nav+m[2],page,count=1,flags=re.S)
    if n!=1:raise ValueError('Expected the sidebar navigation in index.html')
    # Remove any legacy text-download hiding rule from older versions.
    page=re.sub(r'<!-- cv-sync: hide duplicate default CV card -->.*?<!-- /cv-sync -->','',page,flags=re.S)
    # Check the generated IDs and internal links before any changes.
    ids=re.findall(r'\bid="([^"]+)"',page)
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate HTML IDs; website not changed')
    broken=set(re.findall(r'href="#([^"]+)"',page))-set(ids)
    if broken:raise ValueError('Internal links would break: '+', '.join(sorted(broken))+'. Keep the relevant section or update its link in index.html first.')
    updates={index:page.encode('utf-8'),site/'cv-download.js':('// Managed by update_website.py. Add your PDF with --pdf.\nwindow.siteCV = '+json.dumps(cv_config,ensure_ascii=False,indent=2)+';\n').encode('utf-8')}
    if pdf:updates[site/'documents/dovan-darazi-cv.pdf']=pdf.read_bytes()
    removed={r['id'] for r in existing.records}-renderer.used
    print(f'Parsed {len(sections)} sections and {renderer.count} entries.')
    if skipped:print('Skipped: '+', '.join(skipped))
    if removed:print('Old entry anchors no longer present: '+', '.join(sorted(removed)))
    if download_pdf and not pdf:print('Note: existing PDF retained; pass --pdf with a newly compiled PDF to refresh it.')
    for ident,title,_ in sections:print('  #'+ident+' — '+title)
    changed={p:b for p,b in updates.items() if not p.exists() or p.read_bytes()!=b}
    if opt.dry_run:
        print(f'Dry run: {len(changed)} file(s) would change. Nothing written.');return
    if not changed:print('Already up to date.');return
    backup=site/'.cv-backups'/dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    for path in changed:
        if path.exists():
            dest=backup/path.relative_to(site);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    for path,data in changed.items():atomic_write(path,data)
    print('Updated '+str(len(changed))+' file(s). Backups: '+str(backup))
    print('Preview index.html, then commit and push your website changes when ready.')


if __name__=='__main__':
    try:main()
    except (ValueError,OSError) as exc:
        print('Error: '+str(exc),file=sys.stderr);sys.exit(1)
