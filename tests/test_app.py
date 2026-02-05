import pytest
import json
from app import app as flask_app # Ajuste o import conforme sua pasta

@pytest.fixture
def client():
    # Configura modo de teste para o Flask
    flask_app.config['TESTING'] = True
    
    # Dica Ninja: Desabilitamos o Rastreamento do SQLAlchemy nos testes 
    # para não poluir logs ou tentar conectar sem necessidade critica
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:" # Banco Fake na memória RAM
    
    with flask_app.test_client() as client:
        with flask_app.app_context():
            # Cria banco em memória para o teste funcionar liso
            from app import db
            db.create_all()
            yield client

def test_frontend_rum_injection(client):
    """
    Valida se o HTML contém o script de monitoramento (RUM).
    """
    response = client.get('/')
    html = response.data.decode('utf-8')

    assert response.status_code == 200
    assert "<!DOCTYPE html>" in html
    
    # Valida configs do OpenTelemetry
    assert "@opentelemetry/sdk-trace-web" in html
    assert "otel-collector.129-213-28-76.sslip.io" in html
    assert "flask-frontend-rum" in html

def test_backend_checkout_flow(client):
    """
    Valida se a rota POST /checkout responde JSON corretamente.
    """
    # Simula o navegador enviando um POST
    response = client.post('/checkout')
    
    # O status deve ser 200 (Sucesso) ou 500 (Erro controlado)
    # Como estamos usando SQLite em memória, deve dar 200 SUCESSO!
    assert response.status_code == 200
    
    data = response.get_json()
    assert "status" in data
    
    # Se o banco em memória funcionou, deve vir "compra_sucesso"
    if response.status_code == 200:
        assert data['status'] == "compra_sucesso"
        assert "id" in data
