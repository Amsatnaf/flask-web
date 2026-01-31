// Importações Corrigidas
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { SimpleSpanProcessor, ConsoleSpanExporter } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { resourceFromAttributes } from '@opentelemetry/resources'; // Essa funciona!
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

// Disponibiliza no window.otel
window.otel = {
    WebTracerProvider,
    SimpleSpanProcessor,
    ConsoleSpanExporter,
    OTLPTraceExporter,
    resourceFromAttributes, // Exportamos a função em vez da classe
    SemanticResourceAttributes
};
