-- Q1: vendas brutas de balas por mes e canal (3 tabelas).
-- Intervalo semiaberto: inclui inicio, exclui fim.
SELECT to_char(p.data_pedido, 'YYYY-MM') AS mes,
       c.nome AS canal,
       SUM(i.quantidade * i.preco_unitario)::numeric(14,2) AS receita
FROM fruta.pedido p
JOIN fruta.canal_venda c ON c.id = p.canal_venda_id
JOIN fruta.item_pedido i ON i.pedido_id = p.id
WHERE p.data_pedido >= %(inicio)s AND p.data_pedido < %(fim)s
GROUP BY to_char(p.data_pedido, 'YYYY-MM'), c.id, c.nome
ORDER BY mes, canal;
