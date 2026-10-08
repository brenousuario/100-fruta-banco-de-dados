# Registro de validação

Preparação: 21/09/2026. Foram aprovados 16 testes automatizados (arquivo
`tests/test_app.py`), com os seguintes grupos:

1. Estrutura e quantidade de registros nas 14 tabelas.
2. Inserção, consulta, atualização e exclusão nas 14 tabelas; IDs após a carga.
3. Proteção referencial e rollback após erro.
4. Chaves únicas, quantidades, preços e incompatibilidade mel/vegano.
5. Rejeição de consumo acima do saldo e redução indevida do lote de insumo.
6. Rejeição de venda acima do saldo e redução indevida da produção.
7. Coerência temporal em operações e alterações retroativas.
8. Capacidade e unicidade das inscrições em workshops.
9. PEPS, desempate previsto por ID e exclusão de vencidos.
10. Três consultas comparadas com cálculo independente sobre os dados de carga.
11. Limites do período e resultado vazio.
12. Identificadores restritos e tratamento de texto com apóstrofo/comandos aparentes.
13. Repetição segura da inicialização.
14. Contrato HTTP da IA com resposta controlada e ausência de e-mail de cliente no contexto.
15. Falha de conexão da IA sem fabricar uma resposta.
16. Eliminação e reconstrução do schema dentro de transação de teste.

Ambiente: Python 3.12; Psycopg 3.3.6; PGlite com interface TCP PostgreSQL.
As operações passaram pelo driver da aplicação e o SQL foi executado pelo motor
PostgreSQL compilado para WebAssembly. Não foi uma simulação do SQL em SQLite.
A base usada nos gráficos foi reconstruída após o teste e consultada pela aplicação.

Limites: esse ambiente não equivale à homologação de um servidor nativo PostgreSQL 16.
A imagem Docker fornecida não foi executada aqui. Não foram realizados testes de
carga, múltiplos usuários, inferência de LLM real ou validação dos dados pela empresa.
O teste de IA usa mock apenas no teste; o código da aplicação chama o serviço real.
O arquivo de resposta controlada é removido e não faz parte dos resultados entregues.

Os gráficos e o relatório passaram por inspeção visual. Os dados de carga são
sintéticos; as formulações e validades não têm validação técnica de produção.
