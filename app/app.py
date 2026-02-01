from flask import Flask

app = Flask(__name__)

# ==============================================================================
# CONFIGURAÇÃO RUM - VERSÃO EVENTS (O "Pulo do Gato")
# Em vez de brigar com o LogExporter, usamos o TraceExporter que JÁ FUNCIONA.
# ==============================================================================
OTEL_RUM_CONFIG = """
<script type="module">
  import { WebTracerProvider } from 'https://esm.sh/@opentelemetry/sdk-trace-web@1.30.1';
  import { SimpleSpanProcessor, ConsoleSpanExporter } from 'https://esm.sh/@opentelemetry/sdk-trace-base@1.30.1';
  import { Resource } from 'https://esm.sh/@opentelemetry/resources@1.30.1';
  import { SemanticResourceAttributes } from 'https://esm.sh/@opentelemetry/semantic-conventions@1.28.0';
  import { OTLPTraceExporter } from 'https://esm.sh/@opentelemetry/exporter-trace-otlp-http@0.57.2';

  // Nota: Não importamos mais nada de LOGS. Vamos usar apenas TRACES.

  console.log("🚀 Iniciando RUM (Modo Span Events)...");

  try {
      const resource = new Resource({
          [SemanticResourceAttributes.SERVICE_NAME]: 'flask-frontend-rum',
          'deployment.type': 'cdn_loading',
          'env': 'production'
      });

      // --- TRACES (O Canal que sabemos que funciona) ---
      const collectorTraceUrl = 'https://otel-collector.129-213-28-76.sslip.io/v1/traces';
      const traceExporter = new OTLPTraceExporter({ url: collectorTraceUrl });
      
      const tracerProvider = new WebTracerProvider({ resource });
      tracerProvider.addSpanProcessor(new SimpleSpanProcessor(traceExporter));
      tracerProvider.addSpanProcessor(new SimpleSpanProcessor(new ConsoleSpanExporter()));
      tracerProvider.register();

      const tracer = tracerProvider.getTracer('flask-rum-cdn');
      
      // Iniciamos o Trace Principal
      window.rootSpan = tracer.startSpan('carregamento_via_cdn', { 
          startTime: performance.timeOrigin 
      });

      // -----------------------------------------------------
      // A NOVA FUNÇÃO MÁGICA (Sem LogExporter)
      // -----------------------------------------------------
      window.logToSigNoz = (message, severity = 'INFO') => {
          console.log(`🔗 [EVENTO] Adicionando ao Trace: "${message}"`);

          // Em vez de logger.emit, usamos addEvent dentro do próprio Span.
          // Isso garante que o dado fique "grudado" no Trace ID.
          window.rootSpan.addEvent(message, {
              'log.severity': severity,
              'page.url': window.location.href,
              'component': 'button_click'
          });
          
          // Se for erro, também marcamos o status do Span para ficar vermelho no gráfico
          if (severity === 'ERROR') {
              window.rootSpan.setStatus({ code: 2, message: message }); // 2 = ERROR
          }
      };

      window.addEventListener('load', () => {
          window.logToSigNoz("Página carregada (Evento)", "INFO");
          
          setTimeout(() => {
              window.rootSpan.end();
              console.log("✅ Trace enviado com eventos anexados.");
          }, 500);
      });

      window.addEventListener('error', (e) => {
          window.logToSigNoz(`Erro JS: ${e.message}`, "ERROR");
      });

  } catch (e) {
      console.error("❌ Erro RUM:", e);
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
        <title>RUM - Span Events</title>
        {OTEL_RUM_CONFIG}
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5; margin: 0; }}
            .card {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center; max-width: 450px; width: 100%; }}
            h1 {{ color: #2d3e50; margin-bottom: 10px; font-size: 24px; }}
            p {{ color: #6c757d; margin-bottom: 30px; }}
            .btn-group {{ display: flex; gap: 15px; justify-content: center; }}
            .btn {{ padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; color: white; transition: 0.2s; }}
            .btn-info {{ background-color: #0066cc; }}
            .btn-error {{ background-color: #d93025; }}
            .status {{ margin-top: 20px; font-size: 12px; color: #aaa; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>RUM via Span Events 🎯</h1>
            <p>Se o Trace chega, o Log chega junto.</p>
            <div class="btn-group">
                <button class="btn btn-info" onclick="window.logToSigNoz('Click Info', 'INFO')">Registrar Evento</button>
                <button class="btn btn-error" onclick="window.logToSigNoz('Erro Crítico', 'ERROR')">Registrar Erro</button>
            </div>
            <div class="status">Verifique a aba "Events" no SigNoz</div>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
