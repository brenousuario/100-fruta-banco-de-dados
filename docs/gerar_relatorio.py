"""Regera PDF, Markdown e diagramas a partir dos SQLs e dos resultados CSV.
Dependencias adicionais: reportlab. Execute: python docs/gerar_relatorio.py
"""
from pathlib import Path
import re, csv, textwrap
from decimal import Decimal
from xml.sax.saxutils import escape
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
 Spacer, PageBreak, Table, TableStyle, Image, Preformatted, KeepTogether)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs'
INK='#263e30';GREEN='#436c44';ORANGE='#d99436';PALE='#f3f5ed'
plt.rcParams['font.family']='DejaVu Sans'

def diagram(filename, nodes, edges, title, figsize=(12,8)):
 fig,ax=plt.subplots(figsize=figsize);fig.patch.set_facecolor('white')
 ax.set_xlim(-1.7,7.7);ax.set_ylim(-2.15,4.25);ax.axis('off')
 w,h=2.5,1.18
 for a,b,label,offset in edges:
  x,y=nodes[a][0];xx,yy=nodes[b][0];dx,dy=xx-x,yy-y
  f=min(w/2/abs(dx) if dx else 999,h/2/abs(dy) if dy else 999)
  sx,sy=x+f*dx,y+f*dy;ex,ey=xx-f*dx,yy-f*dy
  ax.annotate('',xy=(ex,ey),xytext=(sx,sy),arrowprops=dict(arrowstyle='-|>',color='#839588',lw=1.5),zorder=1)
  ax.text((sx+ex)/2+offset[0],(sy+ey)/2+offset[1],label,fontsize=11.5,ha='center',va='center',color=INK,bbox=dict(facecolor='white',edgecolor='none',pad=2),zorder=4)
 for key,(pos,head,body) in nodes.items():
  x,y=pos
  ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=0.02,rounding_size=0.08',facecolor=PALE,edgecolor=GREEN,lw=1.2,zorder=2))
  ax.text(x,y+.28,head,ha='center',va='center',fontsize=13,fontweight='bold',color=INK,zorder=3)
  ax.text(x,y-.16,body,ha='center',va='center',fontsize=11,color=INK,linespacing=1.35,zorder=3)
 ax.set_title(title,loc='left',fontsize=16,fontweight='bold',color=INK,pad=16)
 fig.text(.05,.025,'Relações lidas da entidade de origem para o destino: 1 → 0..N. Cada filho tem exatamente um pai em cada vínculo.',fontsize=9,color=INK)
 fig.savefig(DOC/(filename+'.png'),dpi=180,bbox_inches='tight');fig.savefig(DOC/(filename+'.svg'),bbox_inches='tight');plt.close(fig)

nodes1={
 'f':((0,3.3),'FORNECEDOR','código • nome\ncidade • contato'),
 'g':((3,3.3),'INGREDIENTE','código • nome\nunidade'),
 'p':((6,3.3),'PRODUTO','código • nome • sabor\nadoçante • vegano\npeso • preço'),
 'li':((0,.9),'LOTE DE INSUMO','código • datas\nquantidade • custo'),
 'r':((3,.9),'FORMULAÇÃO','código\nkg por 100 unidades'),
 'lp':((6,.9),'LOTE DE PRODUÇÃO','código • datas\nunidades produzidas'),
 'c':((3,-1.5),'CONSUMO DE INSUMO','código\nquantidade consumida')}
edges1=[('f','li','fornece\n1 → 0..N',(-.6,0)),('g','li','origina lotes\n1 → 0..N',(-.15,0)),('g','r','compõe\n1 → 0..N',(0,0)),('p','r','define\n1 → 0..N',(.2,0)),('p','lp','possui\n1 → 0..N',(.65,0)),('li','c','é consumido\n1 → 0..N',(-.2,0)),('lp','c','registra\n1 → 0..N',(.2,0))]
diagram('modelo_conceitual_producao',nodes1,edges1,'Modelo conceitual · suprimentos e produção')
nodes2={
 'c':((0,3.3),'CLIENTE','código • nome\ne-mail • cidade • telefone'),
 'v':((6,3.3),'CANAL DE VENDA','código • nome'),
 'p':((3,1.1),'PEDIDO','código • data • status'),
 'pa':((0,-1.3),'PAGAMENTO','código • data\nvalor • meio'),
 'i':((3,-1.3),'ITEM DO PEDIDO','código • quantidade\npreço praticado'),
 'lp':((6,-1.3),'LOTE DE PRODUÇÃO','mesma entidade do\ndiagrama de produção')}
edges2=[('c','p','realiza\n1 → 0..N',(0,0)),('v','p','recebe\n1 → 0..N',(0,0)),('p','pa','recebe\n1 → 0..N',(-.3,0)),('p','i','contém\n1 → 0..N',(0,0)),('lp','i','atende\n1 → 0..N',(0,1.0))]
diagram('modelo_conceitual_vendas',nodes2,edges2,'Modelo conceitual · vendas e recebimentos')
nodes3={'c':((0,2),'CLIENTE','mesma entidade do\ndiagrama de vendas'),'w':((6,2),'WORKSHOP','código • título • início\nvagas • preço • URL'),'i':((3,-.3),'INSCRIÇÃO','código • data')}
diagram('modelo_conceitual_workshops',nodes3,[('c','i','efetua\n1 → 0..N',(0,0)),('w','i','recebe\n1 → 0..N',(0,0))],'Modelo conceitual · workshops',figsize=(12,6))

