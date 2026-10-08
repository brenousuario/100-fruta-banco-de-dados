"""Testes de integracao. Usa e recria apenas o schema fruta do DATABASE_URL.
Executar somente em banco de teste com FRUTA_TEST_ALLOW_RESET=1.
"""
import json
import os
import sys
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from io import BytesIO
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
import psycopg

FIXTURE=json.loads((Path(__file__).parent/'seed_fixture.json').read_text())

class Integration(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if os.getenv('FRUTA_TEST_ALLOW_RESET')!='1':
   raise unittest.SkipTest('Use banco de teste e FRUTA_TEST_ALLOW_RESET=1 para autorizar reinicialização.')
  with app.connect() as c:
   app.drop_schema(c); app.initialize(c)
 @classmethod
 def tearDownClass(cls):
  # Mantem carga original para gerar os resultados; cada teste sofreu rollback.
  pass
 def setUp(self):
  self.c=app.connect()
  self.c.execute('SELECT 1')  # transacao externa: CRUD usa savepoints
 def tearDown(self):
  self.c.rollback();self.c.close()
 def assert_rejected(self,statement,params=None):
  with self.assertRaises(psycopg.Error):
   with self.c.transaction():self.c.execute(statement,params)
 def test_01_schema_and_seed(self):
  for t in app.TABLES:
   with self.subTest(table=t):
    n=self.c.execute(app.sql.SQL('SELECT COUNT(*) n FROM fruta.{}').format(app.sql.Identifier(t))).fetchone()['n']
    self.assertEqual(n,len(FIXTURE[t]))
 def test_02_crud_all_14_tables(self):
  records={}
  cases=[
   ('cliente',dict(nome='Pessoa de teste',email='test@example.com',cidade='Araranguá'),{'cidade':'Turvo'}),
   ('fornecedor',dict(nome='Fornecedor teste',cidade='Turvo',contato='teste@example.com'),{'cidade':'Sombrio'}),
   ('ingrediente',dict(nome='Ingrediente teste'),{'nome':'Ingrediente teste editado'}),
   ('lote_insumo',dict(fornecedor_id='@fornecedor',ingrediente_id='@ingrediente',codigo='TEST-INS',recebido_em='2026-10-01',validade='2026-10-30',quantidade_kg=10,custo_kg=12),{'custo_kg':13}),
   ('produto',dict(nome='Produto teste',sabor='Manga',adocante='demerara',vegano=True,peso_g=40,preco_referencia=8),{'preco_referencia':9}),
   ('formulacao',dict(produto_id='@produto',ingrediente_id='@ingrediente',kg_por_100_unidades=4),{'kg_por_100_unidades':3}),
   ('lote_producao',dict(produto_id='@produto',codigo='TEST-PROD',produzido_em='2026-10-03',validade='2026-10-25',quantidade_unidades=100),{'quantidade_unidades':110}),
   ('consumo_insumo',dict(lote_producao_id='@lote_producao',lote_insumo_id='@lote_insumo',quantidade_kg=4),{'quantidade_kg':3}),
   ('canal_venda',dict(nome='Canal teste'),{'nome':'Canal teste editado'}),
   ('pedido',dict(cliente_id='@cliente',canal_venda_id='@canal_venda',data_pedido='2026-10-10'),{'status':'enviado'}),
   ('item_pedido',dict(pedido_id='@pedido',lote_producao_id='@lote_producao',quantidade=2,preco_unitario=8),{'quantidade':3}),
   ('pagamento',dict(pedido_id='@pedido',pago_em='2026-10-10',valor=24,meio='pix'),{'meio':'cartao'}),
   ('workshop',dict(titulo='Workshop teste',inicio='2026-10-20 19:00:00',vagas=5,preco=30),{'vagas':6}),
   ('inscricao',dict(cliente_id='@cliente',workshop_id='@workshop',inscrito_em='2026-10-01'),{'inscrito_em':'2026-10-02'})]
  for table,values,changes in cases:
   with self.subTest(table=table):
    values={k:records[v[1:]] if isinstance(v,str) and v.startswith('@') else v for k,v in values.items()}
    row=app.insert_record(self.c,table,values);records[table]=row['id']
    self.assertGreater(row['id'],len(FIXTURE[table]))
    self.assertEqual(len(app.list_records(self.c,table,row['id'])),1)
    updated=app.update_record(self.c,table,row['id'],changes)
    for key,value in changes.items():self.assertEqual(str(updated[key]),str(value)) if isinstance(value,str) else self.assertEqual(updated[key],value)
  for table in reversed(app.TABLES):
   app.delete_record(self.c,table,records[table]);self.assertEqual(app.list_records(self.c,table,records[table]),[])
 def test_03_foreign_key_protects_parent(self):
  with self.assertRaises((psycopg.errors.ForeignKeyViolation,psycopg.errors.RestrictViolation)):app.delete_record(self.c,'cliente',1)
  self.assertEqual(len(app.list_records(self.c,'cliente',1)),1)
 def test_04_unique_and_check(self):
  self.assert_rejected("INSERT INTO fruta.cliente(nome,email,cidade) VALUES('X','cliente1@example.com','X')")
  self.assert_rejected('UPDATE fruta.produto SET preco_referencia=-1 WHERE id=1')
  self.assert_rejected("UPDATE fruta.produto SET adocante='mel',vegano=true WHERE id=1")
  self.assert_rejected('UPDATE fruta.item_pedido SET quantidade=0 WHERE id=1')
 def test_05_no_overdraw_ingredients(self):
  self.assert_rejected('UPDATE fruta.consumo_insumo SET quantidade_kg=10000 WHERE id=1')
  self.assert_rejected('UPDATE fruta.lote_insumo SET quantidade_kg=0.1 WHERE id=1')
 def test_06_no_overdraw_products(self):
  self.assert_rejected('UPDATE fruta.item_pedido SET quantidade=10000 WHERE id=1')
  self.assert_rejected('UPDATE fruta.lote_producao SET quantidade_unidades=1 WHERE id=1')
 def test_07_dates(self):
  self.assert_rejected("UPDATE fruta.pedido SET data_pedido='2027-01-01' WHERE id=1")
  self.assert_rejected("UPDATE fruta.lote_insumo SET validade='2026-07-02' WHERE id=1")
  self.assert_rejected("UPDATE fruta.lote_producao SET produzido_em='2026-07-12' WHERE id=1")
  self.assert_rejected('UPDATE fruta.item_pedido SET lote_producao_id=36 WHERE id=1')
  self.c.execute('SET LOCAL search_path TO public')
  self.c.execute('UPDATE fruta.item_pedido SET quantidade=quantidade WHERE id=1')
 def test_08_workshop(self):
  self.assert_rejected('UPDATE fruta.workshop SET vagas=1 WHERE id=1')
  self.assert_rejected("UPDATE fruta.inscricao SET inscrito_em='2027-01-01' WHERE id=1")
  self.assert_rejected('UPDATE fruta.inscricao SET cliente_id=2 WHERE id=1')
 def test_09_peps(self):
  rows=app.peps(self.c,'produto',1,'2026-08-03')
  self.assertEqual([r['codigo'] for r in rows],['PROD-08-01'])
  rows=app.peps(self.c,'insumo',1,'2026-08-03')
  self.assertEqual([r['codigo'] for r in rows],['INS-07-01','INS-08-01'])
  self.assertEqual(app.peps(self.c,'produto',1,'2027-12-01'),[])
 def test_10_queries_match_independent_oracle(self):
  monthly={};products={};suppliers={}
  orders={r['id']:r for r in FIXTURE['pedido']};lots={r['id']:r for r in FIXTURE['lote_producao']}
  names={r['id']:r['nome'] for r in FIXTURE['produto']};channels={r['id']:r['nome'] for r in FIXTURE['canal_venda']}
  for item in FIXTURE['item_pedido']:
   o=orders[item['pedido_id']];key=(o['data_pedido'][:7],channels[o['canal_venda_id']]);value=Decimal(str(item['preco_unitario']))*item['quantidade']
   monthly[key]=monthly.get(key,Decimal(0))+value
   name=names[lots[item['lote_producao_id']]['produto_id']];old=products.get(name,(0,Decimal(0)))
   products[name]=(old[0]+item['quantidade'],old[1]+value)
  ilots={r['id']:r for r in FIXTURE['lote_insumo']};snames={r['id']:r['nome'] for r in FIXTURE['fornecedor']}
  for c in FIXTURE['consumo_insumo']:
   l=ilots[c['lote_insumo_id']];name=snames[l['fornecedor_id']];q=Decimal(str(c['quantidade_kg']));old=suppliers.get(name,(Decimal(0),Decimal(0)))
   suppliers[name]=(old[0]+q,old[1]+q*Decimal(str(l['custo_kg'])))
  q1=app.query_report(self.c,1);q2=app.query_report(self.c,2);q3=app.query_report(self.c,3)
  self.assertEqual({(r['mes'],r['canal']):r['receita'] for r in q1},monthly)
  self.assertEqual({r['produto']:(r['unidades'],r['receita']) for r in q2},products)
  self.assertEqual({r['fornecedor']:(r['kg_consumidos'],r['custo_insumos']) for r in q3},suppliers)
  self.assertEqual(sum(r['receita'] for r in q1),sum(r['receita'] for r in q2))
 def test_11_period_and_empty(self):
  self.assertEqual(len(app.query_report(self.c,1,'2026-07-01','2026-08-01')),3)
  self.assertEqual(app.query_report(self.c,1,'2025-01-01','2026-01-01'),[])
  with self.assertRaises(ValueError):app.period('2027-01-01','2026-01-01')
 def test_12_identifiers_and_parameters(self):
  with self.assertRaises(ValueError):app.list_records(self.c,'cliente; DROP SCHEMA fruta CASCADE')
  with self.assertRaises(ValueError):app.update_record(self.c,'cliente',1,{'id':99})
  marker="O'Connor; DROP TABLE cliente; --"
  app.update_record(self.c,'cliente',1,{'nome':marker})
  self.assertEqual(app.list_records(self.c,'cliente',1)[0]['nome'],marker)
 def test_13_repeated_init_is_safe(self):
  with self.assertRaises(ValueError):app.initialize(self.c)
  self.assertEqual(len(app.list_records(self.c,'produto')),6)
 def test_14_ai_http_contract_only_not_real_model(self):
  # Contrato HTTP verificado com resposta controlada. NAO e inferencia de um LLM real.
  with patch('urllib.request.urlopen',return_value=BytesIO(b'{"response":"Resposta de teste controlada"}')) as mock:
   self.assertIn('teste controlada',app.ai_analysis(self.c,'2026-07-01','2027-01-01','Analise'))
   request=mock.call_args.args[0];payload=json.loads(request.data)
   self.assertFalse(payload['stream']);self.assertIn('DADOS JSON',payload['prompt'])
   self.assertNotIn('cliente1@example.com',payload['prompt'])
  for name in ('analise_ia.md','contexto_ia.json'):(app.ROOT/'resultados'/name).unlink(missing_ok=True)
 def test_15_ai_error_no_fake_response(self):
  with patch('urllib.request.urlopen',side_effect=app.urllib.error.URLError('offline')):
   with self.assertRaisesRegex(RuntimeError,'Nenhuma resposta foi simulada'):
    app.ai_analysis(self.c,'2026-07-01','2027-01-01','Analise')
 def test_16_drop_and_recreate_transactionally(self):
  # Tudo desfeito no tearDown; testa a funcao de limpeza, inclusive views/triggers.
  app.drop_schema(self.c)
  self.assertIsNone(self.c.execute("SELECT 1 FROM pg_namespace WHERE nspname='fruta'").fetchone())
  app.initialize(self.c)
  self.assertEqual(len(app.list_records(self.c,'produto')),6)

if __name__=='__main__':unittest.main(verbosity=2)
