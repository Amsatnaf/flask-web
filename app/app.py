from flask import Flask

app = Flask(__name__)

# Configuração do RUM (Real User Monitoring) corrigida para o seu Bundle
OTEL_RUM_CONFIG = """
<script src="/static/otel-rum.js"></script>

<script>
  // Função para garantir que o script carregou
  if (!window.otel) {
    console.error("ERRO CRÍTICO: window.otel não existe. O arquivo JS não carregou.");
  } else {
    
    // 1. Pegando as ferramentas que TEMOS CERTEZA que existem pelo seu log
    const { WebTracerProvider } = window.otel.sdkTraceWeb;
    const { OTLPTraceExporter } = window.otel.exporterTraceOTLPHttp;
    const { SimpleSpanProcessor, ConsoleSpanExporter } = window.otel.sdkTraceBase;
    
    // AQUI ESTAVA O ERRO: Trocamos 'Resource' por 'resourceFromAttributes'
    const { resourceFromAttributes } = window.otel.resources;

    // 2. Configura o envio para o SigNoz
    const collectorUrl = 'https://otel-collector.129-213-28-76.sslip.io/v1/traces';

    const exporter = new OTLPTraceExporter({
      url: collectorUrl,
    });

    // 3. Cria o Resource usando a função auxiliar (Workaround para o erro de construtor)
    // Usamos a string 'service.name' direto para evitar erros de importação
    const myResource = resourceFromAttributes({
        'service.name': 'flask-frontend-rum',
        'service.version': '1.0.0'
    });

    // 4. Cria o provedor com o resource correto
    const provider = new WebTracerProvider({
      resource: myResource
    });

    provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
    provider.addSpanProcessor(new SimpleSpanProcessor(new ConsoleSpanExporter())); // Log no console para debug

    provider.register();

    // 5. Inicia o rastreamento (Agora pegando o tempo real de navegação)
    const tracer = provider.getTracer('flask-rum-app');
    
    // performance.timeOrigin garante que pegamos o tempo desde o clique do usuário
    const span = tracer.startSpan('carregamento_total_usuario', {
        startTime: performance.timeOrigin 
    });

    window.addEventListener('load', () => {
      span.end();
      console.log(`%c [SUCESSO] RUM enviado para: ${collectorUrl}`, 'color: #00ff00; background: #333; font-size: 14px; padding: 4px;');
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
            .status {{ color: green; font-weight: bold; margin-top: 10px; display: block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Monitoramento RUM 🚀</h1>
            <p>Se você ver a mensagem verde no Console (F12), funcionou!</p>
            <span class="status">● Sistema Operante</span>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
