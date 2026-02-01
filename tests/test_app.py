import pytest
from app.app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Testa se a pagina inicial responde 200 OK e tem o texto certo"""
    response = client.get('/')

    # Verifica se deu sucesso (200)
    assert response.status_code == 200

    # CORREÇÃO: Agora procuramos o texto que está no novo app.py (CDN)
    assert b"Monitoramento via Internet" in response.data
