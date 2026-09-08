# -*- coding: utf-8 -*-
"""Fill the P-card assignment .docx with the Part II / Part III answers."""
import re, shutil, sys, zipfile, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SRC = os.environ.get(
    "PCARD_DOCX",
    os.path.join(os.path.dirname(ROOT), "Analytics_mindset_case_studies_PCard_assignment.docx"))
OUT = os.environ.get(
    "PCARD_DOCX_OUT",
    os.path.join(ROOT, "Analytics_mindset_PCard_assignment_COMPLETED.docx"))
SQLDIR = os.path.join(ROOT, "sql")

PARA_RE = re.compile(r'<w:p(?:\s[^>]*)?(?:/>|>.*?</w:p>)', re.S)
TEXT_RE = re.compile(r'<w:t(?:\s[^>]*)?>(.*?)</w:t>', re.S)
PPR_RE  = re.compile(r'<w:pPr>.*?</w:pPr>', re.S)


def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def para_text(p):
    return ''.join(TEXT_RE.findall(p))


def runs_from_lines(lines, rpr=''):
    """One run holding the lines separated by hard line breaks."""
    parts = []
    for i, line in enumerate(lines):
        if i:
            parts.append('<w:br/>')
        if line:
            parts.append('<w:t xml:space="preserve">%s</w:t>' % esc(line))
    return '<w:r>%s%s</w:r>' % (rpr, ''.join(parts))


def rebuild(p, lines, rpr=''):
    """Keep the paragraph's properties, replace its content with `lines`."""
    m = PPR_RE.search(p)
    ppr = m.group(0) if m else ''
    tag = p[:p.index('>') + 1]
    if tag.endswith('/>'):
        tag = tag[:-2] + '>'
    return tag + ppr + runs_from_lines(lines, rpr) + '</w:p>'


def sql_text(name):
    with open(os.path.join(SQLDIR, name + '.sql'), encoding='utf-8') as fh:
        return fh.read().rstrip('\n').split('\n')


def main():
    with zipfile.ZipFile(SRC) as z:
        names = z.namelist()
        blobs = {n: z.read(n) for n in names}

    xml = blobs['word/document.xml'].decode('utf-8')
    paras = PARA_RE.findall(xml)
    if not paras:
        sys.exit('no paragraphs found')

    # Counters for the placeholders, consumed in document order.
    sql_order = ['qry_T2_Question%d' % i for i in range(1, 15)] + \
                ['qry_T3_Question%d' % i for i in range(1, 9)]
    res_order = [('T2', i) for i in range(1, 15)] + [('T3', i) for i in range(1, 9)]
    ic_titles = [8, 9, 10, 11, 12, 13, 14]
    fr_titles = [5, 6, 7, 8]

    n_sql = n_res = n_ic = n_fr = 0
    n_links = n_note = 0
    n_ictest = n_frtest = 0
    ictest_order = [8, 9, 10, 11, 12, 13, 14]
    frtest_order = [5, 6, 7, 8]

    out = xml
    replacements = []

    for p in paras:
        t = para_text(p)

        # 1. SQL query placeholders: "Question1" .. "Question14", then 1..8 again.
        if re.fullmatch(r'Question\d+', t.strip()):
            qname = sql_order[n_sql]; n_sql += 1
            replacements.append((p, rebuild(p, sql_text(qname))))
            continue

        # 2. Results and conclusion placeholders.
        if t.strip() == '[Enter results and conclusion]':
            part, num = res_order[n_res]; n_res += 1
            src = content.T2_RESULTS if part == 'T2' else content.T3_RESULTS
            lines = []
            for i, para in enumerate(src[num]):
                if i:
                    lines.append('')
                lines.append(para)
            replacements.append((p, rebuild(p, lines)))
            continue

        # 3. Student-defined control / question headings.
        if 'Student-defined internal-control test' in t:
            num = ic_titles[n_ic]; n_ic += 1
            replacements.append((p, rebuild(p, ['Control %d  |  %s' % (num, content.T2_TITLES[num])])))
            continue
        if 'Student-defined fraud test' in t:
            num = fr_titles[n_fr]; n_fr += 1
            replacements.append((p, rebuild(p, ['Question %d  |  %s' % (num, content.T3_TITLES[num])])))
            continue

        # 4. "Test to perform and desired output" bodies for the student-defined items.
        if t.startswith("Define the student"):
            num = ictest_order[n_ictest]; n_ictest += 1
            replacements.append((p, rebuild(p, [content.T2_TESTS[num]])))
            continue
        if t.startswith("Define and perform"):
            num = frtest_order[n_frtest]; n_frtest += 1
            replacements.append((p, rebuild(p, [content.T3_TESTS[num]])))
            continue

        # 5. Part IV: fill the two links in on the lines that ask for them, and
        #    hang the account of what was built off the last paragraph.
        if t.strip() == 'A link to your live website.':
            n_links += 1
            replacements.append((p, rebuild(
                p, ['A link to your live website:  ' + content.PART4_WEBSITE])))
            continue
        if t.strip() == 'A link to your GitHub repository.':
            n_links += 1
            replacements.append((p, rebuild(
                p, ['A link to your GitHub repository:  ' + content.PART4_GITHUB])))
            continue
        if t.startswith('Important — protect your API key'):
            n_note += 1
            lines = [t]
            for para in content.PART4_NOTE:
                lines.append('')
                lines.append(para)
            replacements.append((p, rebuild(p, lines)))
            continue

    for old, new in replacements:
        idx = out.find(old)
        if idx < 0:
            sys.exit('paragraph not found while replacing')
        out = out[:idx] + new + out[idx + len(old):]

    print('replaced: %d sql, %d results, %d control titles, %d question titles, '
          '%d control tests, %d question tests, %d part IV links, %d part IV note'
          % (n_sql, n_res, n_ic, n_fr, n_ictest, n_frtest, n_links, n_note))
    assert (n_sql, n_res, n_ic, n_fr, n_ictest, n_frtest, n_links, n_note) == \
        (22, 22, 7, 4, 7, 4, 2, 1), 'placeholder count mismatch'

    blobs['word/document.xml'] = out.encode('utf-8')
    if os.path.exists(OUT):
        os.remove(OUT)
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, blobs[n])
    print('wrote', OUT)


if __name__ == '__main__':
    main()
