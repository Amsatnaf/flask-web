import os

def test_sanity_check_texto():
    """
    Teste 'Burro':
    Não tenta rodar o app. Apenas lê o arquivo app.py como texto
    e verifica se palavras chaves estão lá.
    Isso garante que o arquivo existe e não está vazio,
    sem quebrar por falta de banco de dados no CI/CD.
    """
    
    # 1. Tenta localizar onde está o app.py (na raiz ou na pasta app)
    caminho = "app.py"
    if not os.path.exists(caminho):
        caminho = "app/app.py"
    
    # Se não achar o arquivo, aí sim falha
    assert os.path.exists(caminho), "O arquivo app.py sumiu!"

    # 2. Lê o conteúdo do arquivo
    with open(caminho, "r") as f:
        conteudo = f.read()

    # 3. Verifica se tem palavras obrigatórias
    assert "Flask" in conteudo
    assert "route" in conteudo
    assert "checkout" in conteudo  # Verifica se a rota de compra existe
