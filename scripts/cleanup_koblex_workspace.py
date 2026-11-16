"""User-authorized removal of obsolete experiments; preserve current science."""
from pathlib import Path
import hashlib
import json
import shutil
import sqlite3
import time
from datetime import datetime,timezone

BASE=Path.cwd().resolve()
ROOT=BASE/'results/koblex-reproduction-v1'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def save(path,data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def main():
    manifest=ROOT/'cleanup-manifest.json'
    if manifest.exists():raise RuntimeError('Cleanup already applied; do not delete again')
    lock=json.loads((ROOT/'protocol-lock.json').read_text())
    runtime=json.loads((ROOT/'runtime-settings.json').read_text())
    # Preserve scientific outputs, including response caches, byte-for-byte.
    preserved={}
    for p in ROOT.rglob('*'):
        if p.is_file() and (p.parent==ROOT or p.parts[-3] in ('metrics','lf-eval') or 'predictions' in p.parts or 'human-review' in p.parts):
            if p.name not in ('legacy-preservation.json','preflight-lock-before-parser-test-fix.json','retrieval-comparison.json','final-status.json'):
                preserved[str(p.relative_to(BASE))]=sha(p)
    old_up=BASE/'.omo/evidence/koblex-design-20261108/upstream'
    new_up=BASE/'data/koblex/upstream'
    assert not new_up.exists()
    path_map={}
    for p in old_up.rglob('*'):
        if p.is_file():path_map[str(p.relative_to(BASE))]=str((new_up/p.relative_to(old_up)).relative_to(BASE))
    # Scripts from this experiment are executed scientific provenance, not legacy runs.
    names=['run_koblex_reproduction.py','run_koblex_reproduction_answers.py',
           'run_koblex_reproduction_answers_paced.py','run_koblex_reproduction_lf_parallel.py']
    provenance=ROOT/'provenance/executed-scripts';provenance.mkdir(parents=True,exist_ok=True)
    for name in names+['audit_koblex_reproduction.py']:
        p=BASE/'scripts'/name;target=provenance/name
        shutil.copy2(p,target)
        path_map[str(p)]=str(target.relative_to(BASE))
        path_map[str(p.relative_to(BASE))]=str(target.relative_to(BASE))
    for p,h in lock['signature']['files'].items():assert sha(p)==h,('Input changed before cleanup',p)
    # Current CPU/MPS probe inputs are retained independently of the removed Vector run.
    probe=json.loads((ROOT/'ce-numerics.json').read_text())
    with (BASE/'results/koblex-paper/primary-v1/raw.jsonl').open() as f:
        for line in f:
            row=json.loads(line)
            if row['query_id']==probe['query_id'] and row['method']=='ce_r':break
    qa={q['id']:q for q in map(json.loads,(old_up/'experiments/source/koblex.jsonl').open())}
    save(ROOT/'ce-numerics-inputs.json',{'query_id':probe['query_id'],'question':qa[probe['query_id']]['question'],
         'candidate_texts':[c['text'] for c in row['candidates'][:8]],'scope':'Inputs used only for current numeric sanity probe'})
    shutil.move(str(old_up),str(new_up))
    # Compact pre-study calls to carried balances without resetting either cap.
    old_db=BASE/'.omo/evidence/koblex-paper-budget/ledger.sqlite'
    new_db=ROOT/'budget/ledger.sqlite';new_db.parent.mkdir(exist_ok=True)
    assert not new_db.exists()
    with sqlite3.connect(old_db) as source,sqlite3.connect(new_db) as db:
        source.backup(db)
        opening=db.execute('SELECT rowid,kind,actual FROM calls ORDER BY rowid LIMIT 19587').fetchall()
        assert len(opening)==19587 and all(r[2] is not None for r in opening)
        assert abs(sum(r[2] for r in opening)-7.130966722)<1e-9
        before=db.execute('SELECT SUM(COALESCE(actual,reserved)),SUM(actual IS NULL),COUNT(*) FROM calls').fetchone()
        balances={kind:sum(r[2] for r in opening if r[1]==kind) for kind in sorted({r[1] for r in opening})}
        db.execute('PRAGMA secure_delete=ON')
        db.execute('DELETE FROM calls WHERE rowid<=?',(opening[-1][0],))
        for kind,value in balances.items():
            db.execute('INSERT INTO calls VALUES(?,?,?,?,?,?)',('opening_balance_'+kind,kind,'OPENING_BALANCE_BEFORE_CURRENT_STUDY',value,value,time.time()))
        db.commit();db.execute('VACUUM')
        after=db.execute('SELECT SUM(COALESCE(actual,reserved)),SUM(actual IS NULL),COUNT(*) FROM calls').fetchone()
        assert abs(before[0]-after[0])<1e-8 and before[1]==after[1]
        assert db.execute('SELECT limit_usd FROM budget').fetchone()[0]==100
        assert db.execute("SELECT limit_usd FROM service_budgets WHERE service='openai'").fetchone()[0]==37
    removed=[];removed_bytes=0
    def remove(path):
        nonlocal removed_bytes
        p=Path(path)
        if not p.is_absolute():p=BASE/p
        assert p.parent!=p and p.is_relative_to(BASE) and '.git' not in p.relative_to(BASE).parts
        if not p.exists() and not p.is_symlink():return
        size=sum(f.lstat().st_size for f in p.rglob('*') if f.is_file() and not f.is_symlink()) if p.is_dir() and not p.is_symlink() else p.lstat().st_size
        removed_bytes+=size;removed.append(str(p.relative_to(BASE)))
        if p.is_dir() and not p.is_symlink():shutil.rmtree(p)
        else:p.unlink()
    for p in (BASE/'results').iterdir():
        if p!=ROOT:remove(p)
    for name in ['legacy-preservation.json','preflight-lock-before-parser-test-fix.json','retrieval-comparison.json']:remove(ROOT/name)
    for p in (BASE/'data').iterdir():
        if p.name!='koblex':remove(p)
    remove(BASE/'indexes')
    for p in (BASE/'configs').iterdir():remove(p)
    research_keep={'KOBLEX_REPRODUCTION_AUDIT_20261109.md','KOBLEX_REPRODUCTION_HUMAN_REVIEW.md',
      'KOBLEX_REPRODUCTION_RESULTS_20261109.md','KOBLEX_REPRODUCTION_RUNBOOK.md',
      'koblex_source_audit_20261108.json','koblex-lf-environment.json','koblex-main-environment.json',
      'requirements-python312-macos-arm64.txt','prompts'}
    for p in (BASE/'research').iterdir():
        if p.name not in research_keep:remove(p)
    for p in (BASE/'research/prompts').iterdir():
        if p.name!='koblex_lf_eval.json':remove(p)
    script_keep={'koblex.py','cleanup_koblex_workspace.py','audit_koblex_reproduction.py','analyze_koblex_human_review.py'}
    for p in (BASE/'scripts').iterdir():
        if p.name not in script_keep:remove(p)
    test_keep={'conftest.py','test_koblex_preparation.py','test_koblex_analysis.py','test_koblex_timing.py',
               'test_koblex_reproduction.py','test_koblex_human_review.py','test_provider_budget.py'}
    for p in (BASE/'tests').iterdir():
        if p.name not in test_keep:remove(p)
    unused=['annotation','evaluation','kbl','lexical','readiness','reports','viewer']
    for name in unused:remove(BASE/f'src/legal_rag_jev/{name}.py')
    remove(BASE/'src/legal_rag_jev/viewer_static')
    for p in (BASE/'.cache').iterdir():
        if p.name not in {'models','tiktoken','koblex-reproduction-deps'}:remove(p)
    model=BASE/'.cache/models/models--dragonkue--bge-reranker-v2-m3-ko'
    reachable={p.resolve() for p in model.rglob('*') if p.is_symlink() and p.is_file()}
    for p in (BASE/'.cache/models').iterdir():
        if p.name.startswith('models--') and p!=model:remove(p)
    shared=BASE/'.cache/models/blobs'
    for p in list(shared.rglob('*')):
        if p.is_file() and p.name!='.huggingface-shared-blobs' and p.resolve() not in reachable:remove(p)
    assert all(p.exists() for p in reachable),'Required CE weights removed'
    for name in ['.omo','.impeccable','.deepeval','.pytest_cache','examples','schemas','.env','.env.example',
      'DESIGN.md','PRODUCT.md','EXPERIMENT_READINESS.md','EXPERIMENT_REQUIREMENTS_AUDIT.md','GETTING_STARTED.md',
      'OPENAI_SETUP.md','PAPER_VALIDATION_RUNBOOK.md','final_research_strategy.md',
      'legal_rag_jev_experiment_design (1).md','legal_rag_jev_paper_design.md']:
        remove(BASE/name)
    # Hash the retained execution-time runtime sources; old UI/CLI were not used by this study.
    retained_runtime={p:h for p,h in runtime['source_sha256'].items() if Path(p).exists() and Path(p).name!='cli.py'}
    for p,h in retained_runtime.items():assert sha(p)==h
    preserved={p:h for p,h in preserved.items() if Path(p).exists()}
    for p,h in preserved.items():assert sha(p)==h,('Scientific result changed',p)
    save(manifest,{'status':'POST_EXECUTION_CLEANUP','created_at_utc':datetime.now(timezone.utc).isoformat(),
        'scientific_results_changed':False,'execution_lock_replaced':False,'path_map':path_map,
        'retained_execution_runtime':retained_runtime,'current_files':{},'preserved_results':preserved,
        'budget_opening_balance':balances,'old_request_records_deleted':19587,
        'current_request_records_retained':after[2]-len(balances),'unsettled_requests_retained':after[1],
        'removed_paths':removed,'removed_regular_file_bytes':removed_bytes,
        'unused_runtime_modules_removed':unused+['cli (replaced with current entry point)']})
    print({'removed_paths':len(removed),'removed_GiB':round(removed_bytes/1024**3,2),
           'current_requests_preserved':after[2]-len(balances),'unsettled_requests_preserved':after[1]})

def remove_installed_automation():
    import os
    import subprocess
    label=f'gui/{os.getuid()}/com.codex.koblex-overnight'
    state=subprocess.run(['launchctl','print',label],capture_output=True,text=True)
    if state.returncode==0:
        subprocess.run(['launchctl','bootout',label],capture_output=True,text=True)
        state=subprocess.run(['launchctl','print',label],capture_output=True,text=True)
        if state.returncode==0:raise RuntimeError('Old automation is still loaded; do not remove its executable')
    files=[Path.home()/'Library/LaunchAgents/com.codex.koblex-overnight.plist',
           Path.home()/'Library/LaunchAgents/koblex_overnight_resume.zsh']
    for p in files:p.unlink(missing_ok=True)
    manifest=ROOT/'cleanup-manifest.json';data=json.loads(manifest.read_text())
    data['installed_automation_removed']=[str(p) for p in files]
    data['old_launchd_job_absent']=True
    save(manifest,data)
    print('Old launchd job absent; two installed automation files removed')

if __name__=='__main__':
    import sys
    if '--remove-installed-automation' in sys.argv:remove_installed_automation()
    else:main()
