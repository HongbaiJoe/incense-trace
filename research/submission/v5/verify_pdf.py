from pathlib import Path
import json,re
import fitz
from pypdf import PdfReader
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parent
pdf=fitz.open(root/'xiangji_v5.pdf'); reader=PdfReader(root/'xiangji_v5.pdf',strict=True)
assert len(reader.pages)==len(pdf)==28
texts=[p.get_text() for p in pdf];whole='\n'.join(texts)
assert 'Hongbai Zhu' in whole and 'Experimental High School' in whole
assert '??' not in whole and '\ufffd' not in whole
assert '1.089' not in whole
figures={str(i+1):re.findall(r'Figure\s+(\d+)\.',t) for i,t in enumerate(texts) if re.search(r'Figure\s+\d+\.',t)}
for start in range(0,len(pdf),4):
 canvas=Image.new('RGB',(1200,1700),'#dadada')
 for j in range(4):
  k=start+j
  if k>=len(pdf):break
  pix=pdf[k].get_pixmap(matrix=fitz.Matrix(1,1)); im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples).convert('RGB');im.thumbnail((580,815))
  x=(j%2)*600+10;y=(j//2)*850+25;canvas.paste(im,(x,y));ImageDraw.Draw(canvas).text((x,y-20),str(k+1),fill='black')
 canvas.save(root/f'contact-{start+1:02d}.png')
result={'pages':len(pdf),'strict_parse':True,'missing_glyph_or_reference':False,'figure_pages':figures,'formula_labels':len(re.findall(r'\\label\{eq:',(root/'xiangji_v5.tex').read_text()))}
(root/'pdf_verification.json').write_text(json.dumps(result,indent=2));print(result)