schema=(ROOT/'sql/01_schema.sql').read_text()
blocks=re.findall(r'CREATE TABLE (\w+) \(\n(.*?)\n\);',schema,re.S)
attrs={};fks=[];mmd=['erDiagram']
for table,block in blocks:
 lines=[];mmd.append('    '+table+' {')
 for line in block.splitlines():
  line=line.strip().rstrip(',')
  match=re.match(r'(\w+)\s+(integer|varchar\([^)]*\)|numeric\([^)]*\)|date|timestamp|boolean)',line)
  if match:
   col,typ=match.groups();fk=re.search(r'REFERENCES (\w+)\(id\)',line)
   role='PK' if col=='id' else 'FK' if fk else ''
   lines.append((col,typ,role,'sim' if 'NOT NULL' not in line and col!='id' else 'não'))
   mmd.append(f'        {typ.split("(")[0]} {col} {role}'.rstrip())
   if fk:fks.append((fk.group(1),table,col))
 mmd.append('    }');attrs[table]=lines
for parent,child,col in fks:mmd.append(f'    {parent} ||--o{{ {child} : "{col}"')
(DOC/'modelo_logico.mmd').write_text('\n'.join(mmd)+'\n')

for name,path in [('Text','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),('TextBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),('Mono','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')]:
 if Path(path).exists():pdfmetrics.registerFont(TTFont(name,path))
 else:
  from reportlab.pdfbase.pdfmetrics import Font
  pdfmetrics.registerFont(Font(name,{'Text':'Helvetica','TextBold':'Helvetica-Bold','Mono':'Courier'}[name],'WinAnsiEncoding'))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyCustom',fontName='Text',fontSize=9.4,leading=14.4,spaceAfter=8,textColor=colors.HexColor(INK)))
styles.add(ParagraphStyle(name='H1Custom',fontName='TextBold',fontSize=21,leading=26,spaceAfter=18,textColor=colors.HexColor(INK)))
styles.add(ParagraphStyle(name='H2Custom',fontName='TextBold',fontSize=12,leading=17,spaceBefore=10,spaceAfter=8,textColor=colors.HexColor(GREEN)))
styles.add(ParagraphStyle(name='SmallCustom',fontName='Text',fontSize=8,leading=11,spaceAfter=6,textColor=colors.HexColor(INK)))
styles.add(ParagraphStyle(name='TableCustom',fontName='Text',fontSize=8,leading=11,textColor=colors.HexColor(INK)))
styles.add(ParagraphStyle(name='CodeCustom',fontName='Mono',fontSize=6.7,leading=9,spaceAfter=5,textColor=colors.HexColor(INK)))
styles.add(ParagraphStyle(name='TitleCustom',fontName='TextBold',fontSize=44,leading=48,textColor=colors.HexColor(INK)))
styles.add(ParagraphStyle(name='SubtitleCustom',fontName='Text',fontSize=21,leading=29,textColor=colors.HexColor(GREEN)))
W,H=A4;LEFT=47;RIGHT=47;CW=W-LEFT-RIGHT
story=[];md=[]
class Report(BaseDocTemplate):
 def afterFlowable(self,flowable):
  if isinstance(flowable,Paragraph) and flowable.style.name=='H1Custom' and flowable.getPlainText()!='Sumário':
   text=flowable.getPlainText();key='h'+str(self.page)
   self.canv.bookmarkPage(key);self.canv.addOutlineEntry(text,key,0)
   self.notify('TOCEntry',(0,text,self.page,key))
def footer(c,doc):
 c.saveState()
 if doc.page>1:
  c.setStrokeColor(colors.HexColor('#d7decf'));c.line(LEFT,H-35,W-RIGHT,H-35)
  c.setFont('Text',7.5);c.setFillColor(colors.HexColor(GREEN))
  c.drawString(LEFT,H-26,'100% FRUTA  /  PROJETO DE BANCO DE DADOS')
  c.drawString(LEFT,27,'DEC7588 · UFSC · 2026.2')
  c.drawRightString(W-RIGHT,27,str(doc.page))
 c.restoreState()
doc=Report(str(ROOT/'Relatorio_100_Fruta.pdf'),pagesize=A4,leftMargin=LEFT,rightMargin=RIGHT,topMargin=55,bottomMargin=47,title='100% Fruta - Projeto de Banco de Dados',author='Breno Felisbino dos Anjos; Davi Ferreira da Silveira')
doc.addPageTemplates(PageTemplate(id='main',frames=Frame(LEFT,47,CW,H-102,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),onPage=footer))
def p(text,small=False):
 story.append(Paragraph(escape(text),styles['SmallCustom' if small else 'BodyCustom']));md.append(text+'\n')
def h1(text):story.append(Paragraph(escape(text),styles['H1Custom']));md.append('# '+text+'\n')
def h2(text):story.append(Paragraph(escape(text),styles['H2Custom']));md.append('## '+text+'\n')
def page():story.append(PageBreak())
def pic(path,width=CW):
 from PIL import Image as PIL
 im=PIL.open(path);height=width*im.height/im.width
 story.append(Image(str(path),width=width,height=height));md.append(f'![{path.stem}]({path.name if path.parent==DOC else "../resultados/"+path.name})\n')
