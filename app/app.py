from flask import Flask

app = Flask(__name__)

# Configuração do RUM (Real User Monitoring) via OpenTelemetry
# Agora usando o arquivo local 'otel-rum.js' gerado pelo esbuild
OTEL_RUM_CONFIG = """
<script src="/static/otel-rum.js"></script>

<script>
  // Verifica se o arquivo carregou corretamente
  if (!window.otel) {
    console.error("Erro: O arquivo otel-rum.js não foi carregado ou window.otel não existe.");
  } else {
    
    // 1. Acessa as bibliotecas que empacotamos no window.otel
    const { WebTracerProvider } = window.otel.sdkTraceWeb;
    const { OTLPTraceExporter } = window.otel.exporterTraceOTLPHttp;
    const { SimpleSpanProcessor, ConsoleSpanExporter } = window.otel.sdkTraceBase;
    const { Resource } = window.otel.resources;
    const { SemanticResourceAttributes } = window.otel.semanticConventions;

    // 2. Configura o destino (SigNoz)
    // IMPORTANTE: Para OTLP HTTP, o padrão é terminar com /v1/traces
    const collectorUrl = 'https://otel-collector.129-213-28-76.sslip.io/v1/traces';

    const exporter = new OTLPTraceExporter({
      url: collectorUrl,
    });

    // 3. Define quem é este serviço (aparecerá assim no SigNoz)
    const provider = new WebTracerProvider({
      resource: new Resource({
        [SemanticResourceAttributes.SERVICE_NAME]: 'flask-frontend-rum',
        [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
      }),
    });

    // Adiciona o exportador para o SigNoz
    provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
    
    // Adiciona exportador para o Console (Ajuda a ver erros no F12 do navegador)
    provider.addSpanProcessor(new SimpleSpanProcessor(new ConsoleSpanExporter()));

    provider.register();

    // 4. Inicia um rastro de teste (carregamento da página)
    const tracer = provider.getTracer('flask-rum-app');
    const span = tracer.startSpan('page_load_init');

    window.addEventListener('load', () => {
      span.end();
      console.log(`%c [RUM] Dados enviados para: ${collectorUrl}`, 'color: #4CAF50; font-weight: bold;');
    });
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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>App Monitorado - RUM Local</title>
        {OTEL_RUM_CONFIG}
        <style>
            body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5; margin: 0; }}
            .card {{ background: white; padding: 2.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; max-width: 450px; }}
            h1 {{ color: #007bff; margin-bottom: 1rem; font-size: 1.8rem; }}
            p {{ color: #6c757d; line-height: 1.5; }}
            .badge {{ background: #28a745; color: white; padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; display: inline-block; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Monitoramento RUM 🚀</h1>
            <p>Este app carrega as bibliotecas OpenTelemetry localmente.</p>
            <p>Verifique o <b>Console (F12)</b> para ver os logs de envio.</p>
            <span class="badge">Status: OTLP Ativo</span>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
