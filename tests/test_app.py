import pytest
from app.app import app # Importa seu app que está na pasta app/app.py

@pytest.fixture
def client():
    # Cria um navegador falso para testar
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Testa se a pagina inicial responde 200 OK e tem o texto certo"""
    response = client.get('/')

    # Verifica se deu sucesso (200)
    assert response.status_code == 200

    # Verifica se o texto "Rancher Fleet" está na resposta
    # O 'b' antes das aspas significa bytes (como a internet trafega dados)
    assert b"Rancher Fleet" in response.data
