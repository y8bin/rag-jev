"""Publication figures from completed local artifacts; no model calls or new inference."""
import os,json,csv,hashlib
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/chapter4-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image,ImageOps,ImageDraw
import numpy as np
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
S=ROOT/'results/koblex-reproduction-v1'; P=S/'chapter4-prep-v1'
A=json.loads((S/'analysis.json').read_text())
CE='parser_ce_fixed'; JV='parser_jev_fixed'; arms=[CE,JV]
COL=['#B64342','#0F4D92']; names=['CE','Jev']
plt.rcParams.update({'font.family':['DejaVu Sans'],'font.size':11,'axes.linewidth':1.3,'axes.spines.top':False,'axes.spines.right':False,'legend.frameon':False,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
manifest=[]
def save(fig,key,data,sources,caption):
 fig.tight_layout(pad=1.2)
 paths=[]
 for ext in ['pdf','svg','png']:
  p=OUT/f'{key}.{ext}';fig.savefig(p,dpi=600,bbox_inches='tight',pad_inches=.08,facecolor='white');paths.append(p)
 plt.close(fig)
 (OUT/f'{key}.data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 manifest.append({'figure':key,'caption_ko':caption,'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}})
def bars(ax,labels,vals,ylabel,ylim):
 x=np.arange(len(labels));w=.32
 for i,(v,c,n) in enumerate(zip(vals,COL,names)):
  b=ax.bar(x+(i-.5)*w,v,w,label=n,color=c,edgecolor='#272727',linewidth=.7,hatch='///' if i==0 else None)
  ax.bar_label(b,fmt='%.2f',padding=4,fontsize=10)
 ax.set_xticks(x,labels);ax.set_ylabel(ylabel);ax.set_ylim(0,ylim);ax.legend(loc='upper left',bbox_to_anchor=(0,1.17),ncol=2)
# 4.1 controlled comparison schematic
fig,ax=plt.subplots(figsize=(10,4));ax.axis('off');ax.set_xlim(0,10);ax.set_ylim(0,4)
def box(x,y,w,h,t,c='#F3F3F3'):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.06',facecolor=c,edgecolor='#4D4D4D',linewidth=1));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=10)
def arrow(x,y,u,v):ax.annotate('',xy=(u,v),xytext=(x,y),arrowprops={'arrowstyle':'->','color':'#4D4D4D','lw':1.4})
box(.1,1.55,1.4,.8,'226 questions\nShared inputs');box(1.95,1.55,1.7,.8,'Predicted statutes\n478 candidate pools');box(4.1,1.55,1.5,.8,'BM25\n100 / pool')
arrow(1.56,1.95,1.88,1.95);arrow(3.72,1.95,4.03,1.95)
box(6.1,2.65,1.5,.65,'CE reranking','#F6CFCB');box(6.1,.65,1.5,.65,'Jev reranking','#DBE7F4')
arrow(5.65,1.95,6.06,2.95);arrow(5.65,1.95,6.06,.95)
box(8.15,1.5,1.65,.9,'Top-10 / pool\nLLM selects 1\nAnswer generation')
arrow(7.67,2.95,8.1,2.15);arrow(7.67,.95,8.1,1.7)
ax.text(5,.1,'Matched candidates, selection model, generation model and evaluation',ha='center',fontsize=11)
save(fig,'fig_4_1_controlled_pipeline',{'questions':226,'candidate_pools':478,'candidates_per_pool':100,'shortlist_per_pool':10,'llm_selections_per_pool':1},[S/'analysis.json',S/'protocol-lock.json'],'동일한 입력·후보와 후속 LLM을 공유하는 CE/Jev 주 비교. 공개 코드 CE는 별도 재현 참조 조건이며 그림에서 생략하였다. 100·10·1은 pool별 개수다.')
# 4.2 evidence forest plot
metrics=['f1','recall','em','gold_set_coverage']; labs=['Evidence F1','Evidence recall','Exact match','Complete gold coverage'];data=[]
fig,ax=plt.subplots(figsize=(7,3.5))
for i,m in enumerate(metrics):
 c=next(c for c in A['comparisons'] if c['metric']==m and c['control']==CE and c['treatment']==JV);v=c['mean_difference']*100;lo,hi=np.array(c['ci95'])*100
 ax.errorbar(v,3-i,xerr=[[v-lo],[hi-v]],fmt='o',color=COL[1],capsize=4,markersize=6,lw=1.8)
 ax.text(6.2,3-i,f'{v:+.2f} [{lo:+.2f}, {hi:+.2f}]',va='center',fontsize=10)
 data.append({'metric':m,'difference_x100':v,'ci95_x100':[lo,hi]})
