// Importações
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { SimpleSpanProcessor, ConsoleSpanExporter } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

// Função que faz TUDO (Cria provider, resource e registra)
// Assim evitamos instanciar classes soltas no HTML
function setupRUM(serviceName, collectorUrl) {
    console.log("Iniciando setup RUM para:", serviceName);

    // 1. Exportador
    const exporter = new OTLPTraceExporter({ url: collectorUrl });

    // 2. Resource
    const resource = resourceFromAttributes({
        [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
        [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0'
    });

    // 3. Provider
    const provider = new WebTracerProvider({ resource });

    // 4. Processadores (Aqui estava o erro, agora roda localmente)
    provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
    provider.addSpanProcessor(new SimpleSpanProcessor(new ConsoleSpanExporter()));

    provider.register();

    // 5. Retorna o tracer pronto para uso
    return provider.getTracer('rum-tracer');
}

// Expõe apenas a função de setup
window.otel = { setupRUM };
