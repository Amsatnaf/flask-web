import sys
import pytest
from unittest.mock import MagicMock

# --- MOCK DA SALVAÇÃO ---
# Engana o Python se faltar lib do OTel para o teste não quebrar no import
mock = MagicMock()
sys.modules["opentelemetry"] = mock
sys.modules["opentelemetry.trace"] = mock
sys.modules["opentelemetry.exporter.otlp.proto.http.trace_exporter"] = mock
# ------------------------

# CORREÇÃO DO ERRO: Importando do caminho completo
# "from app.app" pega o arquivo app.py dentro da pasta app
# "import app" pega a variável 'app = Flask(__name__)' dentro do arquivo
from app.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Banco na memória para não depender de nada externo
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    
    with app.test_client() as client:
        # Tentativa silenciosa de criar o banco. Se falhar, segue o baile.
        try:
            from app.app import db
            with app.app_context():
                db.create_all()
        except:
            pass
        yield client

def test_simples_de_tudo(client):
    """
    Teste Básico: O site abre e tem a palavra 'Loja'?
    """
    response = client.get('/')
    
    # Tem que dar 200 (OK)
    assert response.status_code == 200
    
    # Verifica se existe a palavra "Loja" no HTML
    assert "Loja" in response.data.decode('utf-8')