def table(headers,rows,widths=None):
 data=[[Paragraph(escape(str(v)),styles['TableCustom']) for v in row] for row in [headers]+rows]
 t=Table(data,colWidths=widths or [CW/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dce7d7')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f8f3')]),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor(GREEN))]))
 story.append(t);story.append(Spacer(1,8))
 md.append('| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)+'\n')
def code(text):
 # Blocos curtos permitem quebra de pagina sem cortar linhas nem reduzir demais a fonte.
 wrapped=[]
 for line in text.splitlines():wrapped.extend(textwrap.wrap(line,width=111,replace_whitespace=False,drop_whitespace=False) or [''])
 for n in range(0,len(wrapped),30):story.append(Preformatted('\n'.join(wrapped[n:n+30]),styles['CodeCustom']))
 md.append('```sql\n'+text+'\n```\n')
def brmoney(v):return 'R$ '+f'{Decimal(v):,.2f}'.replace(',','X').replace('.',',').replace('X','.')

story.append(Spacer(1,66));p('UNIVERSIDADE FEDERAL DE SANTA CATARINA\nCampus Araranguá',True)
story.append(Spacer(1,52));story.append(Paragraph('100% Fruta',styles['TitleCustom']))
story.append(Spacer(1,18));story.append(Paragraph('Gestão da produção\nartesanal e vendas'.replace('\n','<br/>'),styles['SubtitleCustom']))
story.append(Spacer(1,24));p('Projeto de banco de dados relacional e aplicação de apoio à gestão')
story.append(Spacer(1,65))
p('Integrantes: Breno Felisbino dos Anjos e Davi Ferreira da Silveira')
p('Disciplina: Banco de Dados - DEC7588 - 2026.2')
p('Professor: Alexandre Leopoldo Gonçalves')
p('Araranguá, 21 de setembro de 2026')
story.append(Spacer(1,34));p('Proposta acadêmica baseada no dossiê fornecido. Registros, preços, formulações e validades de demonstração são fictícios. A autoria deve ser conferida antes da entrega; adicionar segundo integrante se houver.',True)
page()
story.append(Paragraph('Sumário',styles['H1Custom']))
toc=TableOfContents();toc.levelStyles=[ParagraphStyle(name='Toc',fontName='Text',fontSize=10,leading=16,leftIndent=0,firstLineIndent=0,spaceBefore=10,textColor=colors.HexColor(INK))];story.append(toc)
story.append(Spacer(1,30));p('Organização: as seções 1 a 6 atendem aos seis itens do relatório exigido. Os apêndices descrevem a aplicação, a validação e as fontes. O código-fonte completo acompanha este documento no pacote compactado.',True)
p('Base de escopo: DEC7588-Trabalho-Final.pdf e Dossiê 100% Fruta.PDF, ambos fornecidos pelo solicitante. O dossiê descreve uma plataforma proposta; este projeto não presume que ela já exista na empresa.',True)
page();h1('1. Objetivo geral do sistema')
p('Desenvolver um sistema de banco de dados relacional para apoiar a gestão da 100% Fruta, microempresa de Araranguá dedicada à fabricação artesanal de balas de frutas e à oferta de workshops sobre alimentação. O sistema integrará os cadastros de fornecedores, ingredientes, produtos e clientes aos registros de recebimento de insumos, formulações, produção por lote, consumo de matérias-primas, pedidos, pagamentos e inscrições. A solução permitirá rastrear a origem dos insumos utilizados nos lotes vendidos, consultar validades e disponibilidades e apoiar a seleção dos lotes pela ordem de entrada, reduzindo a dispersão de informações operacionais. Além disso, oferecerá consultas agregadas com visualização gráfica das vendas e dos custos de insumos, bem como uma integração com um modelo de linguagem para auxiliar a interpretação desses resultados, mantendo as decisões e a conferência dos dados sob responsabilidade do usuário.')
h2('Delimitação da proposta')
p('O projeto é um protótipo acadêmico administrativo com interface de terminal, PostgreSQL e Python. O tema foi adaptado ao dossiê da empresa. Não é um e-commerce público nem um sistema já homologado para operação comercial. O escopo privilegia os conceitos de modelagem, integridade relacional, manipulação de dados, agregação e integração com IA exigidos pela disciplina.')
h2('Entregas que acompanham o relatório')
table(['Artefato','Conteúdo'],[['Aplicação','Menu, CRUD em 14 tabelas, relatórios, consulta PEPS, criação/carga/remoção e integração Ollama.'],['Banco de dados','DDL completo, dados sintéticos, índices, views e gatilhos de validação.'],['Resultados','Três consultas com amostras, gráficos, CSV e páginas HTML independentes.'],['Apoio à apresentação','Instruções de instalação, testes, roteiro, checklist e indicação de temática.']],[105,CW-105])
page();h1('2. Descrição detalhada e requisitos')
h2('2.1 Contexto, atores e informações de origem')
p('O dossiê caracteriza a 100% Fruta como uma microempresa de Araranguá, Santa Catarina, especializada em balas artesanais de frutas. O portfólio citado inclui morango, manga, maracujá, uva, abacaxi e frutas vermelhas, com mel, açúcar demerara ou xilitol como alternativas de adoçante. Também são mencionadas opções veganas, pectina e workshops online. Esses elementos orientam os cadastros propostos, sem converter as afirmações comerciais do material em comprovação nutricional ou sanitária.')
p('A operação descrita enfrenta perecibilidade e dependência de fornecedores sazonais. O dossiê propõe controle por PEPS, rastreabilidade de lotes e validades, vendas em e-commerce, delivery regional e feiras. A aplicação oferece uma visão administrativa desses processos. O ator principal é o responsável pela gestão; produção e vendas utilizam o mesmo menu no protótipo. Não há autenticação ou separação de permissões nesta versão.')
h2('2.2 Suprimentos e produção')
p('RF01 - Cadastrar fornecedores com nome, cidade e contato, e ingredientes identificados de forma única. A unidade de medida de insumos é quilograma, evitando conversões implícitas. Cada recebimento forma um lote de insumo vinculado a exatamente um fornecedor e a um ingrediente, com código único, data de recebimento, validade, quantidade e custo unitário. Um fornecedor e um ingrediente podem existir antes de qualquer recebimento.')
p('RF02 - Cadastrar produtos com sabor, adoçante, indicação vegana, peso da embalagem e preço de referência. A formulação associa ingredientes ao produto e registra a quantidade de referência por 100 unidades. A fórmula não substitui o apontamento real: cada lote de produção identifica o produto, código, data, validade e quantidade de embalagens produzidas, e os consumos relacionam os lotes de insumos efetivamente utilizados àquele lote produzido.')
p('RF03 - Calcular o saldo de cada lote de insumo como quantidade recebida menos consumos. Calcular o saldo disponível do produto como quantidade produzida menos unidades alocadas aos pedidos. Pedidos não enviados também comprometem esse saldo; por isso ele não equivale ao estoque físico em prateleira. O programa lista lotes positivos e válidos na data informada, ordenados por entrada ou produção, com desempate pelo ID. O operador escolhe o lote e registra o consumo ou item; a divisão entre lotes é explícita.')
h2('2.3 Comercial e educação')
p('RF04 - Manter clientes e canais de venda separados dos pedidos. Cada pedido pertence a um cliente e canal, informa data e status e pode receber vários itens. Cada item referencia um lote de produção e guarda quantidade e preço praticado. Dois lotes do mesmo produto podem aparecer em linhas diferentes; não se repete o mesmo lote em duas linhas do mesmo pedido. Um pedido recém-criado pode estar sem itens enquanto o cadastro é concluído.')
p('RF05 - Registrar pagamentos associados a pedidos com data, meio e valor positivo. Um pedido pode ter zero ou vários pagamentos, permitindo lançamentos parciais. Não há conciliação automática nem bloqueio por total pago; os pagamentos não integram as consultas de receita para evitar duplicação ao unir duas relações 1:N. RF06 - Cadastrar workshops com data/hora, vagas, preço e URL, e inscrições que associam um cliente a uma edição, sem duplicidade e sem ultrapassar a capacidade.')
page();h2('2.4 Operações, análises e IA')
p('RF07 - Disponibilizar inserção, consulta, atualização e exclusão em todas as 14 tabelas. A listagem é paginada; a consulta individual usa o ID. O programa mostra referências possíveis, valida campos obrigatórios e preserva chaves primárias. Erros de unicidade, chave estrangeira, tipo ou regra de negócio são informados sem confirmar alterações inválidas. Cadastros dependentes devem ser excluídos antes dos pais, pois as FKs usam restrição de exclusão.')
p('RF08 - Oferecer três consultas parametrizadas por intervalo de datas: receita mensal por canal, unidades e receita por produto e consumo/custo de insumos por fornecedor. Cada consulta utiliza ao menos três tabelas, GROUP BY e funções de agregação. O programa imprime os resultados e gera uma tabela e um gráfico no mesmo HTML, além de CSV e PNG. O início é inclusivo e o fim exclusivo, facilitando cortes mensais sem depender do último dia do mês.')
p('RF09 - Criar a estrutura e carregar dados predefinidos por uma única opção. As etapas são transacionais e uma base já preparada é recusada, evitando duplicação. Uma opção independente remove o schema exclusivo fruta, incluindo tabelas, views e funções, depois de confirmação literal. O banco de dados PostgreSQL deve existir antes da conexão da aplicação.')
p('RF10 - Encaminhar resultados agregados das três consultas a um LLM local por meio da API do Ollama. O assistente deve produzir uma análise em português, ações possíveis e limitações, sem receber dados individuais de clientes ou executar comandos. Os valores enviados e a resposta são gravados para conferência. A indisponibilidade do serviço gera uma mensagem de erro, sem inventar uma análise.')
h2('2.5 Regras de integridade e requisitos não funcionais')
p('RN01 - Quantidades e preços de venda devem ser positivos; custos e preços de workshops podem ser zero. RN02 - A validade não antecede o recebimento ou a produção. RN03 - O consumo é permitido somente quando o insumo está disponível e válido na data de produção; a venda exige lote produzido e válido na data do pedido. Gatilhos impedem exceder o saldo e recusam alterações retroativas de datas e quantidades que invalidariam operações já registradas.')
p('RN04 - Cada inscrição é única por cliente/workshop e não pode ocorrer após a data do evento. A capacidade não pode ser reduzida abaixo das inscrições existentes. RN05 - O marcador vegano não pode coexistir com adoçante mel. Essa regra não verifica outros ingredientes e não equivale a certificação. RN06 - Os códigos de lotes, nomes de ingredientes, produtos, fornecedores e canais e e-mails de clientes são únicos, conforme as hipóteses simplificadoras deste projeto.')
p('RNF01 - Utilizar PostgreSQL 16+ e Python 3.10+, com valores monetários NUMERIC no banco. RNF02 - Usar parâmetros SQL e identificadores controlados, sem concatenar texto informado pelo usuário a comandos. RNF03 - Organizar código, SQL e documentação para reprodução local. RNF04 - Gerar relatórios visualizáveis sem servidor web. A solução é destinada à demonstração monousuário; não foi dimensionada nem testada para carga produtiva.')
h2('2.6 Hipóteses e exclusões')
p('O dossiê não fornece cadastros, formulações quantitativas, preços, custos, prazos de validade ou transações. Esses dados são exclusivamente didáticos, inclusive os meses futuros simulados. Não se implementam perdas, devoluções, auditoria, versionamento de receitas, FEFO, gateway, logística, campanhas, notas fiscais ou pagamentos de workshops. Consumos podem divergir da formulação de referência; o sistema registra a diferença, mas não certifica rendimento, composição ou segurança alimentar. A estatística de mercado mencionada no dossiê não é utilizada como evidência quantitativa neste projeto.')
page();h1('3. Modelagem conceitual')
p('O modelo possui 14 entidades: dez entidades de cadastro ou evento e quatro entidades associativas (Formulação, Consumo de insumo, Item do pedido e Inscrição). Os diagramas apresentam o mesmo modelo em três recortes para preservar legibilidade. Cliente e Lote de produção aparecem repetidos apenas como pontos de conexão, sem representar entidades adicionais.')
p('Cada ligação marcada 1 → 0..N indica que uma ocorrência da entidade de origem pode ter zero ou muitas ocorrências no destino, e cada ocorrência do destino se vincula a exatamente uma origem. A participação mínima zero permite cadastrar pais antes dos filhos. Formulação, Consumo, Item e Inscrição resolvem associações N:N com atributos próprios.',True)
pic(DOC/'modelo_conceitual_producao.png')
h2('Rastreabilidade')
p('A partir de um item vendido, identifica-se o lote de produção; por seus consumos, chega-se aos lotes de insumos, ingredientes e fornecedores. Uma formulação descreve a referência para um produto, enquanto o consumo guarda a origem efetiva dos insumos usados em um lote específico. Não se confunde uma receita prevista com evidência de produção.')
page();h2('3.1 Comercial e recebimentos')
pic(DOC/'modelo_conceitual_vendas.png',CW*.96)
p('Um pedido pode receber vários pagamentos sem multiplicar seus itens. A opção por status confirmado, enviado e entregue delimita que todos os pedidos existentes são compromissos comerciais; não se modelam carrinhos ou cancelamentos por status.',True)
h2('3.2 Educação e relacionamento')
pic(DOC/'modelo_conceitual_workshops.png',CW*.8)
p('Cliente e Workshop se relacionam por Inscrição. A entidade associativa registra a data e permite impor unicidade e limite de vagas. A inscrição não gera automaticamente um pedido de produtos.',True)
page();h2('3.3 Entidades e significado dos atributos')
meanings={
'cliente':'Pessoa cadastrada para compras ou workshops; e-mail identifica o cadastro nesta proposta.',
'fornecedor':'Origem comercial dos lotes de matérias-primas, com contato e cidade.',
'ingrediente':'Insumo em unidade kg, independente do fornecedor e do lote recebido.',
'lote_insumo':'Recebimento rastreável com quantidade, custo, datas e código próprios.',
'produto':'Embalagem comercial de bala artesanal, sabor, adoçante, peso, preço de referência e marcador vegano.',
'formulacao':'Quantidade de cada ingrediente prevista para 100 embalagens do produto.',
'lote_producao':'Evento de produção de um produto, com quantidade e validade próprias.',
'consumo_insumo':'Quantidade efetivamente retirada de um lote de insumo para um lote produzido.',
'canal_venda':'Meio comercial de origem do pedido: e-commerce, delivery ou feira, entre outros.',
'pedido':'Compromisso comercial de um cliente em um canal e uma data, com status.',
'item_pedido':'Quantidade alocada de um lote produzido a um pedido, com preço unitário praticado.',
'pagamento':'Lançamento de recebimento relacionado a um pedido, com valor, data e meio.',
'workshop':'Edição de um evento educacional online, com capacidade, preço e endereço de acesso.',
'inscricao':'Participação de um cliente em uma edição de workshop, com data de registro.'}
table(['Entidade','Significado'],[[t,meanings[t]] for t,_ in blocks],[115,CW-115])
p('Identificadores conceituais: todos os registros possuem um código interno. Código externo do lote, e-mail e nomes selecionados recebem unicidade adicional. Os atributos de ligação são materializados como chaves estrangeiras somente no modelo lógico.',True)
page();h1('4. Modelagem lógica')
h2('4.1 Transformação do conceitual para o relacional')
p('Cada entidade origina uma tabela. Cada relação 1:N é transformada em uma chave estrangeira NOT NULL na tabela do lado N. As quatro entidades associativas recebem ID próprio e uma restrição UNIQUE no par de referências. Essa escolha preserva a unicidade de negócio e uniformiza o CRUD por ID. As chaves primárias são inteiros gerados por identidade; exclusões são restritas para proteger dependências.')
p('A notação a seguir define as relações derivadas do modelo conceitual. PK identifica a chave primária; os campos com sufixo _id são FKs e têm seus destinos explicitados na tabela seguinte. Tipos, comprimentos, domínios, nulabilidade e restrições completas constam no DDL da seção 5.')
table(['Relação','Atributos e chaves'],[[t,', '.join(f[0]+(' [PK]' if f[2]=='PK' else ' [FK]' if f[2]=='FK' else '') for f in fields)] for t,fields in attrs.items()],[105,CW-105])
page();h2('4.2 Mapeamento das chaves estrangeiras')
table(['Tabela de origem','Chave estrangeira','Referência'],[[ch,col,pa+'.id'] for pa,ch,col in fks],[134,148,CW-282])
h2('4.3 Chaves alternativas')
p('São únicos: cliente.email; fornecedor.nome; ingrediente.nome; produto.nome; canal_venda.nome; lote_insumo.codigo; lote_producao.codigo. As associações são únicas por (produto_id, ingrediente_id), (lote_producao_id, lote_insumo_id), (pedido_id, lote_producao_id) e (cliente_id, workshop_id), respectivamente. Insumos, produtos e clientes distintos devem receber identificadores próprios, sem listas embutidas em campos.')
page();h2('4.4 Normalização e escolhas de armazenamento')
p('Primeira forma normal: cada atributo contém um valor atômico e as repetições são representadas em tabelas associativas. Segunda forma normal: atributos de uma associação, como quantidade consumida, dependem do vínculo completo identificado pela chave alternativa, e não apenas de um dos participantes. Terceira forma normal: fornecedor, ingrediente, produto, cliente e canal são mantidos separadamente, evitando que seus dados descritivos se repitam em cada operação.')
p('O preço de referência do produto é diferente do preço praticado em um item. O segundo depende da venda e deve ser armazenado para que alterações futuras no catálogo não modifiquem o valor das vendas registradas. De modo semelhante, o custo do lote de insumo pertence ao recebimento específico. Alterações administrativas nesses próprios registros são permitidas pelo CRUD e recalculam os relatórios; não há histórico de versões ou auditoria.')
p('Receita do pedido, custo consumido e saldos não são colunas editáveis. São obtidos por agregação. As views saldo_insumo e saldo_produto sintetizam a disponibilidade por lote; a pré-agregação dos filhos evita multiplicação de linhas. As consultas gerenciais não juntam pagamentos e itens simultaneamente, pois duas relações 1:N poderiam duplicar valores e produzir somas incorretas.')
h2('4.5 Domínios, índices e limites')
table(['Grupo','Definição'],[['IDs','INTEGER por identidade, PK; FKs INTEGER.'],['Quantidades','Insumos em NUMERIC(12,3); unidades produzidas e vendidas em INTEGER.'],['Dinheiro','NUMERIC(12,2), evitando armazenamento monetário em ponto flutuante.'],['Datas','DATE nas operações por dia; TIMESTAMP local em workshop (horário assumido: Brasília).'],['Domínios','Status: confirmado/enviado/entregue. Adoçante: mel/demerara/xilitol. Pagamento: pix/cartao/dinheiro.'],['Índices','Ordem PEPS, data do pedido e referências usadas em soma de consumos, itens, pagamentos e inscrições.']],[104,CW-104])
p('A integridade estrutural utiliza PK, FK, UNIQUE, NOT NULL e CHECK. Regras que consultam outras linhas utilizam funções e gatilhos; não são expressas por CHECK com subconsultas. Os gatilhos usam bloqueios de linha para coordenar alocações no mesmo lote, mas a validação executada foi sequencial e não comprova comportamento sob carga concorrente. A fonte Mermaid do modelo lógico está em docs/modelo_logico.mmd.')
page();h1('5. Script DDL')
p('A transcrição abaixo é o script completo sql/01_schema.sql, incluindo tabelas, índices, views, funções e gatilhos. A aplicação o executa na mesma transação da carga inicial. O schema fruta deve estar ausente, e o banco PostgreSQL deve ter sido criado previamente. A documentação oficial consultada descreve as restrições utilizadas [3].',True)
code(schema)
h2('5.1 Remoção da estrutura')
p('A opção de limpeza exige confirmação e executa o arquivo sql/06_drop.sql. Seu alcance é exclusivamente o schema do projeto. A criação posterior repõe tabelas e dados predefinidos.',True)
code((ROOT/'sql/06_drop.sql').read_text())
page();h1('6. Consultas, resultados e gráficos')
p('As consultas foram executadas com a carga sintética de julho a dezembro de 2026. O intervalo utilizado é [2026-07-01, 2027-01-01). As amostras tabulares e os gráficos vêm dos mesmos resultados SQL exportados pela aplicação. A base possui 18 pedidos, 108 itens, 36 lotes produzidos e 108 consumos. Não são vendas reais nem projeções da empresa.')
query_defs=[
(1,'6.1 Vendas mensais por canal','Identificar a distribuição da receita bruta de balas entre os canais e ao longo dos meses, apoiando o acompanhamento comercial. A consulta usa pedido, canal_venda e item_pedido (três tabelas), com SUM sobre quantidade multiplicada pelo preço praticado.','03_consulta_mensal.sql'),
(2,'6.2 Unidades e receita por produto','Comparar a contribuição dos produtos para a receita e o volume de unidades. A consulta usa produto, lote_producao, item_pedido e pedido (quatro tabelas). As duas somas permitem separar volume de valor, preservando os preços registrados em cada item.','04_consulta_produto.sql'),
(3,'6.3 Consumo e custo por fornecedor','Medir quantos quilogramas foram consumidos e qual seu custo por fornecedor, considerando a data de produção. A consulta usa fornecedor, lote_insumo, consumo_insumo e lote_producao (quatro tabelas). O cálculo usa o custo unitário do lote recebido.','05_consulta_insumo.sql')]
for n,title,desc,filename in query_defs:
 if n>1:page()
 h2(title);p(desc)
 code((ROOT/'sql'/filename).read_text())
 rows=list(csv.DictReader((ROOT/f'resultados/consulta_{n}.csv').open(encoding='utf-8-sig')))
 if n==1:
  h2('Amostra do resultado: seis de 18 linhas')
  table(['Mês','Canal','Receita bruta'],[[r['mes'],r['canal'],brmoney(r['receita'])] for r in rows[:6]],[88,244,CW-332])
  p('O CSV e o HTML incluídos no pacote apresentam as 18 linhas. O total das vendas do período é R$ 10.602,00. Os valores são contabilizados pela data do pedido, independentemente da data do pagamento.',True)
 elif n==2:
  table(['Produto','Unidades','Receita bruta'],[[r['produto'],r['unidades'],brmoney(r['receita'])] for r in rows],[285,70,CW-355])
  p('São 1.188 unidades vendidas. A soma da receita por produto também resulta em R$ 10.602,00, conciliando com a primeira consulta. Todos os seis produtos com vendas aparecem nesta amostra.',True)
 else:
  table(['Fornecedor fictício','kg consumidos','Custo'],[[r['fornecedor'].replace('Fornecedor ','').replace(' (fictício)',''),r['kg_consumidos'].replace('.',','),brmoney(r['custo_insumos'])] for r in rows],[260,100,CW-360])
  p('O consumo total é de 165,600 kg e o custo dos insumos utilizados é R$ 2.499,00. A produção inclui unidades ainda não vendidas; esses custos não correspondem diretamente ao custo dos itens vendidos.',True)
 page();h2(title+' · representação gráfica')
 pic(ROOT/f'resultados/consulta_{n}.png')
 if n==1:
  p('No conjunto simulado, a receita mensal passa de R$ 957,00 em julho para R$ 2.577,00 em dezembro. A feira local soma R$ 3.858,00, o delivery R$ 3.534,00 e o e-commerce R$ 3.210,00. O gráfico é empilhado: a altura total representa o mês e cada segmento representa um canal. O padrão crescente foi construído para demonstração e não comprova sazonalidade real.')
 elif n==2:
  p('Frutas vermelhas apresenta a maior receita simulada (R$ 1.980,00), mesmo com menos unidades que manga e abacaxi. Isso ilustra a influência do preço praticado sobre a receita. A análise não determina qual produto é mais lucrativo, pois não aloca todos os custos aos itens vendidos.')
 else:
  p('Safra Local concentra R$ 1.056,00 do custo consumido, seguido de Frutas do Sul (R$ 960,00) e Ingredientes Naturais (R$ 483,00). Esses fornecedores são fictícios. Diferenças de custo podem refletir mix e quantidade; não permitem concluir que um fornecedor é mais eficiente nem medir qualidade ou risco de abastecimento.')
 h2('Execução e leitura')
 p('No menu, selecione a opção 3, escolha esta consulta e informe o período. O sistema retorna o SQL executado na forma de linhas tabulares e gera o gráfico correspondente. Meses e categorias sem operações não produzem linhas; um período totalmente vazio gera uma página e um gráfico com a indicação de ausência de dados. Arquivos CSV e HTML permitem examinar todas as linhas recuperadas.')
page();h1('Apêndice A. Aplicação e demonstração')
table(['Requisito','Implementação'],[['7.a - Conexão','Python + Psycopg com PostgreSQL; configuração DATABASE_URL e opção Docker.'],['7.b / 7.d - CRUD e menu','Opção 2: cinco ações (listar, consultar ID, inserir, atualizar, excluir) em 14 tabelas.'],['7.c - Consultas','Opção 3: três SQLs parametrizados, tabela no terminal e HTML com gráfico.'],['7.e - Criação e remoção','Opções 1 e 6: DDL + carga atômicos e eliminação do schema com confirmação.'],['7.f - IA generativa','Opção 5: resultados SQL agregados enviados à API do Ollama; resposta em português.']],[133,CW-133])
h2('Fluxo da integração com IA')
p('A aplicação executa as três consultas, serializa os resultados em JSON e monta um prompt que delimita evidências e limitações. Em seguida, envia uma requisição HTTP POST à rota /api/generate do Ollama, usando o modelo configurado e stream=false. O texto retornado é exibido e salvo junto ao contexto consultado. O modelo não recebe acesso ao banco e não executa SQL. A API é documentada pela fonte [5].')
p('O usuário precisa instalar o Ollama, iniciar o serviço e baixar o modelo qwen2.5:3b ou configurar outro compatível. Não existe resposta substituta simulada na aplicação. A integração foi testada por contrato HTTP com retorno controlado; uma inferência real ainda deve ser executada no computador da apresentação. Uma resposta de LLM exige revisão e pode conter erros mesmo com um prompt restritivo.')
h2('Instalação e execução')
p('As instruções completas para Windows, Linux/macOS, PostgreSQL local ou Docker estão em README.md. O fluxo básico é instalar requirements.txt, iniciar o banco, executar python app.py init e abrir python app.py. Para gerar todos os relatórios sem interação, use python app.py reports. O roteiro de apresentação de aproximadamente 18 minutos acompanha o pacote.')
page();h1('Apêndice B. Validação e limites')
p('Foram aprovados 16 testes automatizados, incluindo CRUD completo nas 14 tabelas, integridade referencial, unicidade, saldo, validade, inscrições, intervalo de consulta, inicialização repetida e remoção/recriação. As três agregações foram comparadas com cálculos independentes sobre a base de referência. O registro da execução está em docs/testes_execucao.txt e a suíte em tests/test_app.py.')
p('A validação executou os comandos pelo driver da aplicação sobre o motor PostgreSQL do PGlite com interface TCP, utilizando Python 3.12 e Psycopg 3.3.6. Esse ambiente permite conferir SQL real e operações do programa, mas não substitui a homologação da instalação nativa PostgreSQL 16 ou da imagem Docker, que não foram executadas aqui. Também não houve teste de múltiplos usuários, carga elevada ou geração por um LLM real.')
p('Não houve validação dos dados pela empresa. A base é fictícia e inclui meses futuros simulados. Formulações quantitativas e validades são apenas dados de demonstração, sem uso prescritivo na fabricação. A aplicação não implementa todas as integrações propostas pelo dossiê nem constitui uma solução pronta para produção. Esses limites preservam a distinção entre contexto empresarial, hipóteses acadêmicas e evidências de teste.')
h2('Conferência antes de enviar')
p('Conferir o nome do integrante, acrescentar eventual segundo integrante e validar a temática. Executar a aplicação no computador que será usado em aula, testar a IA real e revisar a resposta. O relatório e o código devem ser entregues em um único arquivo compactado no Moodle até 22/11/2026, conforme o enunciado. A apresentação tem avaliação individual; o roteiro é material de estudo, não substitui domínio do projeto.')
p('O enunciado contém uma divergência entre o total indicado para o item 7 e a soma de seus subitens. Foram atendidas as funcionalidades descritas, sem presumir pesos alternativos. A indicação de equipe/tema consta como 20/09/2026; como a preparação é posterior, é necessário conferir com o professor o procedimento de registro.')
page();h1('Referências e materiais de origem')
refs=[
'[1] UNIVERSIDADE FEDERAL DE SANTA CATARINA. DEC7588 - Trabalho Final. Banco de Dados, 2026.2. Professor Alexandre Leopoldo Gonçalves. Enunciado fornecido pelo solicitante, 4 páginas.',
'[2] 100% FRUTA. 100% Fruta: Visão Geral e Estratégia Corporativa. Dossiê fornecido pelo solicitante, 4 páginas, sem data de revisão preenchida. Fonte de contexto e escopo, não de dados transacionais.',
'[3] POSTGRESQL GLOBAL DEVELOPMENT GROUP. PostgreSQL Documentation: Constraints. https://www.postgresql.org/docs/current/ddl-constraints.html. Consulta em 21 set. 2026.',
'[4] PSYCOPG. Passing parameters to SQL queries. https://www.psycopg.org/psycopg3/docs/basic/params.html. Consulta em 21 set. 2026.',
'[5] OLLAMA. Generate a response. https://docs.ollama.com/api/generate. Consulta em 21 set. 2026.',
'[6] ELECTRIC SQL. PGlite Socket: documentação distribuída no pacote @electric-sql/pglite-socket, versão 0.2.11. Utilizada para configurar o ambiente de testes PostgreSQL via TCP.']
for ref in refs:p(ref)
h2('Distinção entre fonte e proposta')
p('A localização, a atividade, os sabores mencionados, os canais e a intenção de controlar PEPS e rastreabilidade vêm do dossiê [2]. O esquema relacional, as regras específicas, a interface, as consultas, os cadastros, as formulações quantitativas e os valores de demonstração foram elaborados para o projeto acadêmico. Nenhum resultado do banco deve ser atribuído ao desempenho real da empresa.')
(DOC/'relatorio_editavel.md').write_text('\n'.join(md),encoding='utf-8')
doc.multiBuild(story)
print('Relatório e diagramas gerados:',ROOT/'Relatorio_100_Fruta.pdf')
