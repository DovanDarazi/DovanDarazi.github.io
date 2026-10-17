# Dovan Darazi — complete academic website

A static, dark website ready for GitHub Pages. No build step or Python packages required.

## Start here

1. Open index.html in a browser to preview the site.
2. Download the latest CV.tex and compiled CV.pdf from Overleaf.
3. In this folder run:

   python update_website.py "path/to/CV.tex" --pdf "path/to/CV.pdf"

   Or use the included source snapshot:

   python update_website.py cv-source/CV.tex --pdf "path/to/CV.pdf"

4. Preview index.html again, then upload/commit the website files to your existing DovanDarazi.github.io repository. Keep your repository's existing assets/files folder so old download URLs continue working.

Your actual latest Overleaf PDF was not available. The package intentionally does not display an old CV or a text CV as a replacement. The CV download appears after the command above copies your PDF into documents/dovan-darazi-cv.pdf. It is copied unchanged.

The included cv-source/CV.tex is a reconstructed source snapshot from the CV in our chat, including the BaBar thesis, GOLEM experiment and Ising project, and excluding extracurricular. If your Overleaf version has newer edits, use your Overleaf .tex instead.

## Add any other document

Copy a PDF, PowerPoint, ZIP, image, notebook, or other file into documents/. Then edit documents.js. Add an object to window.siteDocuments, separated from the previous object by a comma:

```javascript
{
  id: "ising-report",
  title: "Ising model report",
  description: "Statistical mechanics final project · PDF",
  file: "documents/ising-report.pdf",
  section: "monte-carlo-simulation-and-analysis-of-the-ising-model"
}
```

- title: what visitors see.
- description: a short label; optional.
- file: the relative path to the actual file. Do not add a leading slash. Case matters on GitHub Pages. Spaces and Unicode filenames are supported, though simple filenames are easier to manage.
- id: a short unique identifier used for direct document links.
- section: optional. Adds the same document under that project/experience as well as in the main Documents section. Click # next to an entry to get its ID from the URL.

For a document that belongs only in Documents, leave out section.

Your stereoscopic-imaging report and PowerPoint from the original repository are already included and configured. Click a document title to open it, or Download to save it. New documents are added by updating repository files; there is no online upload dashboard or private storage. Everything published in this site is public.

## CV downloads are separate

- cv-download.js is managed by the Python updater.
- documents.js is your editable list for all OTHER documents.
- Do not add the CV to documents.js. The script filters duplicate paths and the old generated CV text path as an extra safeguard.
- No text CV is created or offered by this version.
- Running without --pdf preserves an existing documents/dovan-darazi-cv.pdf.
- To remove the CV download intentionally, delete that PDF and run the updater again.

## Update the website from LaTeX

```bash
python update_website.py cv-source/CV.tex
```

The updater reads the restructured CV commands: cvsection, cventry, cvplainentry and StudyTopics. It does not execute LaTeX. Standard links, basic math, itemize lists and the supplied skill tables are supported. Unsupported commands produce an error before updating. PDF-only extraction is not supported; passing CV.pdf works only if matching CV.tex is beside it.

The .tex is authoritative for the CV sections. Entries removed from it disappear from the website; extracurricular is always omitted. The contact/hero header remains in index.html and is edited there.

- The section logos persist after every update.
- Existing matching entry IDs are retained where possible.
- Your general document list, files, design and SEO remain intact.
- If you rename/remove an entry, review its section value in documents.js.
- Backups are created in .cv-backups/ before changes.
- Use --dry-run to check the input without writing files.

## Logo and direct links

The numbered section labels are replaced by your existing DD logo at seo-assets/brand.jpg. All headings still have a # link. Click it and copy the browser URL.

Examples after publication:

- https://dovandarazi.github.io/#stereoscopic-diagnostics
- https://dovandarazi.github.io/#documents
- https://dovandarazi.github.io/#document-stereoscopic-report
- https://dovandarazi.github.io/#document-stereoscopic-presentation

The older professional-experience anchor remains. Other old section names are mapped by seo-assets/legacy-links.js where an equivalent section exists.

## SEO

SEO has already been applied. Keep these files when publishing:

- index.html (canonical URL, description, social metadata and structured data)
- robots.txt and sitemap.xml
- google03d8efe08fb890e8.html (original Google verification file)
- seo-assets/

If you replace the homepage template, run:

```bash
python optimize_seo.py
```

This preserves your page content and makes backups in .seo-backups/. Future CV updates preserve SEO automatically. Edit the profile details in optimize_seo.py when your academic status changes.

After publishing, open https://search.google.com/search-console/, select https://dovandarazi.github.io/, submit sitemap.xml and request indexing of the homepage. Verification and SEO do not guarantee any particular Google ranking.

## Files

- index.html — complete CV webpage.
- styles.css — responsive dark design and section logos.
- script.js — general downloads, per-project downloads and navigation.
- documents.js — YOUR document list; edit this to add documents.
- cv-download.js — generated CV PDF configuration.
- documents/ — included imaging files and your future documents.
- cv-source/CV.tex — complete editable source snapshot from this chat.
- update_website.py — CV-to-website updater, Python 3.9+.
- optimize_seo.py — SEO maintenance, Python 3.9+.
- seo-assets/ — logo, icons and compatibility links.
- robots.txt, sitemap.xml and google03d8efe08fb890e8.html — search visibility files.
- .gitignore — excludes updater backups and LaTeX build byproducts.
- .nojekyll — plain static publishing on GitHub Pages.

When merging into an existing checkout, merge .gitignore entries rather than discarding your existing ignore rules. Do not delete unrelated repository files. No deployment or Git commands are run by these Python scripts.

## Verification

Checked source completeness against the earlier site, all 22 CV entries, section logos, document file paths, JavaScript syntax, Google verification bytes, JSON-LD/sitemap validity, and updater behavior. Confirmed that subsequent updates preserve logos and SEO, retain custom documents, and expose only one CV PDF. Browser rendering was not verified in this environment.
