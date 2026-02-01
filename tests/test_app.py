# 1. Importa a biblioteca de testes (Pytest)
import pytest

# 2. Importa a sua aplicação Flask do arquivo app.py
# (O Python precisa saber onde está o objeto 'app' que criamos no outro arquivo)
from app.app import app

# ---------------------------------------------------------
# SETUP (PREPARAÇÃO)
# ---------------------------------------------------------
# O @pytest.fixture define uma função de apoio que prepara o terreno antes do teste.
# Pense nisso como "Arrumar a mesa antes do jantar".
@pytest.fixture
def client():
    # 3. app.test_client() cria um "Navegador Fake" (simulado).
    # Ele permite testar rotas sem precisar rodar o servidor de verdade (runserver).
    with app.test_client() as client:
        
        # 4. O 'yield' entrega esse navegador fake para a função de teste usar.
        # O teste roda enquanto o 'with' mantém o navegador aberto.
        yield client

# ---------------------------------------------------------
# O TESTE EM SI
# ---------------------------------------------------------
# O Pytest procura automaticamente funções que começam com "test_"
# O argumento 'client' aqui é a fixture que criamos acima sendo injetada.
def test_home_page(client):
    """
    Objetivo: Verificar se a rota principal '/' carrega sem erros
    e se mostra o conteúdo esperado na tela.
    """

    # 5. AÇÃO: Simula um usuário acessando a URL raiz ('/')
    # O resultado (HTML, código de status, headers) é salvo na variável 'response'.
    response = client.get('/')

    # -----------------------------------------------------
    # VALIDAÇÕES (ASSERTS) - É aqui que o teste passa ou falha
    # -----------------------------------------------------

    # 6. Verifica se o servidor respondeu "OK" (Código 200).
    # Se fosse 404 (Não encontrado) ou 500 (Erro no servidor), o teste pararia aqui.
    assert response.status_code == 200

    # 7. Verifica o CONTEÚDO do HTML.
    # response.data vem em formato de BYTES (por isso o 'b' antes das aspas).
    # Estamos procurando se a frase "Monitoramento Full" existe dentro do HTML retornado.
    # IMPORTANTE: Se você mudar o texto no app.py, tem que mudar aqui também!
    assert b"Monitoramento Full" in response.data
    
    # 8. (Opcional) Podemos verificar se o script do RUM está presente também
    assert b"Iniciando RUM Profissional" in response.data
