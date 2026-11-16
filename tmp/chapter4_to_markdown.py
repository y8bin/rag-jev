"""Export the current chapter fragments as editable GitHub-flavored Markdown."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path('research/chapter4')
SOURCES = [ROOT / f'section4_{n}.tex' for n in range(1, 6)]
ORIGINAL_HASHES = {str(p): sha256(p.read_bytes()).hexdigest() for p in SOURCES}
LABELS = {
    'tab:ch4_conditions': ('표 1', 'tab-ch4-conditions'),
    'tab:ch4_main_results': ('표 2', 'tab-ch4-main-results'),
    'tab:ch4_cases': ('표 3', 'tab-ch4-cases'),
    'fig:ch4_hop_f1': ('그림 1', 'fig-ch4-hop-f1'),
}


def inline(text):
    text = re.sub(r'\\texttt\{([^}]+)\}', lambda m: '`' + m[1].replace(r'\_', '_') + '`', text)
    text = re.sub(r'\\textbf\{([^}]+)\}', r'**\1**', text)
    text = text.replace(r'\%', '%').replace(r'\_', '_')
    text = text.replace(r'\Delta', 'Δ').replace(r'\to', ' → ').replace(r'\,', ' ')
    text = text.replace('10^{-12}', '10⁻¹²').replace('$', '')
    text = text.replace('--', '–')
    return re.sub(r'\s+', ' ', text).strip()


def table(match):
    text = match[0]
    caption = inline(re.search(r'\\caption\{(.*?)\}\s*\\label', text, re.S)[1])
    label = re.search(r'\\label\{([^}]+)\}', text)[1]
    title, anchor = LABELS[label]
    body = re.search(r'\\begin\{tabular\}[^\n]*\n(.*?)\\end\{tabular\}', text, re.S)[1]
    rows = []
    for row in body.split(r'\\'):
        row = row.replace(r'\hline', '').strip()
        if not row:
            continue
        if row.startswith(r'\multicolumn'):
            group = re.search(r'\\textbf\{([^}]+)\}', row)[1]
            rows.append(['**' + group + '**'] + [''] * (len(rows[0]) - 1))
        else:
            rows.append([inline(cell) for cell in row.split('&')])
    assert len(set(map(len, rows))) == 1
    lines = [f'<a id="{anchor}"></a>', '', f'**{title}. {caption}**', '']
    for i, row in enumerate(rows):
        lines.append('| ' + ' | '.join(row) + ' |')
        if i == 0:
            lines.append('| ' + ' | '.join(['---'] * len(row)) + ' |')
    note = re.search(r'\\begin\{minipage\}\{\\linewidth\}\s*\\footnotesize(.*?)\\end\{minipage\}', text, re.S)
    if note:
        chunks = [inline(s) for s in note[1].split(r'\\') if s.strip()]
        lines += ['', '주: ' + chunks[0]]
        if len(chunks) > 1:
            lines += [''] + ['- ' + s for s in chunks[1:]]
    return '\n'.join(lines) + '\n'


def figure(match):
    text = match[0]
    caption = inline(re.search(r'\\caption\{(.*?)\}\s*\\label', text, re.S)[1])
    label = re.search(r'\\label\{([^}]+)\}', text)[1]
    title, anchor = LABELS[label]
    return f'<a id="{anchor}"></a>\n\n![공식 hop별 최종 근거 F1](figures/hop_f1.png)\n\n**{title}. {caption}**\n'


def convert(source, number):
    text = re.sub(r'(?<!\\)%[^\n]*', '', source)
    text = re.sub(r'\\begin\{table\}.*?\\end\{table\}', table, text, flags=re.S)
    text = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', figure, text, flags=re.S)
    text = re.sub(r'\\subsection\{([^}]+)\}', rf'## 4.{number} \1', text)
    text = re.sub(r'\\label\{[^}]+\}', '', text)
    for label, (title, anchor) in LABELS.items():
        prefix = title.split()[0]
        text = text.replace(prefix + r'~\ref{' + label + '}', f'[{title}](#{anchor})')
    paragraphs = []
    for paragraph in re.split(r'\n\s*\n', text.strip()):
        if paragraph.startswith(('|', '<a ', '![', '- ')):
            paragraphs.append(paragraph)
        else:
            paragraphs.append(inline(paragraph))
    return '\n\n'.join(paragraphs)


def main():
    sections = [convert(p.read_text(), n) for n, p in enumerate(SOURCES, 1)]
    header = '<!-- 2026-11-09 문체 수정본의 Markdown 편집용 버전. 출처: section4_1.tex–section4_5.tex. -->\n\n# 4. 실험 결과 및 분석\n\n'
    md = header + '\n\n'.join(sections) + '\n'
    output = ROOT / 'chapter4.md'
    output.write_text(md)
    assert len(re.findall(r'^## 4\.[1-5] ', md, re.M)) == 5
    assert len(re.findall(r'^\| ---', md, re.M)) == 3
    assert len(re.findall(r'^!\[', md, re.M)) == 1
    assert not re.search(r'\\(?:begin|end|ref|label|caption|subsection|texttt|multicolumn|Delta|to)\b', md)
    assert (ROOT / 'figures/hop_f1.png').is_file()
    assert all(f'id="{anchor}"' in md for _, anchor in LABELS.values())
    numeric = lambda s: Counter(re.findall(r'\d+\.\d+', s))
    source_numbers = numeric('\n'.join(re.sub(r'(?<!\\)%[^\n]*', '', p.read_text()) for p in SOURCES))
    assert numeric(md) == source_numbers + Counter({'4.1': 1, '4.2': 1, '4.3': 1, '4.4': 1, '4.5': 1})
    assert all(sha256(Path(p).read_bytes()).hexdigest() == h for p, h in ORIGINAL_HASHES.items())
    print(json.dumps({'output': str(output), 'sections': 5, 'tables': 3, 'figures': 1, 'decimal_values_and_repetitions_preserved': True, 'source_files_unchanged': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
