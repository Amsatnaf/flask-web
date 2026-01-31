from flask import Flask

app = Flask(__name__)

# Configuração do OpenTelemetry RUM (Real User Monitoring)
# Este script será executado no navegador do seu cliente.
OTEL_RUM_CONFIG = """
<!-- SDKs do OpenTelemetry -->
<script src="https://cdn.jsdelivr.net"></script>
<script src="https://cdn.jsdelivr.net"></script>
<script src="https://cdn.jsdelivr.net"></script>

<script>
  const { WebTracerProvider } = window.otel.sdkTraceWeb;
  const { OTLPTraceExporter } = window.otel.exporterTraceOTLPHttp;
  const { SimpleSpanProcessor } = window.otel.sdkTraceBase;
  const { Resource } = window.otel.resources;
  const { SemanticResourceAttributes } = window.otel.semanticConventions;

  // 1. Configura o exportador para o seu Ingress HTTPS
  const exporter = new OTLPTraceExporter({
    url: 'https://otel-collector.129-213-28-76.sslip.io',
  });

  // 2. Define o nome do serviço que aparecerá no SigNoz
  const provider = new WebTracerProvider({
    resource: new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: 'flask-frontend-rum',
    }),
  });

  provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
  provider.register();

  // 3. Inicia o rastreamento do carregamento da página
  const tracer = provider.getTracer('browser-tracer');
  const span = tracer.startSpan('visualizacao_pagina_principal');

  window.addEventListener('load', () => {
    span.end(); // Finaliza a medição quando a página está pronta
    console.log("Métricas RUM enviadas para o SigNoz!");
  });
</script>
"""

@app.route('/')
def hello():
    # Retornamos o HTML estruturado com o monitoramento no <head>
    return f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>App Monitorado - RUM</title>
        {OTEL_RUM_CONFIG}
        <style>
            body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f2f5; }}
            .card {{ background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }}
            .status {{ color: #28a745; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>CI - CD com Rancher Fleet e GitHub 🚀</h1>
            <p>Sua latência de servidor foi de 3.38ms, mas agora estamos medindo a sua <b>experiência real</b>.</p>
            <p class="status">Monitoramento Full-Stack Ativo (SigNoz + OTel)</p>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    # host 0.0.0.0 é obrigatório para rodar dentro do container/Kubernetes
    app.run(host='0.0.0.0', port=8080)
