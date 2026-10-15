"""Build V5 from the supplied V4 without changing the source artifact."""
from pathlib import Path
import json,re,shutil,hashlib
from reconcile_weak import reconcile

HERE=Path(__file__).resolve().parent
R=HERE.parent.parent
ROOT=R.parents[2]
source=HERE/'original_v4.tex'
if not source.exists():raise FileNotFoundError('Place original_v4.tex beside this script.')
text=source.read_text()
for ext in ('tex','pdf'):
    target=HERE/('original_v4.'+ext)
    if source.with_suffix('.'+ext).resolve()!=target.resolve():shutil.copy2(source.with_suffix('.'+ext),target)
template=ROOT/'work/mdpi-acs-2026/Definitions'
if template.exists():shutil.copytree(template,HERE/'Definitions',dirs_exist_ok=True)
if not (HERE/'Definitions/logo-mdpi.pdf').exists():raise FileNotFoundError('Missing bundled Definitions/logo-mdpi.pdf')
end=text.index('%  ---------------- END MDPI-STYLE LAYOUT ----------------')
text='\\documentclass[applsci,article,submit,oneauthor]{Definitions/mdpi}\n'+text[end:].split('\n',1)[1]
text=text.replace('\\corres{Correspondence: [e-mail address]}','\\corres{Correspondence: Hongbai Zhu; contact details supplied through the submission system.}')
text=text.replace('\\pubvolume{1}','\\pubvolume{0}').replace('\\issuenum{1}','\\issuenum{0}')
text=text.replace('\\hreflink{https://doi.org/}', '')
text=re.sub(r'\\TitleCitation\{[^}]*\}', '', text)
text=re.sub(r'\\AuthorCitation\{[^}]*\}', '', text)
text=text.replace('\\usepackage{bm}','\\usepackage{bm}\n\\usepackage{amsthm}')
text=text.replace('\\usepackage{bm}', r'''\usepackage{bm}
% The official EPS logo is supplied also as a vector PDF for XeTeX/Tectonic.
\let\originalincludegraphics\includegraphics
\renewcommand{\includegraphics}[2][]{\IfStrEq{#2}{Definitions/logo-mdpi.eps}{\originalincludegraphics[#1]{Definitions/logo-mdpi.pdf}}{\originalincludegraphics[#1]{#2}}}
''')
text=text.replace('If, in addition, the lift of the unseen target work satisfies','For $s_{ab}>0$, if the lift of the unseen target work satisfies')
old='Thus $G^\\star$ is a distributionally robust~\\cite{bental2009} edge: it assumes the least favourable plausible lift for the new book. Under the random-effects reading it is a lower predictive quantile; the grid $\\gamma\\in\\{0,0.25,0.5,1\\}$ corresponds to quantile levels $0.50$, $0.60$, $0.69$ and $0.84$.'
new='Thus $G^\\star$ is an interval-robust edge~\\cite{bental2009}: it uses the least favourable lift in the specified interval. Under the normal random-effects assumption, the grid $\\gamma\\in\\{0,0.25,0.5,1\\}$ gives lower predictive quantiles at approximately $0.50$, $0.40$, $0.31$ and $0.16$, respectively. If $s_{ab}=0$, the interval reduces to a single point and the displayed probability is one.'
assert old in text;text=text.replace(old,new)
text=text.replace('Under the null hypothesis that each $\\Delta_{md}$ is symmetrically distributed about zero, the exact two-sided sign-flip (randomisation) test', 'Under joint invariance of the work-level difference vector to independent sign changes, the two-sided sign-flip (randomisation) test')
text=text.replace('If $D\' of the $D$ differences','If $D\' of the $D$ differences') if False else text
text=text.replace("If $D'$ of the $D$ differences are non-zero, then", "If $D'\\ge1$ of the $D$ differences are non-zero, then")
text=text.replace('With $D=6$ and one tie,', "If all differences are zero, $p_{\\mathrm{flip}}=1$. With $D=6$ and one tie,")
text=text.replace('Few clusters limit what any test can show', 'Few clusters limit the resolution of this test')
text=text.replace('A test at the 5\\% level was therefore impossible for the pre-specified primary comparison once one work tied, and we do not replace it by a one-sided or formula-level test after the fact. Instead we report, in addition to $p_{\\mathrm{flip}}$,', 'For this comparison, the attainable two-sided sign-flip resolution is 0.0625. Alongside $p_{\\mathrm{flip}}$, we report')
text=text.replace('which is valid under symmetry of the differences about $\\theta$, together with', 'under the same joint sign-invariance assumption about $\\theta$, together with')
text=text.replace('The comparison of SSCL with frequency on hidden F1 in the primary protocol was designated as primary.', 'SSCL versus frequency on hidden F1 is the principal comparison in the reported benchmark.')
text=text.replace('which is valid under', 'which is valid under')
needle='\\subsection{Probability Calibration}'
text=text.replace(needle,(HERE/'mathematical_extension.tex').read_text()+'\n\n'+needle)
text=text.replace('five development works)', 'five development works: Chen, 38 formulas; Huizhai, 10; Liexiang, 6; Xiaolu, 2; and unresolved Xiangcheng, 29)')
text=text.replace('graph $0.366\\to0.348$, decoder $0.367\\to0.349$', 'graph $0.3654\\to0.3482$, decoder $0.3665\\to0.3494$')
text=text.replace('(1,0.3655) (2,0.3665)', '(1,0.3654197598) (2,0.3664678699)')
text=text.replace('(1,0.3482) (2,0.3494)', '(1,0.3481871861) (2,0.3493799086)')
text=text.replace('Two books held out', 'Two books held out')
data=json.loads((R/'experiments/v5_upgrade.json').read_text())
rows=[]
for key,label in [('directed','Directed graph'),('sscl_v4','SSCL'),('posterior','Posterior-moment extension'),('operational','SSCL, unknown fraction and mass')]:
    m=data['models'][key]['source_macro_metrics'];rows.append(label+' & '+' & '.join(f'{m[k]:.4f}' for k in ('hidden_f1','weighted_jaccard','count_absolute_error','hidden_shape_tv','hidden_mass_absolute_error'))+r' \\')
