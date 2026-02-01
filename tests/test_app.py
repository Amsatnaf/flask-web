# 1. Importa o framework 'pytest', que é a ferramenta que vai rodar os testes
import pytest

# 2. Importa a variável 'app' (sua aplicação Flask) de dentro da pasta/arquivo 'app/app.py'
from app.app import app

# ---------------------------------------------------------------------------
# FIXTURE (PREPARAÇÃO)
# ---------------------------------------------------------------------------
# O @pytest.fixture indica que esta função prepara um recurso para ser usado nos testes.
@pytest.fixture
def client():
    # 3. Cria um contexto com o 'test_client()'. 
    # Isso simula um navegador web na memória, sem precisar abrir porta de internet.
    with app.test_client() as client:
        
        # 4. O comando 'yield' entrega esse cliente simulado para a função de teste.
        # O teste roda, e quando acabar, o sistema limpa a memória automaticamente.
        yield client

# ---------------------------------------------------------------------------
# O TESTE (EXECUÇÃO)
# ---------------------------------------------------------------------------
# Define a função de teste. O pytest reconhece ela porque começa com "test_".
# Ela recebe o 'client' que criamos ali em cima.
def test_home_page(client):
    """
    Testa se a página carrega e se a versão baseada em Span Events está ativa.
    """
    # 1. Faz a requisição
    response = client.get('/')

    # 2. Verifica se o site está NO AR
    assert response.status_code == 200

    # 3. Verifica se o TÍTULO VISUAL mudou
    # No novo app.py colocamos: <h1>RUM via Span Events 🎯</h1>
    assert b"RUM via Span Events" in response.data

    # 4. VERIFICAÇÃO TÉCNICA (O Pulo do Gato):
    # O teste antigo procurava por 'traceFlags'.
    # O novo deve procurar pela função 'addEvent', que prova que mudamos a lógica.
    assert b"window.rootSpan.addEvent" in response.data

    # 5. Verifica se NÃO estamos mais importando a lib de logs (limpeza de código)
    # Garante que você removeu o peso morto do código antigo
    assert b"OTLPLogExporter" not in response.data
