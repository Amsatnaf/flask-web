from flask import Flask

app = Flask(__name__)

# Configuração RUM Final (Blindada contra erros de versão)
OTEL_RUM_CONFIG = """
<script src="/static/otel-rum.js"></script>

<script>
  if (!window.otel) {
    console.error("ERRO: window.otel não carregou.");
  } else {
    // 1. Acessa as ferramentas do nosso bundle
    const { 
        WebTracerProvider, 
        OTLPTraceExporter, 
        SimpleSpanProcessor, 
        ConsoleSpanExporter,
        resourceFromAttributes // Usando a função auxiliar
    } = window.otel;

    // 2. Configura SigNoz
    const collectorUrl = 'https://otel-collector.129-213-28-76.sslip.io/v1/traces';
    const exporter = new OTLPTraceExporter({ url: collectorUrl });

    // 3. Cria o Resource usando a função (em vez de new Resource)
    // Usamos strings diretas ('service.name') para evitar erros de constantes
    const myResource = resourceFromAttributes({
        'service.name': 'flask-frontend-rum',
        'service.version': '1.0.0'
    });

    // 4. Cria o Provider
    const provider = new WebTracerProvider({
      resource: myResource
    });

    provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
    provider.addSpanProcessor(new SimpleSpanProcessor(new ConsoleSpanExporter()));

    provider.register();

    // 5. Inicia o trace (Usando performance.timeOrigin para precisão)
    const tracer = provider.getTracer('flask-rum-app');
    const span = tracer.startSpan('carregamento_usuario_real', {
        startTime: performance.timeOrigin
    });

    window.addEventListener('load', () => {
      span.end();
      console.log(`%c [SUCESSO] RUM enviado para: ${collectorUrl}`, 'color: #00ff00; background: #333; padding: 4px;');
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
        <title>Monitoramento RUM</title>
        {OTEL_RUM_CONFIG}
        <style>
            body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f4f4f9; margin: 0; }}
            .container {{ text-align: center; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; }}
            .badge {{ background: #007bff; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Monitoramento RUM 🚀</h1>
            <p>Se deu certo, verifique o Console (F12) e a aba Network.</p>
            <span class="badge">Versão Final</span>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
