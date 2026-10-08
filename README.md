# 100% Fruta · Gestão da produção artesanal e vendas

> Projeto acadêmico de gestão: organização de insumos, produção por lote e vendas, com análise de dados para apoiar a tomada de decisão.

**Tecnologias:** Python · PostgreSQL · SQL · Docker Compose · Ollama (integração opcional com IA)

## Visão de gestão

Este projeto conecta o estudo de banco de dados a processos de uma pequena operação de produção artesanal. O objetivo é demonstrar como registros organizados e consultas podem apoiar o acompanhamento da produção, do estoque e das vendas.

| Frente de gestão | Aplicação no projeto |
| --- | --- |
| Suprimentos e estoque | Cadastro de fornecedores e insumos, saldos por lote e seleção assistida por PEPS. |
| Produção | Registro de formulações, lotes produzidos e consumo efetivo de insumos. |
| Comercial | Organização de clientes, canais de venda, pedidos e pagamentos. |
| Análise de dados | Três consultas SQL com tabelas, gráficos e exportações em CSV e HTML. |
| Apoio à decisão | Integração opcional com IA para interpretar resultados agregados, sujeita à revisão humana. |

**Estágio:** protótipo acadêmico com dados fictícios. Os limites e as verificações pendentes estão descritos nas seções de testes e regras do protótipo.

## Navegação do projeto

