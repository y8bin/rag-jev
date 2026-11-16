from pathlib import Path
import re
root = Path('research/chapter4')
s = (root / 'chapter4.md').read_text()
labels = {'tab-ch4-conditions': 'tab:ch4_conditions', 'tab-ch4-main-results': 'tab:ch4_main_results', 'tab-ch4-cases': 'tab:ch4_cases', 'fig-ch4-hop-f1': 'fig:ch4_hop_f1'}
section_labels = ['sec:ch4_conditions', 'sec:ch4_evidence_results', 'sec:ch4_subgroups', 'sec:ch4_answer_resources', 'sec:ch4_errors']
def inline(text):
    literals = []
    def keep(m):
        literals.append(m[1])
        return f'ZZCODE{len(literals)-1}ZZ'
    text = re.sub(r'`([^`]+)`', keep, text)
    refs = []
    def ref(m):
        refs.append(m[1].split()[0] + '~\\ref{' + labels[m[2]] + '}')
        return f'ZZREF{len(refs)-1}ZZ'
    text = re.sub(r'\[([^]]+)\]\(#([^)]+)\)', ref, text)
    text = re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', text)
    text = text.replace('%', r'\%').replace('&', r'\&').replace('_', r'\_')
    text = text.replace('Δ', r'$\Delta$').replace('→', r'$\to$').replace('−', r'$-$').replace('–', '--')
    text = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', text)
    for i, literal in enumerate(literals):
        text = text.replace(f'ZZCODE{i}ZZ', r'\texttt{' + literal.replace('_', r'\_') + '}')
    for i, ref in enumerate(refs):
        text = text.replace(f'ZZREF{i}ZZ', ref)
    return text
sections = re.split(r'^## 4\.\d ', s, flags=re.M)[1:]
for n, section in enumerate(sections, 1):
    title, _, body = section.partition('\n')
    output = [f'% 최종 축약본. chapter4.md와 같은 본문에서 생성.\n\\subsection{{{title}}}\n\\label{{{section_labels[n-1]}}}']
    pending_label = pending_caption = None
    for para in re.split(r'\n\s*\n', body.strip()):
        anchor = re.fullmatch(r'<a id="([^"]+)"></a>', para)
        if anchor:
            pending_label = labels[anchor[1]]
            continue
        caption = re.fullmatch(r'\*\*표 \d\. (.+)\*\*', para)
        if caption:
            pending_caption = caption[1]
            continue
        if para.startswith('|'):
            rows = [[c.strip() for c in line.split('|')[1:-1]] for line in para.splitlines()]
            rows.pop(1)
            cols = len(rows[0])
            tabular = [r'\begin{table}[htbp]', r'\centering', r'\caption{' + inline(pending_caption) + '}', r'\label{' + pending_label + '}', r'\small', r'\setlength{\tabcolsep}{3pt}', r'\begin{tabular}{@{}l' + ('r' * (cols-1) if n in (2,5) else 'l' * (cols-1)) + '@{}}', r'\hline']
            for index, row in enumerate(rows):
                if row[0].startswith('**') and all(not c for c in row[1:]):
                    tabular.append(r'\multicolumn{' + str(cols) + r'}{@{}l}{' + inline(row[0]) + r'} \\')
                else:
                    tabular.append(' & '.join(inline(c) for c in row) + r' \\')
                if index == 0:
                    tabular.append(r'\hline')
            tabular += [r'\hline', r'\end{tabular}', r'\end{table}']
            output.append('\n'.join(tabular))
            pending_label = pending_caption = None
        elif para.startswith('주: ') and output[-1].endswith(r'\end{table}'):
            note = '\\par\\smallskip\n\\begin{minipage}{\\linewidth}\\footnotesize\n' + inline(para[3:]) + '\n\\end{minipage}\n\\end{table}'
            output[-1] = output[-1][:-len(r'\end{table}')] + note
        elif para.startswith('!['):
            continue
        elif para.startswith('**그림 1.'):
            caption = re.fullmatch(r'\*\*그림 1\. (.+)\*\*', para)[1]
            output.append('\n'.join([r'\begin{figure}[htbp]', r'\centering', r'\includegraphics[width=\linewidth]{research/chapter4/figures/hop_f1.pdf}', r'\caption{' + inline(caption) + '}', r'\label{' + pending_label + '}', r'\end{figure}']))
            pending_label = None
        else:
            output.append(inline(para))
    (root / f'section4_{n}.tex').write_text('\n\n'.join(output) + '\n')
print('Markdown and five LaTeX fragments synchronized.')