ax.axvline(0,color='#767676',ls='--',lw=1);ax.set_yticks(range(4),labs[::-1]);ax.set_xlim(-3.5,11.2);ax.set_xticks([-2,0,2,4,6]);ax.set_xlabel('Jev − CE (points; percentage points for binary rates)');ax.set_ylim(-.6,3.6)
save(fig,'fig_4_2_evidence_effects',data,[S/'analysis.json'],'최종 선택 근거의 Jev−수정 CE 차이. '+'막대는 151개 의존 그룹의 대응 bootstrap 10,000회로 산출한 탐색적 95% CI다. 다중 비교 무보정이며 EM·완전 회수율 구간은 0을 포함한다.')
# 4.3 shortlist quality
stage=list(csv.DictReader((P/'A4/stage-summary.csv').open())); vals=[];data=[]
for arm in arms:
 r=next(r for r in stage if r['arm']==arm and r['stage']=='shortlist');v=[float(r['macro_question_gold_recall'])*100,float(r['all_gold_question_rate'])*100];vals.append(v);data.append({'arm':arm,'macro_gold_recall_x100':v[0],'all_gold_question_rate_x100':v[1],'n':226})
fig,ax=plt.subplots(figsize=(6.5,3.8));bars(ax,['Gold recall\n(question mean)','All gold in shortlist\n(questions)'],vals,'Shortlist quality (%)',100)
save(fig,'fig_4_3_shortlist_quality',data,[P/'A4/stage-summary.csv'],'재정렬 후 상위 10개 후보 합집합의 정답 근거 유지 수준(226문항). Recall은 문항별 비가중 평균, 모든 gold 포함률은 문항 비율이다. 점추정만 표시한다. 지연은 최종 집계 미완료로 포함하지 않았다.')
# 4.4 answer quality + resources separate units panels
resources=list(csv.DictReader((P/'A5/descriptive-statistics.csv').open()))
def resource(arm,v):return float(next(r for r in resources if r['arm']==arm and r['variable']==v)['mean'])
fig,axes=plt.subplots(1,3,figsize=(11,3.8),gridspec_kw={'width_ratios':[1.6,1,1]});data={}
quality=[[A['summaries'][arm][m]*100 for m in ['token_f1','lf_eval']] for arm in arms]
bars(axes[0],['Token F1','LF-Eval'],quality,'Answer score (0–100)',100);axes[0].set_title('(a) Automatic quality',y=1.2,fontsize=12)
for ax,var,title in zip(axes[1:],['context_tokens','api_input_tokens'],['(b) Selected context','(c) Total API input']):
 v=[resource(a,var) for a in arms];b=ax.bar(names,v,color=COL,edgecolor='#272727',linewidth=.7);b[0].set_hatch('///');ax.bar_label(b,fmt='%.2f',padding=4,fontsize=10);ax.set_ylim(0,max(v)*1.25);ax.set_ylabel('Mean tokens / question');ax.set_title(title,y=1.2,fontsize=12);data[var]=v
 data['quality']=quality
