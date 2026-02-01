from flask import Flask

app = Flask(__name__)

# Configuração RUM Simplificada (Facade Pattern)
OTEL_RUM_CONFIG = """
<script src="/static/otel-rum.js"></script>
<script>
  if (!window.otel || !window.otel.setupRUM) {
    console.error("ERRO CRÍTICO: RUM não carregado.");
  } else {
    try {
        // Agora chamamos apenas UMA função que faz tudo
        const tracer = window.otel.setupRUM(
            'flask-frontend-rum', 
            'https://otel-collector.129-213-28-76.sslip.io/v1/traces'
        );

        // Inicia o trace
        const span = tracer.startSpan('carregamento_usuario_facade', {
            startTime: performance.timeOrigin
        });

        window.addEventListener('load', () => {
            span.end();
            console.log("%c [SUCESSO] Trace finalizado via Facade!", "color: green; font-weight: bold;");
        });
        
    } catch (e) {
        console.error("Erro ao iniciar RUM:", e);
    }
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
        <title>Monitoramento RUM</title>
        {OTEL_RUM_CONFIG}
    </head>
    <body>
        <h1>RUM Funcionando 🚀</h1>
        <p>Verifique o Console (F12) para a mensagem de sucesso.</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
