"""Single-column (85 mm) variants from the same completed figure data."""
from pathlib import Path
import os,json
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/chapter4-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=Path(__file__).resolve().parent
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.linewidth':.8,'axes.spines.top':False,'axes.spines.right':False,'legend.frameon':False,'pdf.fonttype':42,'svg.fonttype':'none'})
def save(f,n):
 f.tight_layout(pad=.5)
 for e in ['pdf','png','svg']:f.savefig(R/(n+'_column.'+e),dpi=600,bbox_inches='tight',pad_inches=.03)
 plt.close(f)
d=json.loads((R/'fig_4_2_evidence_effects.data.json').read_text());f,a=plt.subplots(figsize=(3.35,2.0))
for i,r in enumerate(d):
 v=r['difference_x100'];l,h=r['ci95_x100'];a.errorbar(v,3-i,xerr=[[v-l],[h-v]],fmt='o',color='#0F4D92',capsize=2,ms=4,lw=1.2)
a.axvline(0,color='#767676',ls='--',lw=.8);a.set_yticks(range(4),['Complete coverage','Exact match','Evidence recall','Evidence F1']);a.set_xlim(-3.7,6.5);a.set_xlabel('Jev − CE (points / percentage points)');a.set_ylim(-.5,3.5);save(f,'fig_4_2_evidence_effects')
d=json.loads((R/'fig_4_3_shortlist_quality.data.json').read_text());f,a=plt.subplots(figsize=(3.35,2.0));x=np.arange(2)
for i,r in enumerate(d):
 v=[r['macro_gold_recall_x100'],r['all_gold_question_rate_x100']];b=a.bar(x+(i-.5)*.34,v,.34,color=['#B64342','#0F4D92'][i],label=['CE','Jev'][i],edgecolor='#272727',lw=.5,hatch='///' if i==0 else None);a.bar_label(b,fmt='%.2f',padding=3,fontsize=7)
a.set_xticks(x,['Gold recall','All gold retained']);a.set_ylim(0,100);a.set_ylabel('Shortlist quality (%)');a.legend(ncol=2,loc='upper left',fontsize=7);save(f,'fig_4_3_shortlist_quality')
d=json.loads((R/'fig_4_5_gold_loss_stages.data.json').read_text());f,a=plt.subplots(figsize=(3.35,2.25));y=np.arange(5)
for i,r in enumerate(d):
 b=a.barh(y+(i-.5)*.34,list(r['counts'].values()),.34,color=['#B64342','#0F4D92'][i],label=['CE','Jev'][i],edgecolor='#272727',lw=.5,hatch='///' if i==0 else None);a.bar_label(b,padding=2,fontsize=7)
a.set_yticks(y,['No corpus match','BM25 miss','Reranking loss','Selection loss','Final selection']);a.invert_yaxis();a.set_xlim(0,295);a.set_xlabel('Gold occurrences (n = 443 / method)');a.legend(ncol=2,loc='upper right',fontsize=7);save(f,'fig_4_5_gold_loss_stages')
