import time
import os
import logging
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

# --- OPENTELEMETRY (Backend) ---
# Usamos apenas a API para pegar o tracer. 
# A instrumentação pesada (Exporters) vem do Agente do SigNoz (Annotation do K8s).
from opentelemetry import trace

# Pega o tracer global configurado pelo SigNoz
tracer = trace.get_tracer(__name__)

app = Flask(__name__)

# --- Configuração do Banco de Dados ---
db_user = os.getenv("DB_USER", "root")
db_pass = os.getenv("DB_PASS", "senha")
db_host = os.getenv("DB_HOST", "127.0.0.1")
db_name = os.getenv("DB_NAME", "loja_rum")

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Configurações para evitar queda de conexão pelo Firewall da GCP
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,
    'pool_pre_ping': True
}

db = SQLAlchemy(app)

# --- Modelo ---
class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto = db.Column(db.String(50))
    status = db.Column(db.String(20))
    valor = db.Column(db.Float)
    timestamp_epoch = db.Column(db.Float)

# Inicializa DB
with app.app_context():
    try:
        db.create_all()
        print(f"INFO: Conectado ao MySQL em {db_host}")
    except Exception as e:
        print(f"ERRO: Falha ao conectar DB: {e}")

# --- FRONTEND RUM (CORRIGIDO) ---
RUM_HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Loja SigNoz RUM</title>
    <link rel="preconnect" href="https://esm.sh" crossorigin>
    
    <script type="module">
      // 1. IMPORT CORRIGIDO: Adicionamos 'trace' aqui
      import { propagation, context, trace } from 'https://esm.sh/@opentelemetry/api@1.7.0';
      import { WebTracerProvider } from 'https://esm.sh/@opentelemetry/sdk-trace-web@1.30.1';
      import { BatchSpanProcessor } from 'https://esm.sh/@opentelemetry/sdk-trace-base@1.30.1';
      import { Resource } from 'https://esm.sh/@opentelemetry/resources@1.30.1';
      import { SemanticResourceAttributes } from 'https://esm.sh/@opentelemetry/semantic-conventions@1.28.0';
      import { OTLPTraceExporter } from 'https://esm.sh/@opentelemetry/exporter-trace-otlp-http@0.57.2';
      import { FetchInstrumentation } from 'https://esm.sh/@opentelemetry/instrumentation-fetch@0.34.0';
      import { W3CTraceContextPropagator } from 'https://esm.sh/@opentelemetry/core@1.30.1';

      try {
          console.log("Iniciando RUM...");
          const collectorUrl = 'https://otel-collector.129-213-28-76.sslip.io/v1/traces';
          
          const resource = new Resource({
              [SemanticResourceAttributes.SERVICE_NAME]: 'flask-frontend-rum',
          });

          const provider = new WebTracerProvider({ resource });
          
          // Batching para performance
          provider.addSpanProcessor(new BatchSpanProcessor(new OTLPTraceExporter({ url: collectorUrl })));
          
          // Importante: W3C Propagator conecta o Front ao Back
          provider.register({ propagator: new W3CTraceContextPropagator() });

          // Instrumenta o Fetch (AJAX)
          const fetchInstr = new FetchInstrumentation({
              propagateTraceHeaderCorsUrls: [/.+/],
          });
          fetchInstr.setTracerProvider(provider);

          const tracer = provider.getTracer('frontend-loja');

          // Função Global de Ação
          window.realAction = (actionType) => {
              console.log(`Click: ${actionType}`);
              
              const span = tracer.startSpan(`click_${actionType.toLowerCase()}`);
              
              // 2. CORREÇÃO CRÍTICA: Usar trace.setSpan em vez de propagation.setSpan
              context.with(trace.setSpan(context.active(), span), () => {
                  
                  const endpoint = actionType === 'COMPRAR' ? '/checkout' : '/simular_erro';
                  
                  // O fetch vai herdar o contexto automaticamente por causa do context.with
                  fetch(endpoint, { method: 'POST' })
                    .then(r => r.json())
                    .then(data => {
                        console.log("Sucesso:", data);
                        span.setStatus({ code: 1 }); // OK
                        alert("Retorno: " + (data.status || 'OK'));
                    })
                    .catch(e => {
                        console.error("Erro:", e);
                        span.recordException(e);
                        span.setStatus({ code: 2, message: e.message }); // ERROR
                        alert("Erro! Veja o console.");
                    })
                    .finally(() => {
                        span.end();
                    });
              });
          };
          console.log("RUM Pronto!");

      } catch (e) { console.error("Erro RUM:", e); }
    </script>
</head>
<body style="font-family: sans-serif; text-align: center; padding: 50px;">
    <h1>🛒 Loja Integrada (OCI + GCP)</h1>
    <p>Monitoramento: Frontend -> Backend -> DB</p>
    <div style="margin-top:20px;">
        <button style="padding:15px 30px; background:blue; color:white; cursor:pointer;" onclick="window.realAction('COMPRAR')">🛍️ Comprar</button>
        <button style="padding:15px 30px; background:red; color:white; cursor:pointer; margin-left:10px;" onclick="window.realAction('ERROR')">💣 Erro</button>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return RUM_HTML

@app.route('/checkout', methods=['POST'])
def checkout():
    # O SigNoz já criou o span pai. Criamos um span manual filho aqui.
    with tracer.start_as_current_span("logica_negocio_backend"):
        try:
            time.sleep(0.05) # Simula processamento
            
            # Gravando no MySQL GCP (Gera span automático do SQLAlchemy)
            novo = Pedido(produto="Gamer PC", status="PAGO", valor=5000.0, timestamp_epoch=time.time())
            db.session.add(novo)
            db.session.commit()
            
            return jsonify({"status": "compra_sucesso", "id": novo.id})
        except Exception as e:
            db.session.rollback()
            # Registra erro no span atual
            trace.get_current_span().record_exception(e)
            return jsonify({"status": "erro", "msg": str(e)}), 500

@app.route('/simular_erro', methods=['POST'])
def simular_erro():
    with tracer.start_as_current_span("logica_falha_backend"):
        try:
            falha = Pedido(produto="Bug", status="ERRO", valor=0.0, timestamp_epoch=time.time())
            db.session.add(falha)
            db.session.commit()
            
            raise ValueError("Simulacao de Crash no Python!")
        except Exception as e:
            trace.get_current_span().record_exception(e)
            trace.get_current_span().set_status(trace.Status(trace.StatusCode.ERROR))
            return jsonify({"status": "erro_capturado", "msg": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True)
