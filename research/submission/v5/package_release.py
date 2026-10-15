"""Package reproducible V5 deliverables without caches, credentials or old drafts."""
from pathlib import Path
import argparse, hashlib, json, shutil, zipfile

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent.parent

def allowed(p):
    return (not any(x in {'.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache', '.wrangler', 'dist', 'tmp'} for x in p.parts)
            and not p.name.startswith(('.env', 'qa-page-', 'contact-'))
            and p.name != 'page1.png'
            and p.suffix not in {'.pyc', '.aux', '.log', '.out', '.tsbuildinfo', '.DS_Store'})

def write_zip(path, entries):
    manifest = {}
    entries = list({name: file for file, name in entries}.items())
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, file in sorted(entries):
            if not file.is_file() or not allowed(file): continue
            z.write(file, name)
            manifest[name] = hashlib.sha256(file.read_bytes()).hexdigest()
        z.writestr('SHA256_MANIFEST.json', json.dumps(manifest, indent=2, ensure_ascii=False))
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
    return {'files': len(manifest), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--site', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args(); args.output.mkdir(parents=True, exist_ok=True)
    report={}
    paper=[(p, 'xiangji-v5/'+p.relative_to(HERE).as_posix()) for p in HERE.rglob('*') if p.is_file() and not p.name.startswith('original_v4')]
    report['Xiangji_V5_LaTeX.zip']=write_zip(args.output/'Xiangji_V5_LaTeX.zip',paper)
    folders=['src','tests','data','experiments','configs','protocol','ontology','literature','manuscript','reports','submission/v5']
    entries=[]
    for folder in folders:
        entries.extend((p,'research/'+p.relative_to(RESEARCH).as_posix()) for p in (RESEARCH/folder).rglob('*') if p.is_file())
    entries.extend((RESEARCH/name,'research/'+name) for name in ['pyproject.toml','uv.lock','README.md','Makefile'])
    # Older audit tests consume these small coordinate/manifest assets.
    entries.extend((p,'research/'+p.relative_to(RESEARCH).as_posix()) for p in (RESEARCH/'figures').rglob('*') if p.is_file() and p.suffix in {'.json','.csv'})
    # Retain the exact legacy release assets checked by the inherited test suite.
    # Do not silently drop those tests or include hundreds of MB of unused TIFFs.
    from xiangji.freeze_cycle5 import FILES as cycle5_files
    from xiangji.freeze_cycle6 import FILES as cycle6_files
    from xiangji.mathematical_audit import TEX, WORD
    for name in set(cycle5_files) | set(cycle6_files):
        entries.append((RESEARCH/name, 'research/'+name))
    entries.extend((p,'research/'+p.relative_to(RESEARCH).as_posix()) for p in (TEX,WORD))
    report['Xiangji_V5_Reproducibility.zip']=write_zip(args.output/'Xiangji_V5_Reproducibility.zip',entries)
    site_entries=[(p,'website/'+p.relative_to(args.site).as_posix()) for p in args.site.rglob('*')
                  if p.is_file() and '.impeccable/review' not in p.as_posix()]
    report['Xiangji_Website_Source.zip']=write_zip(args.output/'Xiangji_Website_Source.zip',site_entries)
    shutil.copy2(HERE/'xiangji_v5.pdf',args.output/'Xiangji_V5.pdf')
    for name in ['JOURNAL_AND_SUBMISSION.md','CHANGES_AND_FIVE_ANSWERS.md','REPRODUCE.md']:
        shutil.copy2(HERE/name,args.output/name)
    (args.output/'PACKAGE_MANIFEST.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
