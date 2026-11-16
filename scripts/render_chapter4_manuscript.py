"""Synchronize the Korean chapter Markdown to LaTeX and build the review PDF."""
import re,subprocess,shutil
from pathlib import Path
R=Path('research/chapter4')
def inline(s):
 s=s.replace('\\','\\textbackslash{}').replace('&',r'\&').replace('%',r'\%').replace('_',r'\_').replace('#',r'\#')
 s=s.replace('−',r'$-$').replace('→',r'$\to$').replace('Δ',r'$\Delta$')
 s=re.sub(r'`([^`]+)`',r'\\texttt{\1}',s)
 return s
sections=re.split(r'^## 4\.\d ',(R/'chapter4.md').read_text(),flags=re.M)[1:]
# Map the readable Markdown numbers ("그림 1", "표 2") to LaTeX labels so the PDF uses \ref.
labels={}
for n,s in enumerate(sections,1):
 for kind,num in re.findall(r'^\*\*(그림|표) (\d+)\.',s,flags=re.M):
  key=(kind,num);base=('fig' if kind=='그림' else 'tab')+':ch4_'+str(n);lab=base;i=1
  while lab in labels.values():i+=1;lab=base+chr(96+i)
  labels[key]=lab
def refs(s):return re.sub(r'(?<![가-힣])(그림|표) (\d+)',lambda m:m[1]+r'~\ref{'+labels[(m[1],m[2])]+'}' if (m[1],m[2]) in labels else m[0],s)
for n,s in enumerate(sections,1):
 title,_,body=s.partition('\n');parts=[r'\subsection{'+inline(title)+'}',r'\label{sec:ch4_'+str(n)+'}'];pending=None;caption=None
 for para in re.split(r'\n\s*\n',body.strip()):
  if para.startswith('!['):pending=re.search(r'\]\(([^)]+)\)',para)[1];continue
  if para.startswith('**그림 '):
   num=re.match(r'^\*\*그림 (\d+)\.',para)[1];text=re.sub(r'^\*\*그림 \d+\. |\*\*$','',para);path=(R/pending).with_suffix('.pdf').as_posix();wide=False
   env='figure*' if wide else 'figure'
   parts.append('\n'.join([r'\begin{'+env+'}[H]',r'\centering',r'\includegraphics[width=\linewidth]{'+path+'}',r'\caption{'+inline(text)+'}',r'\label{'+labels[('그림',num)]+'}',r'\end{'+env+'}']));continue
  if para.startswith('**표 '):tnum=re.match(r'^\*\*표 (\d+)\.',para)[1];caption=re.sub(r'^\*\*표 \d+\. |\*\*$','',para);continue
  if para.startswith('|'):
   rows=[[c.strip() for c in l.split('|')[1:-1]] for l in para.splitlines()];rows.pop(1)
   t=[r'\begin{table}[H]',r'\centering',r'\caption{'+inline(caption)+'}',r'\label{'+labels[('표',tnum)]+'}',(r'\scriptsize' if len(rows[0])>7 else r'\footnotesize' if len(rows[0])>5 else r'\small'),r'\setlength{\tabcolsep}{'+('1.5pt' if len(rows[0])>7 else '2.5pt' if len(rows[0])>5 else '3pt')+'}',r'\begin{tabular}{@{}l'+'r'*(len(rows[0])-1)+'@{}}',r'\hline']
   for i,row in enumerate(rows):
    t.append(' & '.join(inline(c) for c in row)+r' \\')
    if i==0:t.append(r'\hline')
   t += [r'\hline',r'\end{tabular}',r'\end{table}'];parts.append('\n'.join(t));continue
  parts.append(refs(inline(para)))
 (R/f'section4_{n}.tex').write_text('\n\n'.join(parts)+'\n')
Path('tmp/pdfs/chapter4').mkdir(parents=True,exist_ok=True)
for _ in range(2):
 p=subprocess.run(['xelatex','-interaction=nonstopmode','-halt-on-error','-jobname=chapter4-draft','-output-directory=tmp/pdfs/chapter4','research/chapter4/preview.tex'],capture_output=True,text=True)
 Path('tmp/pdfs/chapter4/authoring-build.log').write_text(p.stdout+p.stderr)
 if p.returncode:raise SystemExit(p.stdout[-4000:])
shutil.copy2('tmp/pdfs/chapter4/chapter4-draft.pdf','output/pdf/chapter4-draft.pdf')
shutil.copy2('output/pdf/chapter4-draft.pdf','output/pdf/chapter4-final.pdf')
print(p.stdout[-650:])