- **Entender o estudo:** [relatório editável](docs/relatorio_editavel.md).
- **Executar a aplicação:** [requisitos](#requisitos) e [instalação rápida](#instalação-rápida).
- **Explorar as análises:** [resultados](resultados/) e [consultas SQL](sql/).
- **Conferir a validação:** [documentação de validação](docs/VALIDACAO.md) e [testes](tests/).
- **Preparar a apresentação:** [roteiro](docs/ROTEIRO_APRESENTACAO.md) e [checklist](docs/CHECKLIST.md).

## Contato profissional

**Breno Felisbino dos Anjos** — foco em gestão e interesse na aplicação de tecnologia a estudos, oportunidades profissionais e projetos para clientes.

[LinkedIn de Breno Felisbino dos Anjos](https://www.linkedin.com/in/breno-felisbino-021ab9266/)

---

## Contexto acadêmico


Projeto acadêmico de Banco de Dados, DEC7588, UFSC, 2026.2.
Tema baseado no arquivo “Dossiê 100% Fruta.PDF”. O escopo cobre fornecedores,
insumos, formulações, produção por lote, vendas, pagamentos e workshops.
**Todos os registros de demonstração são fictícios.** Preços, receitas produtivas,
pesos, custos, validades e datas são hipóteses didáticas, não informações operacionais
validadas pela empresa nem instruções de fabricação de alimentos.

## Equipe

- Breno Felisbino dos Anjos
- Davi Ferreira da Silveira

## Comece aqui

1. Leia `docs/relatorio_editavel.md` (itens 1 a 6 do enunciado).
2. Instale e execute a aplicação seguindo as etapas abaixo.
3. Para apresentar, use `docs/ROTEIRO_APRESENTACAO.md`.
4. Antes de enviar ao Moodle, confira autoria e a lista em `docs/CHECKLIST.md`.

## Requisitos

- Python 3.10 ou superior.
- PostgreSQL 16 ou superior, em instalação local **ou** Docker com Compose.
- Navegador para visualizar os gráficos HTML (não requer servidor web).
- Para a opção de IA: Ollama e modelo `qwen2.5:3b`. O primeiro download requer
  internet e espaço em disco; o tempo de geração depende da máquina.

## Instalação rápida

Execute os comandos na pasta do repositório baixado.

```bash
python -m venv .venv
```

Ative no Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

Ou no Linux/macOS:

```bash
source .venv/bin/activate
```

Se a ativação do PowerShell estiver bloqueada, execute os comandos Python usando
`.\.venv\Scripts\python.exe` diretamente, sem alterar políticas do computador.

```bash
python -m pip install -r requirements.txt
docker compose up -d --wait
python app.py init
python app.py
```

O arquivo `compose.yaml` cria um PostgreSQL local com volume persistente. A aplicação
usa a conexão padrão definida em `.env.example`; não é necessário criar `.env`
para o exemplo padrão. Caso personalize as configurações, copie `.env.example`
para `.env` e edite os valores. As variáveis de ambiente têm prioridade.

### Sem Docker

Crie um banco vazio no pgAdmin ou em uma sessão administrativa do PostgreSQL:

```sql
CREATE ROLE fruta LOGIN PASSWORD 'fruta_demo';
CREATE DATABASE fruta100 OWNER fruta;
```

Conecte-se a `fruta100` com esse usuário, ou use `python app.py init`. O programa
cria o **schema e as tabelas dentro do banco**, não o servidor nem o banco de dados.
O usuário precisa de permissão para criar schemas no banco de destino.
As credenciais do exemplo são apenas para demonstração local.

## Menu e cobertura

| Opção | Função |
|---|---|
| 1 | Cria 14 tabelas, índices, views e gatilhos; carrega a base fictícia em uma transação |
| 2 | Lista, consulta por ID, insere, atualiza e exclui em qualquer uma das 14 tabelas |
| 3 | Executa uma das três consultas SQL e abre tabela + gráfico no navegador |
| 4 | Lista lotes com saldo e válidos na data escolhida, em ordem PEPS |
| 5 | Consulta o LLM no Ollama com os resultados agregados do banco |
| 6 | Elimina o schema `fruta` com confirmação literal `APAGAR FRUTA` |
| 0 | Encerra |

No CRUD, o programa mostra os primeiros IDs de referência para ajudar a preencher
as FKs. Para ver todos, use a listagem paginada da tabela referenciada. Informe datas
`AAAA-MM-DD`, decimais com ponto, booleanos `true/false`. Enter mantém o valor na edição
ou utiliza o padrão na inserção. `/null` apaga um campo opcional. O ID é automático
e não é editável. A exclusão exige confirmação; FKs impedem apagar registros em uso.

Cadastre os pais antes dos filhos. Ordem sugerida: cliente, fornecedor, ingrediente,
produto, canal_venda, workshop; depois lote_insumo e formulacao; lote_producao;
consumo_insumo; pedido; item_pedido; pagamento; inscricao. Para excluir uma cadeia,
use a ordem inversa. Excluir um consumo ou item devolve o saldo derivado do lote.
Trata-se de manutenção acadêmica; o sistema não emite estornos fiscais nem mantém
auditoria de exclusões.

### Executar consultas e PEPS sem menu

```bash
python app.py reports --start 2026-07-01 --end 2027-01-01
python app.py peps --kind insumo --id 1 --date 2026-08-03
python app.py peps --kind produto --id 1 --date 2026-08-03
```

O início é inclusivo e o fim exclusivo. Cada consulta grava CSV, PNG e um HTML
independente em `resultados/`. Abra `consulta_1.html`, `consulta_2.html` ou
`consulta_3.html`. O gráfico está embutido no HTML. A tabela reproduz todas as linhas
retornadas. Meses/canais sem vendas não geram linhas; no gráfico, combinações ausentes
entre os meses presentes recebem zero. Os relatórios entregues usam julho a dezembro
**simulados** de 2026, inclusive datas futuras em relação à preparação do projeto.

Receita é o valor bruto dos itens dos pedidos cadastrados (todos os três status
representam pedidos confirmados). Não corresponde ao caixa recebido nem ao lucro.
Pagamentos são lançamentos parciais livres e não são automaticamente conciliados.
A terceira consulta mede somente o custo dos insumos consumidos, não a margem.

### SQL em um cliente externo

Os arquivos 03 a 05 contêm parâmetros nomeados do Psycopg. Para executá-los diretamente
no pgAdmin, substitua `%(inicio)s` por `DATE '2026-07-01'` e `%(fim)s` por
`DATE '2027-01-01'`. Os scripts 01 e 02 são SQL PostgreSQL comuns; rode-os, nessa
ordem, dentro de `BEGIN; ... COMMIT;` em um banco sem schema `fruta`.

## IA generativa real

Instale o Ollama conforme a documentação oficial: https://docs.ollama.com/quickstart

Em um terminal, caso o serviço não esteja ativo:

```bash
ollama serve
```

Em outro terminal:

```bash
ollama pull qwen2.5:3b
python app.py ai --question "Quais produtos e canais merecem atenção? Cite os dados e as limitações."
```

Também é possível usar a opção 5 do menu. `OLLAMA_URL` e `OLLAMA_MODEL` podem ser
alterados no `.env`. O aplicativo envia um POST a `/api/generate` com `stream:false`
e os resultados das três consultas. O contexto não contém e-mails nem nomes de
clientes. O modelo não tem acesso direto ao banco e não executa SQL ou comandos.
A saída e o contexto são salvos em `resultados/analise_ia.md` e `contexto_ia.json`.
Revise os números: instruções no prompt não eliminam possíveis erros de um LLM.

Se o modelo ou serviço estiver indisponível, a aplicação informa o erro;
**não substitui a resposta por um texto simulado**. A integração foi testada no nível
do contrato HTTP com resposta controlada, mas a inferência de um LLM real não foi
executada no ambiente de preparação. Execute esta etapa antes de apresentar o item 7.f.

## Regras e limites do protótipo

- 14 tabelas, chaves primárias artificiais, FKs restritivas, unicidade e CHECKs.
- Saldo de insumos = recebido menos consumido. Saldo disponível de produtos = produzido
  menos alocado aos pedidos, inclusive pedidos ainda não enviados. Não é contagem física.
- Gatilhos recusam consumo/venda acima do saldo, datas incompatíveis e algumas edições
  retroativas que invalidariam os registros dependentes. Datas são avaliadas na data da
  operação registrada, permitindo cadastrar operações históricas.
- PEPS ordena por recebimento/produção e desempata por ID; exclui lotes vencidos.
  A seleção é assistida e não obrigatória nem automática. Não é FEFO (validade mais próxima).
- Formulação é uma referência atual; consumo registra uso efetivo. Não há baixa automática
  pela receita nem validação de equivalência, rendimento ou substituições.
- Os campos `vegano` e `adocante` são cadastros. A regra apenas impede marcar como vegano
  um produto adoçado com mel; não certifica toda a formulação nem faz alegações de saúde.
- Workshops têm limite de vagas e uma inscrição por cliente. O pagamento de workshops
  não está no escopo; `pagamento` referencia pedidos de balas.
- Não implementa checkout público, frete, gateways, marketing, autenticação, perdas,
  devoluções, emissão fiscal, auditoria ou rastreabilidade regulatória completa.
- Bloqueios de linha apoiam a integridade das alocações; concorrência e carga elevada
  não foram testadas. A demonstração é monousuário.

## Testes

**Use um banco separado**: os testes removem e recriam o schema `fruta` no banco
apontado por `DATABASE_URL`. A variável adicional evita execução destrutiva acidental.

Linux/macOS (depois de criar um banco `fruta100_teste` vazio):

```bash
DATABASE_URL=postgresql://fruta:fruta_demo@localhost:5432/fruta100_teste FRUTA_TEST_ALLOW_RESET=1 python tests/test_app.py
```

PowerShell:

```powershell
$env:DATABASE_URL="postgresql://fruta:fruta_demo@localhost:5432/fruta100_teste"
$env:FRUTA_TEST_ALLOW_RESET="1"
python tests/test_app.py
Remove-Item Env:DATABASE_URL
Remove-Item Env:FRUTA_TEST_ALLOW_RESET
```

Foram aprovados 16 testes automatizados, incluindo um teste parametrizado de CRUD
nas 14 tabelas, comparação das três consultas com cálculos independentes e testes de
restrições. Veja `docs/VALIDACAO.md` e `docs/testes_execucao.txt`.
O ambiente disponível utilizou o motor PostgreSQL do PGlite por protocolo TCP;
a instalação nativa PostgreSQL 16/Docker e uma inferência real do Ollama ainda
precisam de verificação no computador da apresentação.

## Reinicialização e encerramento

A criação recusa uma base já preparada e não altera seus dados. Para reiniciar:

```bash
python app.py drop --confirm "APAGAR FRUTA"
python app.py init
```

Para desligar apenas o banco Docker mantendo os dados: `docker compose down`.

## Arquivos

- O PDF do relatório pode ser regenerado conforme a seção abaixo.
- `docs/relatorio_editavel.md`: conteúdo editável do relatório.
- `docs/modelo_*.png`, `.svg` e `modelo_logico.mmd`: diagramas e fonte editável.
- `app.py`, `requirements.txt`, `.env.example`, `compose.yaml`: aplicação.
- `sql/`: DDL completo, carga inicial, três consultas e remoção.
- `resultados/`: resultados SQL em tabelas CSV, gráficos PNG e páginas HTML.
- `tests/`: testes e base de referência para conferência independente.
- `docs/INDICACAO_EQUIPE.md`: texto inicial de temática e campos para conferência.
- `docs/ROTEIRO_APRESENTACAO.md`: sequência de demonstração de 15 a 20 minutos.

O enunciado solicita um único arquivo compactado contendo relatório e código.
Prazo indicado: **22/11/2026**. A indicação de equipe/tema consta como **20/09/2026**;
confira com o professor como registrar essa indicação, pois a preparação é posterior.
As apresentações previstas são 23/11, 25/11, 30/11 e 02/12, conforme distribuição no Moodle.

## Editar e regerar o relatório

O conteúdo está em `docs/relatorio_editavel.md`. Para alterar a versão PDF gerada,
edite o texto e a autoria em `docs/gerar_relatorio.py`, instale as dependências adicionais
e execute o gerador (ele sobrescreve PDF, Markdown e diagramas):

```bash
python -m pip install -r requirements-docs.txt
python docs/gerar_relatorio.py
```

Os resultados CSV/PNG devem existir em `resultados/`; para atualizá-los, execute antes
`python app.py reports`. Alterar apenas o Markdown não atualiza automaticamente o PDF.