save(fig,'fig_4_4_answer_quality_resources',data,[S/'analysis.json',P/'A5/descriptive-statistics.csv'],'최종 답변의 자동 품질과 생성 입력 요구량(226문항). 세 패널은 서로 다른 단위·축을 사용하며 막대는 0에서 시작한다. 캐시 재사용 행도 논리적 입력량에 포함한다. 신규 청구액·근거 주장 지지율이 아니며, 오차막대는 표시하지 않았다. 입력량 절감은 관찰되지 않았다.')
# 4.5 exclusive first-loss counts
labels=['No exact match\nin corpus','Missing from\nBM25 pools','Lost at\nreranking','Not selected\nfrom shortlist','Finally\nselected'];data=[];vals=[]
for arm in arms:
 rs={r['stage']:int(r['surviving_gold_occurrences']) for r in stage if r['arm']==arm};v=[443-rs['corpus'],rs['corpus']-rs['bm25'],rs['bm25']-rs['shortlist'],rs['shortlist']-rs['final'],rs['final']];assert sum(v)==443;vals.append(v);data.append({'arm':arm,'counts':dict(zip(labels,v)),'denominator':443})
fig,ax=plt.subplots(figsize=(9,3.8));bars(ax,labels,vals,'Gold occurrences (count)',300)
# use integer labels for counts
for t in ax.texts:t.set_text(t.get_text().split('.')[0])
save(fig,'fig_4_5_gold_loss_stages',data,[P/'A4/stage-summary.csv'],'문항별 gold 출현 443건을 최초 탈락 단계 또는 최종 선택으로 배타 분류한 결과. 같은 gold가 다른 문항에 필요하면 각각 센다. shortlist 이후 미선택에는 pool별 하나 선택 제약이 작용할 수 있으므로 법률 판단 오류로 단정하지 않는다.')
# provenance, captions, overview
meta={'skill':'scientific-figure-making','skill_snapshot':'research/chapter4/figures/skill-references/SKILL.md','upstream_commit':'b709de17da7e8f9a72e51a5de5bced924a01eeab','matplotlib':matplotlib.__version__,'new_model_calls':0,'new_statistical_tests':0,'figures':manifest}
(OUT/'provenance.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
md=['# 제4장 절별 논문 figure','', '완료된 기존 결과만 사용. PNG 600 dpi, 벡터 PDF/SVG, 그림별 원자료 JSON 제공. 영어 도표 레이블과 한국어 캡션을 사용한다. CE는 수정 CE다. 기존 원고·기존 그림은 변경하지 않았다.','']
for f in manifest:
 k=f['figure'];md += [f'## {k}','',f'![{k}]({k}.png)','',f['caption_ko'],'',f'[PDF]({k}.pdf) · [SVG]({k}.svg) · [원자료]({k}.data.json)','']
md += ['4.3 지연 비교는 최종 summary 및 완전한 대응 표본이 확보된 뒤 별도 갱신해야 한다. 4.1은 실험 조건 도식이며 결과 그래프가 아니다. 4.4는 사람 근거 충실도 또는 필터링 후 답변 평가 결과를 나타내지 않는다.','', '재현: `.venv/bin/python research/chapter4/figures/section-figures-v1/build_figures.py`']
(OUT/'README.md').write_text('\n'.join(md)+'\n')
thumbs=[]
for f in manifest:
 im=Image.open(OUT/(f['figure']+'.png')).convert('RGB');im.thumbnail((1100,440));cell=Image.new('RGB',(1160,490),'white');cell.paste(im,((1160-im.width)//2,35));ImageDraw.Draw(cell).text((20,10),f['figure'],fill='black');thumbs.append(cell)
canvas=Image.new('RGB',(1160,490*len(thumbs)),'#dddddd')
for i,im in enumerate(thumbs):canvas.paste(im,(0,i*490))
canvas.save(OUT/'overview.png')
print('Created',len(manifest),'figures in',OUT)
