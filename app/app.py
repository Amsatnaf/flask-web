import os
import time
import logging
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
# Importamos apenas o básico do OTel para pegar o Span atual (sem configurar nada manual)
from opentelemetry import trace

app = Flask(__name__)

# --- Configuração de Logs ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuração do Banco de Dados ---
# Pega as variáveis que definimos no deployment.yaml
db_user = os.getenv("DB_USER", "root")
db_pass = os.getenv("DB_PASS", "senha")
db_host = os.getenv("DB_HOST", "127.0.0.1")
db_name = os.getenv("DB_NAME", "loja_rum")

# String de conexão do MySQL (PyMySQL driver)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Configurações para evitar queda de conexão (pool recycle)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 280, 'pool_pre_ping': True}

db = SQLAlchemy(app)

# --- Modelo da Tabela ---
class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto = db.Column(db.String(50))
    status = db.Column(db.String(20))
    valor = db.Column(db.Float)
    timestamp_epoch = db.Column(db.Float)

# --- Inicialização do Banco ---
# Tenta criar a tabela ao iniciar. Se der erro de conexão, loga mas não mata o app imediatamente.
with app.app_context():
    try:
        db.create_all()
        logger.info(f"✅ CONECTADO AO BANCO: {db_host}")
    except Exception as e:
        logger.error(f"❌ FALHA AO CONECTAR NO BANCO: {e}")

# --- Frontend RUM (HTML + JS do OpenTelemetry) ---
RUM_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Loja RUM - Observabilidade</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; text-align: center; background-color: #f4f4f9; padding: 50px; }
        .card { background: white; max-width: 400px; margin: auto; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        h1 { color: #333; }
        button { width: 100%; padding: 15px; margin: 10px 0; border: none; border-radius: 5px; font-size: 18px; cursor: pointer; transition: 0.3s; }
        .btn-buy { background-color: #28a745; color: white; }
        .btn-buy:hover { background-color: #218838; }
        .btn-error { background-color: #dc3545; color: white; }
        .btn-error:hover { background-color: #c82333; }
        #status { margin-top: 20px; font-weight: bold; color: #555; }
    </style>
    
    <script type="module">
      import { context, trace } from 'https://esm.sh/@opentelemetry/api@1.7.0';
      import { WebTracerProvider } from 'https://esm.sh/@opentelemetry/sdk-trace-web@1.30.1';
      import { BatchSpanProcessor } from 'https://esm.sh/@opentelemetry/sdk-trace-base@1.30.1';
      import { Resource } from 'https://esm.sh/@opentelemetry/resources@1.30.1';
      import { SemanticResourceAttributes } from 'https://esm.sh/@opentelemetry/semantic-conventions@1.28.0';
      import { OTLPTraceExporter } from 'https://esm.sh/@opentelemetry/exporter-trace-otlp-http@0.57.2';
      import { FetchInstrumentation } from 'https://esm.sh/@opentelemetry/instrumentation-fetch@0.34.0';
      import { W3CTraceContextPropagator } from 'https://esm.sh/@opentelemetry/core@1.30.1';

      // Configura o exportador para mandar direto pro seu SigNoz (Collector)
      const provider = new WebTracerProvider({
          resource: new Resource({ [SemanticResourceAttributes.SERVICE_NAME]: 'frontend-loja' })
      });
      
      // ATENÇÃO: Substitua o IP abaixo pelo IP do seu Ingress/Collector se necessário.
      // Como estamos usando sslip.io, ele deve resolver para o loadbalancer.
      provider.addSpanProcessor(new BatchSpanProcessor(new OTLPTraceExporter({ 
          url: 'https://otel-collector.129-213-28-76.sslip.io/v1/traces' 
      })));
      
      provider.register({ propagator: new W3CTraceContextPropagator() });
      
      // Instrumenta o 'fetch' para conectar o Frontend ao Backend no gráfico
      new FetchInstrumentation({ propagateTraceHeaderCorsUrls: [/.+/] }).setTracerProvider(provider);
      const tracer = provider.getTracer('loja-frontend');

      window.acao = (tipo) => {
          const span = tracer.startSpan(`click_${tipo}`);
          const endpoint = tipo === 'comprar' ? '/checkout' : '/simular_erro';
          
          document.getElementById('status').innerText = "Processando...";

          context.with(trace.setSpan(context.active(), span), () => {
              fetch(endpoint, { method: 'POST' })
                .then(r => r.json().then(data => ({status: r.status, body: data})))
                .then(res => { 
                    if(res.status === 200) {
                        document.getElementById('status').innerText = `✅ Sucesso! ID: ${res.body.id}`;
                        document.getElementById('status').style.color = "green";
                    } else {
                        document.getElementById('status').innerText = `❌ Erro Capturado: ${res.body.msg}`;
                        document.getElementById('status').style.color = "red";
                    }
                    span.end(); 
                })
                .catch(e => { 
                    document.getElementById('status').innerText = "Erro de Rede/Console"; 
                    span.recordException(e);
                    span.end(); 
                });
          });
      };
    </script>
</head>
<body>
    <div class="card">
        <h1>🛍️ Loja RUM</h1>
        <p>Simule transações para gerar rastros no SigNoz.</p>
        <button class="btn-buy" onclick="window.acao('comprar')">COMPRAR (Sucesso)</button>
        <button class="btn-error" onclick="window.acao('erro')">GERAR ERRO (Falha)</button>
        <div id="status">Aguardando ação...</div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return RUM_HTML

@app.route('/checkout', methods=['POST'])
def checkout():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("processar_pagamento"):
        try:
            logger.info("Iniciando checkout...")
            novo = Pedido(produto="PlayStation 5", status="PAGO", valor=4500.00, timestamp_epoch=time.time())
            db.session.add(novo)
            db.session.commit()
            logger.info(f"Pedido salvo com ID: {novo.id}")
            return jsonify({"status": "sucesso", "id": novo.id})
        except Exception as e:
            logger.error(f"Erro no checkout: {e}")
            # Registra a exceção no SigNoz automaticamente
            trace.get_current_span().record_exception(e)
            return jsonify({"status": "erro", "msg": str(e)}), 500

@app.route('/simular_erro', methods=['POST'])
def simular_erro():
    # Esta rota serve para pintar o gráfico de vermelho propositalmente
    logger.error("Simulação de erro solicitada!")
    # Lançamos um erro genérico que o agente Python vai pegar
    raise Exception("Falha de Conexão Simulada com Gateway de Pagamento")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
