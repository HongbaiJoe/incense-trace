"""Export editable figure sources and exact plotted coordinates from final TeX."""
from pathlib import Path
import re,csv,json
root=Path(__file__).resolve().parent
text=(root/'xiangji_v5.tex').read_text()
out=root/'editable_figures';out.mkdir(exist_ok=True)
style=text[text.index('\\usepackage{sansmath}'):text.index('\\usepackage{bm}')]
header=r'\documentclass[tikz,border=8pt]{standalone}'+'\n'+r'\usepackage{amsmath,amssymb,bm}'+'\n'+style+'\n'+r'\newcommand{\logit}{\operatorname{logit}}\newcommand{\expit}{\operatorname{expit}}'+'\n'+r'\begin{document}'+'\n'
manifest=[]
for i,match in enumerate(re.finditer(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}',text,re.S),1):
    body=match.group();(out/f'figure-{i}.tex').write_text(header+body+'\n'+r'\end{document}'+'\n')
    (out/f'figure-{i}.tikz').write_text(body+'\n')
    rows=[]
    for series,coords in enumerate(re.findall(r'coordinates\s*\{([^}]+)\}',body),1):
        for point in re.findall(r'\(([^()]*)\)',coords):
            xy=point.split(',');rows.append([series,*xy])
    with (out/f'figure-{i}-coordinates.csv').open('w') as f:
        writer=csv.writer(f);writer.writerow(['plot_series','x','y']);writer.writerows(rows)
    manifest.append({'figure':i,'source':f'figure-{i}.tex','coordinate_rows':len(rows)})
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(manifest)
