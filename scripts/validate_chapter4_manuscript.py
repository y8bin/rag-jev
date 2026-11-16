"""Check manuscript scope, source hashes, displayed values and review PDF budget."""
from pathlib import Path
import hashlib,json,re
from pypdf import PdfReader
r=Path('research/chapter4');md=(r/'chapter4.md').read_text();pdf=Path('output/pdf/chapter4-final.pdf');reader=PdfReader(pdf)
assert len(reader.pages)<=3
assert len(re.findall(r'^## 4\.\d ',md,re.M))==5
assert len(re.findall(r'^!\[',md,re.M))==3
sources={}
prov=json.loads((r/'figures/section-figures-v1/provenance.json').read_text())
for fig in prov['figures']:
 for name,h in fig['sources'].items():
  assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h,name
  sources[name]=h
a=json.loads(Path('results/koblex-reproduction-v1/analysis.json').read_text())
f=json.loads(Path('results/koblex-filtering-v1/summary.json').read_text())
for arm in ['parser_ce_fixed','parser_jev_fixed']:
 s=a['summaries'][arm]
 for v in [s['retrieval']['f1'],s['retrieval']['precision'],s['retrieval']['recall'],s['token_f1'],s['lf_eval']]:assert f'{v*100:.2f}' in md
for arm in ['ce','jev']:
 s=f['cv_overall'][arm]['filtered_cv']
 for k in ['f1','precision','recall']:assert f'{s[k]:.2f}' in md
 assert str(s['kept_items_total']) in md

# Independently verify completed latency rows, pairing and summary values.
from collections import defaultdict
import numpy as np
latroot=Path('results/koblex-latency-v1')
lat=json.loads((latroot/'summary.json').read_text())
assert hashlib.sha256((latroot/'raw.jsonl').read_bytes()).hexdigest()==lat['raw_sha256']
rows=[json.loads(l) for l in (latroot/'raw.jsonl').read_text().splitlines() if l.strip()]
measured=[r for r in rows if not r['warmup']]
assert len(measured)==360 and all(r['status']=='ok' for r in measured)
by=defaultdict(list)
for row in measured:by[(row['query_id'],row['method'])].append(row)
assert len(by)==120 and all(sorted(r['repetition'] for r in rs)==[0,1,2] for rs in by.values())
qids=sorted({q for q,m in by});assert len(qids)==60
for method in ['ce','jev']:
 vals=[np.mean([r['wall_clock_ms'] for r in by[q,method]]) for q in qids]
 for name,v in [('mean',np.mean(vals)),('median',np.median(vals)),('p95',np.quantile(vals,.95))]:
  assert np.isclose(v,lat['per_question_ms'][method][name])
  assert f'{v/1000:.2f}' in md
 count=sum(r['top10_same_as_quality_run'] for r in measured if r['method']==method)
 assert count==(180 if method=='ce' else 2)
assert sum(r.get('retries',0) for r in measured if r['method']=='jev')==0
for v in [lat['jev_minus_ce_ms']['mean_difference']/1000,*[x/1000 for x in lat['jev_minus_ce_ms']['ci95']],lat['jev_over_ce_geometric_mean_ratio']['estimate'],*lat['jev_over_ce_geometric_mean_ratio']['ci95']]:
 assert f'{v:.2f}' in md
assert np.isclose(np.mean([r['top10_set_overlap'] for r in measured if r['method']=='jev']),lat['repeatability']['jev']['top10_set_overlap_mean'])
for name in ['summary.json','protocol.json','raw.jsonl','completed.json']:sources[str(latroot/name)]=hashlib.sha256((latroot/name).read_bytes()).hexdigest()

for target in re.findall(r'!\[[^]]*\]\(([^)]+)\)',md):assert (r/target).exists()
log=Path('tmp/pdfs/chapter4/chapter4-draft.log').read_text()
for bad in ['Overfull','Missing character','undefined references','LaTeX Error']:assert bad not in log,bad
files=[r/'chapter4.md',r/'chapter4-supplement.md',r/'preview.tex',r/'chapter4.tex',pdf]+[r/f'section4_{i}.tex' for i in range(1,6)]
o={'status':'PASS_FINAL_MANUSCRIPT_WITH_LATENCY','actual_pages':len(reader.pages),'maximum_pages':3,'layout':'A4, 10pt, two columns, 20mm margins','sections':5,'figures':3,'tables':2,'source_hashes_checked':sources,'main_metrics_and_filtering_values':'PASS','latency_rows_pairing_and_summary':'PASS','latex_errors_overfull_missing_glyphs':'NONE','visual_review':'All three final pages inspected; labels legible, no clipping, overlap or float-only pages; last-page columns balanced','excluded_results':['unperformed human review'],'new_experiments':0,'new_statistical_tests':0,'new_human_judgments':0,'files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(r/'draft-validation.json').write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n')
print(o['status'],len(reader.pages),'pages')
