// Importamos o BasicTracerProvider (O Pai) direto da base
// Isso resolve o problema de "is not a function"
import { BasicTracerProvider, SimpleSpanProcessor, ConsoleSpanExporter } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

function setupRUM(serviceName, collectorUrl) {
    console.log("Iniciando setup RUM (Modo Compatibilidade) para:", serviceName);

    const exporter = new OTLPTraceExporter({ url: collectorUrl });

    const resource = resourceFromAttributes({
        [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
        [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
        'deployment.environment': 'production'
    });

    // MUDANÇA CRUCIAL: Usamos BasicTracerProvider
    const provider = new BasicTracerProvider({ resource });

    // Debug: Mostra o que é o provider no console para termos certeza
    console.log("Provider criado:", provider);

    // Agora isso TEM que funcionar, pois o método é nativo dessa classe
    provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
    provider.addSpanProcessor(new SimpleSpanProcessor(new ConsoleSpanExporter()));

    provider.register();

    return provider.getTracer('rum-tracer-base');
}

window.otel = { setupRUM };
