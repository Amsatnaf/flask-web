from flask import Flask

app = Flask(__name__)

# ==============================================================================
# CONFIGURAÇÃO RUM - MODO PRODUÇÃO (Separação de Load e Click)
# ==============================================================================
OTEL_RUM_CONFIG = """
<script type="module">
  import { WebTracerProvider } from 'https://esm.sh/@opentelemetry/sdk-trace-web@1.30.1';
  import { SimpleSpanProcessor, ConsoleSpanExporter } from 'https://esm.sh/@opentelemetry/sdk-trace-base@1.30.1';
  import { Resource } from 'https://esm.sh/@opentelemetry/resources@1.30.1';
  import { SemanticResourceAttributes } from 'https://esm.sh/@opentelemetry/semantic-conventions@1.28.0';
  import { OTLPTraceExporter } from 'https://esm.sh/@opentelemetry/exporter-trace-otlp-http@0.57.2';

  try {
      const resource = new Resource({
          [SemanticResourceAttributes.SERVICE_NAME]: 'flask-frontend-rum',
          'deployment.type': 'production_real',
          'env': 'production'
      });

      const collectorTraceUrl = 'https://otel-collector.129-213-28-76.sslip.io/v1/traces';
      const traceExporter = new OTLPTraceExporter({ url: collectorTraceUrl });
      
      const tracerProvider = new WebTracerProvider({ resource });
      tracerProvider.addSpanProcessor(new SimpleSpanProcessor(traceExporter));
      // tracerProvider.addSpanProcessor(new SimpleSpanProcessor(new ConsoleSpanExporter())); // Pode comentar em prod
      tracerProvider.register();

      const tracer = tracerProvider.getTracer('flask-rum-cdn');
      
      // -----------------------------------------------------------
      // 1. TRACE DE CARREGAMENTO (PAGE LOAD)
      // Esse aqui tem que ser RÁPIDO para seu alerta ficar verde.
      // -----------------------------------------------------------
      const loadSpan = tracer.startSpan('page_load', { startTime: performance.timeOrigin });

      window.addEventListener('load', () => {
          // Fecha o trace assim que a página termina de montar
          setTimeout(() => {
              loadSpan.end();
              console.log("✅ Page Load enviado (Rápido!)");
          }, 100); // 100ms de buffer é saudável
      });

      // -----------------------------------------------------------
      // 2. TRACE DE INTERAÇÃO (CLIQUES)
      // Criamos um NOVO span independente cada vez que o usuário clica.
      // -----------------------------------------------------------
      window.logToSigNoz = (message, severity = 'INFO') => {
          console.log(`🖱️ Interação: "${message}"`);

          // Cria um Trace NOVO e RÁPIDO só para esse clique
          const interactionSpan = tracer.startSpan('user_interaction', {
              attributes: {
                  'component': 'button',
                  'action': message
              }
          });

          // Adiciona o evento (Log)
          interactionSpan.addEvent(message, { 'log.severity': severity });
          
          if (severity === 'ERROR') {
              interactionSpan.setStatus({ code: 2, message: "Erro no clique" });
          }

          // Fecha imediatamente (Latência do clique será baixíssima)
          interactionSpan.end(); 
      };

      // Captura erros globais também como traces separados
      window.addEventListener('error', (e) => {
          const errorSpan = tracer.startSpan('js_error');
          errorSpan.setStatus({ code: 2, message: e.message });
          errorSpan.end();
      });

  } catch (e) {
      console.error("Erro RUM:", e);
  }
</script>
"""

@app.route('/')
def hello():
    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <title>RUM - Produção</title>
        {OTEL_RUM_CONFIG}
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; background-color: #eef2f5; margin: 0; }}
            .card {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center; max-width: 450px; width: 100%; }}
            .btn {{ padding: 12px 24px; margin: 10px; border: none; border-radius: 8px; cursor: pointer; color: white; font-weight: bold; }}
            .btn-info {{ background-color: #0066cc; }}
            .btn-error {{ background-color: #d93025; }}
            p {{ color: #666; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Site Rápido Novamente ⚡</h1>
            <p>Latência de load normalizada (< 1s).</p>
            <p>Cliques geram traces separados.</p>
            
            <button class="btn btn-info" onclick="window.logToSigNoz('Adicionar ao Carrinho', 'INFO')">
                🛒 Comprar
            </button>

            <button class="btn btn-error" onclick="window.logToSigNoz('Falha Checkout', 'ERROR')">
                ❌ Erro
            </button>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
