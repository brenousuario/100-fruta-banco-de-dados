-- Q2: unidades e receita bruta por produto (4 tabelas).
SELECT pr.nome AS produto,
       SUM(i.quantidade) AS unidades,
       SUM(i.quantidade * i.preco_unitario)::numeric(14,2) AS receita
FROM fruta.produto pr
JOIN fruta.lote_producao l ON l.produto_id = pr.id
JOIN fruta.item_pedido i ON i.lote_producao_id = l.id
JOIN fruta.pedido p ON p.id = i.pedido_id
WHERE p.data_pedido >= %(inicio)s AND p.data_pedido < %(fim)s
GROUP BY pr.id, pr.nome
ORDER BY receita DESC, produto;
