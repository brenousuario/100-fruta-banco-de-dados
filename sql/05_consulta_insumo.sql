-- Q3: consumo e custo de materia-prima por fornecedor (4 tabelas).
-- Custo historico do lote, nao custo total de fabricacao nem lucro.
SELECT f.nome AS fornecedor,
       SUM(c.quantidade_kg)::numeric(14,3) AS kg_consumidos,
       SUM(c.quantidade_kg * l.custo_kg)::numeric(14,2) AS custo_insumos
FROM fruta.fornecedor f
JOIN fruta.lote_insumo l ON l.fornecedor_id = f.id
JOIN fruta.consumo_insumo c ON c.lote_insumo_id = l.id
JOIN fruta.lote_producao p ON p.id = c.lote_producao_id
WHERE p.produzido_em >= %(inicio)s AND p.produzido_em < %(fim)s
GROUP BY f.id, f.nome
ORDER BY custo_insumos DESC, fornecedor;
