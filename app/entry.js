import { BasicTracerProvider, SimpleSpanProcessor, ConsoleSpanExporter } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

function setupRUM(serviceName, collectorUrl) {
    console.log("Iniciando RUM (Modo MacGyver) para:", serviceName);

    const exporter = new OTLPTraceExporter({ url: collectorUrl });
    const consoleExporter = new ConsoleSpanExporter();

    const resource = resourceFromAttributes({
        [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
        [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0'
    });

    const provider = new BasicTracerProvider({ resource });

    // --- O PULO DO GATO ---
    // Tenta adicionar do jeito normal. Se der erro, usa a propriedade interna que vimos no log.
    function safeAddProcessor(proc) {
        if (typeof provider.addSpanProcessor === 'function') {
            provider.addSpanProcessor(proc);
        } else if (provider._activeSpanProcessor) {
            console.warn("⚠️ Usando acesso direto ao _activeSpanProcessor");
            provider._activeSpanProcessor.addSpanProcessor(proc);
        } else {
            console.error("❌ Não foi possível adicionar o processador!");
        }
    }

    safeAddProcessor(new SimpleSpanProcessor(exporter));
    safeAddProcessor(new SimpleSpanProcessor(consoleExporter));

    provider.register();

    return provider.getTracer('rum-macgyver');
}

window.otel = { setupRUM };
