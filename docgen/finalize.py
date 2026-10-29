# -*- coding: utf-8 -*-
"""Make the completed .docx ready to hand in.

Runs on the output of build_doc.py and changes presentation only:

  * the student's name and the date under the title on the first page, and in
    the file's author fields;
  * SQL blocks one point smaller, so the longest query lines fit on one line;
  * the Part IV account split into a heading and separate paragraphs with bold
    lead-ins, instead of one paragraph held together by line breaks;
  * the website and repository addresses as clickable links.

    python docgen/finalize.py [path/to/COMPLETED.docx]
"""
import datetime, html, os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content
from build_doc import PARA_RE, PPR_RE, esc, para_text, ROOT

DOCX = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    ROOT, "Analytics_mindset_PCard_assignment_COMPLETED.docx")

ARIAL = '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
LINKS = [content.PART4_WEBSITE, content.PART4_GITHUB]
# A paragraph of the Part IV account that opens with a short label sentence.
LEAD_RE = re.compile(r'^(Tab \d — [^.]+\.|[A-Z][a-zA-Z-]+(?: [a-zA-Z-]+){0,4}\.) ')


def run(text, rpr=''):
    return '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, esc(text))


def para(ppr, runs):
    return '<w:p>%s%s</w:p>' % (ppr, runs)


def with_links(text, rpr=''):
    """Runs for `text`, with every submission address turned into a hyperlink."""
    out, pos = [], 0
    pattern = '|'.join(re.escape(u) for u in LINKS)
    for m in re.finditer(pattern, text):
        if m.start() > pos:
            out.append(run(text[pos:m.start()], rpr))
        out.append('<w:hyperlink r:id="%s" w:history="1">%s</w:hyperlink>' % (
            LINK_IDS[m.group(0)], run(m.group(0), '<w:rPr><w:rStyle w:val="Hyperlink"/></w:rPr>')))
        pos = m.end()
    if pos < len(text):
        out.append(run(text[pos:], rpr))
    return ''.join(out)


def only(paras, test, what):
    hits = [p for p in paras if test(para_text(p))]
    if len(hits) != 1:
        sys.exit('%s: expected one paragraph, found %d' % (what, len(hits)))
    return hits[0]


with zipfile.ZipFile(DOCX) as z:
    names = z.namelist()
    blobs = {n: z.read(n) for n in names}

xml = blobs['word/document.xml'].decode('utf-8')
rels = blobs['word/_rels/document.xml.rels'].decode('utf-8')
styles = blobs['word/styles.xml'].decode('utf-8')
core = blobs['docProps/core.xml'].decode('utf-8')

if content.STUDENT_NAME in para_text(xml[:20000]):
    sys.exit('already finalized: %s' % DOCX)

# Relationship ids for the two links.
LINK_IDS = {}
for n, url in enumerate(LINKS, 1):
    rid = 'rIdSubmitLink%d' % n
    LINK_IDS[url] = rid
    rels = rels.replace('</Relationships>',
                        '<Relationship Id="%s" Type="http://schemas.openxmlformats.org/'
                        'officeDocument/2006/relationships/hyperlink" Target="%s" '
                        'TargetMode="External"/></Relationships>' % (rid, url))

paras = PARA_RE.findall(xml)

# 1. Name and date under the first-page title.
title = next(p for p in paras if para_text(p) == 'P-card')
ppr = PPR_RE.search(title).group(0)
today = datetime.date.today()
byline = 'Submitted by %s  ·  %d %s %d' % (
    content.STUDENT_NAME, today.day, today.strftime('%B'), today.year)
xml = xml.replace(title, title + para(ppr, run(byline, '<w:rPr>%s<w:sz w:val="20"/>'
                                                    '<w:szCs w:val="20"/></w:rPr>' % ARIAL)), 1)

# 2. The two submission bullets: addresses as links.
for label in ('A link to your live website:', 'A link to your GitHub repository:'):
    p = only(paras, lambda t: t.startswith(label), label)
    m = PPR_RE.search(p)
    xml = xml.replace(p, p[:p.index('>') + 1] + (m.group(0) if m else '')
                      + with_links(html.unescape(para_text(p))) + '</w:p>')

# 3. Part IV account: heading plus one paragraph per block.
p = only(paras, lambda t: t.startswith('Important — protect your API key'), 'Part IV note')
m = PPR_RE.search(p)
body_ppr = m.group(0) if m else ''
intro = html.unescape(para_text(re.sub(r'<w:br/>.*', '', p, flags=re.S)))
blocks = [para(body_ppr, run(intro))]
heading, rest = content.PART4_NOTE[0], content.PART4_NOTE[1:]
blocks.append(para('<w:pPr><w:pStyle w:val="ControlBlockTitle"/></w:pPr>', run(heading)))
for text in rest:
    lead = LEAD_RE.match(text)
    if lead:
        runs = run(lead.group(1), '<w:rPr><w:b/></w:rPr>') + with_links(text[lead.end(1):])
    else:
        runs = with_links(text)
    blocks.append(para('<w:pPr><w:pStyle w:val="ControlFieldText"/>'
                       '<w:spacing w:after="120"/></w:pPr>', runs))
xml = xml.replace(p, ''.join(blocks))

# 4. SQL blocks one point smaller (9 pt -> 8 pt).
style = re.search(r'<w:style [^>]*w:styleId="SQLQueryBlock".*?</w:style>', styles, re.S).group(0)
styles = styles.replace(style, style.replace('w:val="18"', 'w:val="16"'))

# 5. Author fields.
now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
core = re.sub(r'<dc:creator>.*?</dc:creator>', '<dc:creator>%s</dc:creator>' % content.STUDENT_NAME, core)
core = re.sub(r'<cp:lastModifiedBy>.*?</cp:lastModifiedBy>',
              '<cp:lastModifiedBy>%s</cp:lastModifiedBy>' % content.STUDENT_NAME, core)
core = re.sub(r'<dc:title>.*?</dc:title>', '<dc:title>Analytics mindset — P-card</dc:title>', core)
core = re.sub(r'(<dcterms:modified [^>]*>).*?(</dcterms:modified>)', r'\g<1>%s\g<2>' % now, core)

blobs['word/document.xml'] = xml.encode('utf-8')
blobs['word/_rels/document.xml.rels'] = rels.encode('utf-8')
blobs['word/styles.xml'] = styles.encode('utf-8')
blobs['docProps/core.xml'] = core.encode('utf-8')
tmp = DOCX + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
    for n in names:
        z.writestr(n, blobs[n])
os.replace(tmp, DOCX)
print('finalized', DOCX)