result=r'''
\subsection{Posterior Moments and Operational Reconstruction}
\label{sec:operational-results}

Table~\ref{tab:v5} separates the posterior-moment extension from the operational decoder. The former reaches hidden F1 0.4266, compared with 0.4263 for SSCL and 0.4260 for the directed graph. Inner validation selects direct-graph fallback in four outer folds and posterior-moment pooling in two. The similar aggregate performance shows that exact posterior moments sharpen the model's interpretation without establishing a substantial accuracy gain on this corpus. We retain SSCL for deployment and release the posterior extension as a tested alternative.

With both the observation fraction and visible mass withheld, deployed SSCL reaches hidden F1 0.3943 and weighted Jaccard 0.3845. Its missing-mass error is 0.2560 and its hidden-shape total variation is 0.7209. These two measures identify different challenges: total-mass estimation loses information supplied by the benchmark, while rare missing materials remain difficult to identify. The interface consequently allows a researcher to supply a documented ingredient count or visible mass when either is available, and preserves the supplied within-fragment ratios exactly.

\begin{table}[H]
\caption{V5 extensions on the same six outer work folds (90 formulas, five masks each). Lower is better for count MAE, hidden-shape TV and missing-mass error. The first three rows receive the benchmark observation fraction and visible absolute mass; the operational row receives neither.}
\label{tab:v5}
\begin{adjustwidth}{-\extralength}{0cm}
\small\begin{tabularx}{\fulllength}{Lrrrrr}
\toprule
Model & Hidden F1 & W. Jaccard & Count MAE & $\operatorname{TV}_H$ & $E_M$\\
\midrule
'''+ '\n'.join(rows)+r'''
\bottomrule
\end{tabularx}\end{adjustwidth}
\end{table}

The released web implementation uses a frozen graph fitted to the 91 reviewed records, with parameters selected by leave-one-work-out validation over these training records. Its predictions retain model version, observed materials, supplied constraints and supporting formula references. Saved records remain separate from the benchmark and are never incorporated into training automatically. This keeps new scholarly corrections traceable while the released evaluation remains reproducible.
'''
text=text.replace('\\section{Discussion}',result+'\n\\section{Discussion}')
text=text.replace('\\dataavailability{The curated formula records, source locators, material ontology, deterministic split and mask definitions, experiment configurations, model code, tests and the source data for all figures and tables are available at [repository DOI to be inserted]. Records retain the source attribution and rights statement of each transcription.}', '\\dataavailability{The accompanying reproducibility archive contains curated formula records, source locators, deterministic splits and masks, model implementations, evaluation outputs and figure source data. Records retain the source attribution and rights statement of each transcription. The operational interface is available at \\url{https://incense-trace-lab.joe-zhuhb.chatgpt.site/}.}')
start=text.index('\\acknowledgments{');end=text.index('\n',start)
text=text[:start]+r'\acknowledgments{Generative AI tools, including OpenAI GPT-5.6 Sol and GPT-6 Astra and Anthropic Claude, assisted with historical-source retrieval, manuscript organisation and editing, mathematical development and checks, software implementation, figure preparation, repository organisation and typesetting. Human authorship and responsibility for the research remain with Hongbai Zhu.}' +text[end:]
text=re.sub(r'% TODO\(author\):[^\n]*\n','',text)
# Verify original files were only read; expose a deterministic input hash.
text=reconcile(text,R)
text=text.replace('no test can reach $p<0.0625$', 'this two-sided sign-flip test cannot reach $p<0.0625$')
text=text.replace(r'$\Delta_{md}$; $D$ & work-level difference from frequency; number of works \\',r'''$\Delta_{md}$; $D$ & work-level difference from frequency; number of works \\
$A_{abd},B_{abd}$; $\psi,\psi_1$ & beta shape parameters; digamma and trigamma functions \\
$m_{abd},V_{abd}$; $q_d$ & posterior lift mean and variance; normalised source weight \\
$\widehat\tau_{ab}^2,U_{ab}^2$ & estimated source variance; predictive-scale variance \\
$\rho$; $a_0,b_0$ & retention probability; beta retention-prior parameters \\
$M,u_a,r_j$ & visible mass; observed relative share; reference composition weight \\
$\operatorname{TV}_H,E_M$ & hidden-shape total variation; missing-mass absolute error \\''')
(HERE/'xiangji_v5.tex').write_text(text)
(HERE/'build_manifest.json').write_text(json.dumps({'v4_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'template':'MDPI ACS, class v6.5a 2026-09-11','experiment':'experiments/v5_upgrade.json','tex_sha256':hashlib.sha256(text.encode()).hexdigest()},indent=2))
print(HERE/'xiangji_v5.tex')
