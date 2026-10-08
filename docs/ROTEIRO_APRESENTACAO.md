# Roteiro de apresentação · 100% Fruta

Duração sugerida: 18 minutos, seguida das perguntas previstas no enunciado.
Não foi exigido um arquivo de slides; este roteiro acompanha a demonstração do sistema.

## Antes da aula

- Confira autoria, escopo e regras de cada entidade.
- Inicie o PostgreSQL, instale as dependências e rode os testes em banco separado.
- Prepare a base de demonstração. Abra os dois diagramas conceituais e o lógico.
- Inicie o Ollama e rode uma análise real. O teste com resposta controlada não
  substitui a demonstração com LLM.
- Abra os três HTMLs de resultados para a alternativa de apresentação offline.
- Faça backup dos dados se tiver realizado alterações úteis; a reinicialização apaga dados.

## 0–2 min · Problema e objetivo

Explique que a empresa fabrica balas de frutas e oferece workshops. A perecibilidade
motiva controlar validade, lotes e origem. Identifique como hipóteses acadêmicas os
preços, quantidades e prazos. Não apresente os dados simulados como resultados da empresa.

## 2–6 min · Modelagem

Mostre as 14 entidades e as associações: formulação liga produto e ingrediente;
consumo liga lote de insumo e lote de produção; item liga pedido a lote produzido;
inscrição liga cliente a workshop. Explique 1:N, associações N:N resolvidas,
PK/FK, chaves alternativas, normalização e saldo derivado. Uma venda pode ser
rastreada até fornecedores passando por item, lote produzido, consumo e lote de insumo.

## 6–11 min · Banco e CRUD

1. Opção 1: criação e carga. Mostrar que repetir a criação preserva os dados.
2. Opção 2, tabela cliente: inserir uma pessoa fictícia com e-mail único; consultar
   pelo ID, atualizar a cidade e excluir. Não utilize dados pessoais reais.
3. Mostrar as 14 tabelas no menu: as mesmas quatro operações estão disponíveis em todas.
4. Consultar um item; tentar quantidade 10000 para mostrar rejeição por saldo.
5. Tentar apagar cliente 1 para demonstrar dependência referencial. Nada será apagado.
6. Opção 4: tipo `insumo`, ingrediente `1`, data `2026-08-03`: julho aparece antes de agosto.
   Explicar por que PEPS é diferente de escolher a validade mais próxima.

## 11–14 min · Consultas com gráficos

Use período 2026-07-01 a 2027-01-01. Execute as três consultas e abra os gráficos.
Explique os JOINs e a agregação de cada uma. A receita bruta total simulada é
R$ 10.602,00, distribuída em 1.188 unidades. O custo dos insumos consumidos é
R$ 2.499,00. Não subtraia esses valores para anunciar lucro: as bases são distintas,
há produção ainda não vendida e faltam outros custos.

## 14–17 min · IA generativa

Opção 5: “Quais produtos e canais merecem atenção? Cite os números e as limitações.”
Explique que a aplicação consulta o banco, serializa agregados e os envia ao LLM.
Compare uma afirmação numérica da resposta com a tabela. O modelo não escreve no
banco. Se houver erro factual, mostre como identificá-lo; não esconda a limitação.

## 17–18 min · Limpeza e fechamento

Após todas as demais demonstrações, opção 6 com `APAGAR FRUTA`; depois opção 1.
Confirme que o banco voltou à carga inicial. Explique os limites: sem gateway,
auditoria, perdas ou conciliação automática. Ambos os integrantes, se houver,
devem dominar os conceitos; a nota de apresentação é individual.

## Perguntas para estudar

- Por que o preço praticado fica no item e não é obtido do preço atual do produto?
- Por que quantidade disponível é derivada e não editada manualmente?
- O que acontece ao excluir um pai referenciado? Como desfazer uma operação com erro?
- Como evitar multiplicação indevida de receita ao juntar itens e pagamentos?
- Quais dados faltam para calcular lucro, desperdício e capacidade produtiva?
- Qual a diferença entre formulação prevista e consumo efetivo?
- O que foi efetivamente testado e o que depende do ambiente da apresentação?
