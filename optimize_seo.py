#!/usr/bin/env python3
"""SEO update for DovanDarazi.github.io. Python 3.9+, standard library only.

Extract this package into the website folder, then run:
    python optimize_seo.py
Or specify the folder:
    python optimize_seo.py --site /path/to/DovanDarazi.github.io

Updates metadata in index.html without replacing CV content or design.
Preserves verification meta tags and files; replaces old JSON-LD with the
verified profile below. Adds robots.txt, sitemap.xml and legacy anchor support.
Backs up changed existing files to .seo-backups/. Does not publish or run Git.
Run again if you replace index.html with a different template. The CV updater
provided in this chat preserves this metadata automatically.
"""
import argparse
import datetime
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import sys

URL='https://dovandarazi.github.io/'
TITLE='Dovan Darazi | Physics Researcher & Graduate Student'
DESCRIPTION=('Dovan Darazi, physics graduate student and teaching assistant at the '
             'American University of Beirut. Research, publications, projects, and CV.')
VERIFY='google03d8efe08fb890e8.html'
VERIFICATION=b'google-site-verification: google03d8efe08fb890e8.html'

class Tag(HTMLParser):
    def __init__(self, tag):
        super().__init__(); self.attrs={}; self.feed(tag)
    def handle_starttag(self, tag, attrs):
        self.attrs=dict(attrs)


def remove_managed_tag(match):
    tag=match[0]; a=Tag(tag).attrs
    if tag.lower().startswith('<meta'):
        name=a.get('name','').lower(); prop=a.get('property','').lower()
        # Verification tokens, viewport, charset and other unrelated tags survive.
        if name in ('description','author','robots','googlebot','keywords') or name.startswith('twitter:') or prop.startswith('og:'):
            return ''
    else:
        rel=a.get('rel','').lower().split()
        if 'canonical' in rel or 'icon' in rel or 'apple-touch-icon' in rel:return ''
    return tag


def metadata():
    schema={
      '@context':'https://schema.org',
      '@graph':[
        {'@type':'WebSite','@id':URL+'#website','url':URL,'name':'Dovan Darazi','inLanguage':'en'},
        {'@type':'ProfilePage','@id':URL+'#profile','url':URL,'name':TITLE,
         'description':DESCRIPTION,'isPartOf':{'@id':URL+'#website'},
         'mainEntity':{'@id':URL+'#person'}},
        {'@type':'Person','@id':URL+'#person','name':'Dovan Darazi','url':URL,
         'jobTitle':'Physics graduate student and teaching assistant',
         'description':DESCRIPTION,
         'affiliation':{'@type':'CollegeOrUniversity','name':'American University of Beirut','url':'https://www.aub.edu.lb/'},
         'alumniOf':{'@type':'CollegeOrUniversity','name':'Lebanese University','url':'https://www.ul.edu.lb/'},
         'sameAs':['https://github.com/DovanDarazi','https://scholar.google.com/citations?user=SUrLchwAAAAJ'],
         'knowsAbout':['Particle physics','Plasma physics','Dark matter','Computational physics'],
         'knowsLanguage':['English','Arabic','French'],
         'mainEntityOfPage':{'@id':URL+'#profile'}}
      ]}
    e=lambda s:html.escape(s,quote=True)
    return '\n'+f'''<title>{e(TITLE)}</title>
<meta name="description" content="{e(DESCRIPTION)}">
<meta name="author" content="Dovan Darazi">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{URL}">
<meta property="og:type" content="profile">
<meta property="og:site_name" content="Dovan Darazi">
<meta property="og:title" content="{e(TITLE)}">
<meta property="og:description" content="{e(DESCRIPTION)}">
<meta property="og:url" content="{URL}">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="{URL}seo-assets/brand.jpg">
<meta property="og:image:alt" content="Dovan Darazi monogram">
<meta property="og:image:width" content="1024">
<meta property="og:image:height" content="1024">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(TITLE)}">
<meta name="twitter:description" content="{e(DESCRIPTION)}">
<meta name="twitter:image" content="{URL}seo-assets/brand.jpg">
<meta name="twitter:image:alt" content="Dovan Darazi monogram">
<link rel="icon" href="seo-assets/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="seo-assets/apple-touch-icon.png">
<script id="dovan-profile-data" type="application/ld+json">
{json.dumps(schema,ensure_ascii=False,indent=2)}
</script>
<script defer src="seo-assets/legacy-links.js"></script>
'''


def optimize(page):
    match=re.search(r'<head\b[^>]*>(.*?)</head>',page,re.S|re.I)
    if not match:raise ValueError('index.html has no head element.')
    head=match[1]
    head=re.sub(r'<title\b[^>]*>.*?</title>','',head,flags=re.S|re.I)
    head=re.sub(r'<script\b[^>]*>.*?</script>',lambda m:'' if Tag(m[0].split('>')[0]+'>').attrs.get('type','').lower()=='application/ld+json' or Tag(m[0].split('>')[0]+'>').attrs.get('src')=='seo-assets/legacy-links.js' else m[0],head,flags=re.S|re.I)
    head=re.sub(r'<(?:meta|link)\b[^>]*>',remove_managed_tag,head,flags=re.I)
    head=re.sub(r'(?:\n[ \t]*){2,}', '\n',head).strip()+'\n'+metadata()
    page=page[:match.start(1)]+head+page[match.end(1):]
    # Preserve the visual line break, while giving the name a text separator.
    page=page.replace('Dovan<br><em>','Dovan<br>\n<em>')
    return page


def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--site',type=Path,default=Path(__file__).resolve().parent)
    p.add_argument('--dry-run',action='store_true')
    o=p.parse_args();site=o.site.resolve();bundle=Path(__file__).resolve().parent
    target=site/'index.html'
    if not target.is_file():raise ValueError('Put this script beside index.html, or provide --site.')
    page=optimize(target.read_text(encoding='utf-8-sig'))
    # Check the complete output before touching the website.
    assert len(re.findall(r'<title\b',page,re.I))==1
    assert len(re.findall(r'<link\s+rel="canonical"',page,re.I))==1
    json.loads(re.search(r'<script id="dovan-profile-data"[^>]*>(.*?)</script>',page,re.S)[1])
    updates={target:page.encode('utf-8'),
      site/'robots.txt':f'User-agent: *\nAllow: /\n\nSitemap: {URL}sitemap.xml\n'.encode(),
      site/'sitemap.xml':f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url><loc>{URL}</loc></url>\n</urlset>\n'.encode(),
      site/VERIFY:VERIFICATION}
    for name in ['brand.jpg','favicon.ico','apple-touch-icon.png','legacy-links.js']:
        src=bundle/'seo-assets'/name
        if not src.is_file():raise ValueError('Missing bundled asset: '+str(src))
        updates[site/'seo-assets'/name]=src.read_bytes()
    changed={path:data for path,data in updates.items() if not path.exists() or path.read_bytes()!=data}
    if o.dry_run:print(f'Validated SEO update. {len(changed)} files would change; nothing written.');return
    if not changed:print('SEO is already up to date.');return
    backup=site/'.seo-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    for path in changed:
        if path.is_file():
            dest=backup/path.relative_to(site);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    for path,data in changed.items():
        path.parent.mkdir(parents=True,exist_ok=True)
        tmp=path.with_name(path.name+'.seo.tmp');tmp.write_bytes(data);tmp.replace(path)
    print(f'Updated {len(changed)} files. Existing content and verification tags preserved.')
    print('Backups: '+str(backup))
    print('Review and publish these files. Then submit sitemap.xml and request homepage indexing in Search Console.')

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,AssertionError) as e:
        print('Error: '+str(e),file=sys.stderr);sys.exit(1)
