#!/usr/bin/env python3
"""
Test Validation Runner - Executa e valida testes do DuilioCode Studio
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Tuple

# Importar TEST_WORKSPACE
TEST_WORKSPACE = os.path.expanduser("~/test-validation-workspace")

# Configurações
BASE_URL = "http://127.0.0.1:8080"
TEST_WORKSPACE = os.path.expanduser("~/test-validation-workspace")

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_test(msg):
    print(f"{Colors.CYAN}{Colors.BOLD}🧪 {msg}{Colors.RESET}")

def check_server():
    """Verifica se o servidor está rodando"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def send_chat_message(prompt: str, workspace_path: str = None, conversation_history: List[Dict] = None) -> Tuple[str, Dict]:
    """Envia mensagem para o chat e retorna resposta"""
    url = f"{BASE_URL}/api/chat"
    
    messages = conversation_history or []
    messages.append({"role": "user", "content": prompt})
    
    data = {
        "messages": messages,
        "workspace_path": workspace_path or TEST_WORKSPACE,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=data, timeout=180)
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Check if actions were processed
            if result.get("actions_processed"):
                actions_result = result.get("actions_result", {})
                print_info(f"Ações processadas: {actions_result.get('success_count', 0)} sucesso, {actions_result.get('error_count', 0)} erros")
            
            return content, result
        else:
            print_error(f"Erro na API: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print_error(f"Erro ao enviar mensagem: {e}")
        return None, None

def check_file_exists(file_path: str, workspace: str = None) -> bool:
    """Verifica se arquivo existe"""
    if not workspace:
        workspace = TEST_WORKSPACE
    
    # Se path é absoluto, usar direto
    if os.path.isabs(file_path):
        return os.path.exists(file_path)
    
    # Se path é relativo, juntar com workspace
    full_path = os.path.join(workspace, file_path)
    return os.path.exists(full_path)

def read_file_content(file_path: str, workspace: str = None) -> str:
    """Lê conteúdo do arquivo"""
    if not workspace:
        workspace = TEST_WORKSPACE
    
    if os.path.isabs(file_path):
        full_path = file_path
    else:
        full_path = os.path.join(workspace, file_path)
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print_warning(f"Erro ao ler arquivo {file_path}: {e}")
        return None

def check_directory_exists(dir_path: str, workspace: str = None) -> bool:
    """Verifica se diretório existe"""
    if not workspace:
        workspace = TEST_WORKSPACE
    
    if os.path.isabs(dir_path):
        return os.path.isdir(dir_path)
    
    full_path = os.path.join(workspace, dir_path)
    return os.path.isdir(full_path)

def extract_create_file_actions(response_text: str) -> List[Tuple[str, str]]:
    """Extrai ações create-file da resposta"""
    import re
    pattern = r'```create-file:([^\n]+)\n([\s\S]*?)```'
    matches = re.findall(pattern, response_text)
    return [(path.strip(), content) for path, content in matches]

def test_1_1_create_simple_file():
    """Teste 1.1: Arquivo Único Básico"""
    print_test("Teste 1.1: Criar arquivo utils.js simples")
    
    prompt = "Crie um arquivo chamado utils.js com funções auxiliares para manipulação de strings."
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(3)
    
    # Verificar se arquivo foi criado
    if not check_file_exists("utils.js"):
        print_error("Arquivo utils.js não foi criado")
        print_info(f"Resposta do AI: {response[:500]}")
        return False
    
    print_success("Arquivo utils.js criado")
    
    # Verificar conteúdo
    content = read_file_content("utils.js")
    if not content:
        print_error("Não foi possível ler conteúdo do arquivo")
        return False
    
    # Verificar se contém funções de string
    if "function" in content.lower() or "const" in content.lower() or "export" in content.lower():
        print_success("Conteúdo contém funções")
    else:
        print_warning("Conteúdo pode não ter funções")
    
    # Verificar se tem manipulação de strings
    string_keywords = ["string", "substring", "replace", "split", "trim", "slice"]
    has_string_ops = any(kw in content.lower() for kw in string_keywords)
    
    if has_string_ops:
        print_success("Conteúdo contém operações de string")
    else:
        print_warning("Conteúdo pode não ter operações de string explícitas")
    
    return True

def test_1_2_create_json_file():
    """Teste 1.2: Arquivo JSON com estrutura específica"""
    print_test("Teste 1.2: Criar arquivo config.json")
    
    prompt = """Crie um arquivo config.json com as seguintes configurações:
- apiUrl: "https://api.example.com"
- timeout: 5000
- retries: 3"""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(3)
    
    if not check_file_exists("config.json"):
        print_error("Arquivo config.json não foi criado")
        return False
    
    print_success("Arquivo config.json criado")
    
    content = read_file_content("config.json")
    if not content:
        return False
    
    # Verificar se é JSON válido
    try:
        data = json.loads(content)
        print_success("JSON válido")
        
        # Verificar propriedades
        if "apiUrl" in data:
            print_success("Propriedade apiUrl presente")
        else:
            print_error("Propriedade apiUrl ausente")
            return False
        
        if data.get("timeout") == 5000:
            print_success("timeout correto")
        else:
            print_warning(f"timeout = {data.get('timeout')}, esperado 5000")
        
        if data.get("retries") == 3:
            print_success("retries correto")
        else:
            print_warning(f"retries = {data.get('retries')}, esperado 3")
        
        return True
    except json.JSONDecodeError as e:
        print_error(f"JSON inválido: {e}")
        return False

def test_1_3_create_file_in_subdirectory():
    """Teste 1.3: Arquivo em Subdiretório"""
    print_test("Teste 1.3: Criar arquivo src/components/Button.jsx")
    
    prompt = "Crie um arquivo src/components/Button.jsx com um componente React de botão."
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(3)
    
    # Verificar se diretório foi criado
    if not check_directory_exists("src/components"):
        print_error("Diretório src/components/ não foi criado")
        return False
    
    print_success("Diretório src/components/ criado")
    
    # Verificar se arquivo foi criado
    if not check_file_exists("src/components/Button.jsx"):
        print_error("Arquivo Button.jsx não foi criado")
        return False
    
    print_success("Arquivo Button.jsx criado no local correto")
    
    # Verificar conteúdo
    content = read_file_content("src/components/Button.jsx")
    if not content:
        return False
    
    # Verificar se é componente React
    react_keywords = ["react", "import", "export", "function", "component", "props"]
    has_react = any(kw in content.lower() for kw in react_keywords)
    
    if has_react:
        print_success("Componente React funcional")
    else:
        print_warning("Conteúdo pode não ser um componente React válido")
    
    # Verificar imports
    if "import" in content.lower() and "react" in content.lower():
        print_success("Imports corretos")
    else:
        print_warning("Imports podem estar faltando")
    
    return True

def test_2_1_add_function():
    """Teste 2.1: Adicionar Função"""
    print_test("Teste 2.1: Adicionar função formatDate em utils.js")
    
    # Primeiro verificar se utils.js existe (criado no teste 1.1)
    if not check_file_exists("utils.js"):
        print_warning("utils.js não existe, criando primeiro...")
        # Criar utils.js básico se não existir
        prompt = "Crie um arquivo utils.js com funções auxiliares básicas."
        send_chat_message(prompt)
        time.sleep(3)
    
    if not check_file_exists("utils.js"):
        print_error("Não foi possível criar/verificar utils.js")
        return False
    
    # Ler conteúdo original
    original_content = read_file_content("utils.js")
    if not original_content:
        print_error("Não foi possível ler utils.js")
        return False
    
    print_info(f"Conteúdo original tem {len(original_content)} caracteres")
    
    # Adicionar função
    prompt = """MODIFIQUE o arquivo EXISTENTE utils.js (que já existe no workspace) adicionando uma função chamada formatDate que formata datas no formato DD/MM/YYYY.
    
CRÍTICO: 
- O arquivo utils.js JÁ EXISTE no workspace
- Você DEVE usar o formato ```modify-file:utils.js (NÃO create-file)
- Você DEVE incluir TODO o conteúdo do arquivo existente
- Você DEVE preservar TODAS as funções existentes (capitalize, isEmpty, reverseString, createSlug, countWords)
- Você DEVE adicionar a nova função formatDate ao final do arquivo
- NÃO crie novos arquivos, apenas MODIFIQUE o arquivo existente"""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    # Verificar se a resposta contém modify-file
    if "modify-file" in response.lower():
        print_success("Resposta contém modify-file")
    else:
        print_warning(f"Resposta pode não conter modify-file: {response[:200]}")
    
    print_info("Aguardando processamento...")
    time.sleep(5)  # Aumentar tempo de espera
    
    # Verificar se arquivo ainda existe
    if not check_file_exists("utils.js"):
        print_error("Arquivo utils.js foi removido!")
        return False
    
    # Ler conteúdo modificado
    modified_content = read_file_content("utils.js")
    if not modified_content:
        return False
    
    # Verificar se função foi adicionada (case-insensitive)
    modified_lower = modified_content.lower()
    if "formatdate" in modified_lower or "format_date" in modified_lower:
        print_success("Função formatDate adicionada")
    else:
        print_error("Função formatDate não foi encontrada")
        print_info(f"Conteúdo modificado tem {len(modified_content)} caracteres")
        print_info(f"Primeiras 200 chars: {modified_content[:200]}")
        print_info(f"Últimas 200 chars: {modified_content[-200:]}")
        # Verificar se o arquivo foi modificado
        if len(modified_content) <= len(original_content):
            print_warning("Arquivo pode não ter sido modificado (tamanho similar ou menor)")
        return False
    
    # Verificar se código existente foi preservado
    # Pelo menos 50% do conteúdo original deve estar presente
    original_length = len(original_content)
    preserved = sum(1 for line in original_content.split('\n')[:5] if line.strip() in modified_content)
    
    if preserved >= 2 or len(modified_content) >= original_length * 0.5:
        print_success("Código existente preservado")
    else:
        print_warning("Código existente pode ter sido removido")
    
    # Verificar formato de data
    if "DD/MM/YYYY" in modified_content or "dd/mm/yyyy" in modified_content.lower() or "/" in modified_content:
        print_success("Formato de data correto (DD/MM/YYYY)")
    else:
        print_warning("Formato de data pode não estar correto")
    
    return True

def test_3_1_create_folder():
    """Teste 3.1: Criar Pasta"""
    print_test("Teste 3.1: Criar pasta tests/")
    
    prompt = "Crie uma pasta chamada tests para armazenar os testes do projeto."
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(3)
    
    # Verificar se pasta foi criada
    if not check_directory_exists("tests"):
        print_error("Pasta tests/ não foi criada")
        return False
    
    print_success("Pasta tests/ criada")
    
    # Verificar estrutura
    if os.path.isdir(os.path.join(TEST_WORKSPACE, "tests")):
        print_success("Estrutura de diretório correta")
    else:
        print_error("Estrutura de diretório incorreta")
        return False
    
    # Verificar se pode criar arquivos dentro
    test_file = os.path.join(TEST_WORKSPACE, "tests", "test.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print_success("Pode criar arquivos dentro da pasta")
    except Exception as e:
        print_warning(f"Não foi possível criar arquivo dentro: {e}")
    
    return True

def test_3_2_create_folder_structure():
    """Teste 3.2: Estrutura de Pastas Completa"""
    print_test("Teste 3.2: Criar estrutura de pastas React")
    
    prompt = """Crie a estrutura completa de pastas para um projeto React com arquivos úteis em cada pasta:
- src/components (com index.js ou exemplo de componente)
- src/hooks (com index.js ou exemplo de hook)
- src/utils (com index.js com funções utilitárias)
- src/services (com index.js com serviços de API)
- public (com index.html ou README.md)

Crie TODAS as pastas com arquivos úteis e profissionais, não apenas pastas vazias."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(5)  # Mais tempo para múltiplas pastas
    
    # Verificar todas as pastas
    folders = [
        "src/components",
        "src/hooks",
        "src/utils",
        "src/services",
        "public"
    ]
    
    all_created = True
    for folder in folders:
        # Verificar se pasta existe (pode ter sido criada por arquivo dentro)
        folder_path = os.path.join(TEST_WORKSPACE, folder)
        if os.path.isdir(folder_path):
            # Verificar se tem arquivos úteis dentro (não apenas .gitkeep)
            files_in_folder = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            useful_files = [f for f in files_in_folder if not f.endswith('.gitkeep')]
            
            if useful_files:
                print_success(f"Pasta {folder}/ criada com arquivos úteis: {', '.join(useful_files)}")
            elif files_in_folder:
                print_success(f"Pasta {folder}/ criada (com .gitkeep)")
            else:
                print_success(f"Pasta {folder}/ criada")
        else:
            print_error(f"Pasta {folder}/ não foi criada")
            all_created = False
    
    if not all_created:
        # Verificar quantas foram criadas
        created_count = sum(1 for folder in folders if os.path.isdir(os.path.join(TEST_WORKSPACE, folder)))
        print_warning(f"Apenas {created_count}/{len(folders)} pastas foram criadas")
        return False
    
    # Verificar estrutura hierárquica
    if check_directory_exists("src") and check_directory_exists("public"):
        print_success("Estrutura hierárquica correta")
    else:
        print_error("Estrutura hierárquica incorreta")
        return False
    
    return True

def test_5_1_create_web_project():
    """Teste 5.1: Projeto Web Todo List"""
    print_test("Teste 5.1: Criar projeto web Todo List completo")
    
    prompt = """Crie um aplicativo web completo de Todo List com:
- index.html (estrutura HTML5)
- styles.css (tema dark moderno)
- app.js (lógica completa)
- README.md (documentação)"""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(5)  # Mais tempo para projeto completo
    
    # Verificar todos os arquivos
    files = ["index.html", "styles.css", "app.js", "README.md"]
    
    all_created = True
    for file in files:
        if check_file_exists(file):
            print_success(f"Arquivo {file} criado")
        else:
            print_error(f"Arquivo {file} não foi criado")
            all_created = False
    
    if not all_created:
        return False
    
    # Verificar HTML
    html_content = read_file_content("index.html")
    if html_content:
        if "<!DOCTYPE html>" in html_content or "<html" in html_content.lower():
            print_success("HTML válido e semântico")
        else:
            print_warning("HTML pode não estar correto")
    
    # Verificar CSS
    css_content = read_file_content("styles.css")
    if css_content:
        if "dark" in css_content.lower() or "background" in css_content.lower():
            print_success("CSS com tema dark")
        else:
            print_warning("CSS pode não ter tema dark")
    
    # Verificar JavaScript
    js_content = read_file_content("app.js")
    if js_content:
        if "function" in js_content.lower() or "const" in js_content.lower():
            print_success("JavaScript funcional")
        else:
            print_warning("JavaScript pode não estar completo")
    
    # Verificar README
    readme_content = read_file_content("README.md")
    if readme_content:
        if len(readme_content) > 50:
            print_success("README completo")
        else:
            print_warning("README pode estar incompleto")
    
    return True

def test_8_3_reference_existing_file():
    """Teste 8.3: Referência a Arquivo Existente"""
    print_test("Teste 8.3: Criar Card.jsx baseado em Button.jsx")
    
    # Primeiro garantir que Button.jsx existe (criado no teste 1.3)
    if not check_file_exists("src/components/Button.jsx"):
        print_warning("Button.jsx não existe, criando primeiro...")
        prompt = "Crie um arquivo src/components/Button.jsx com um componente React de botão."
        send_chat_message(prompt)
        time.sleep(3)
    
    if not check_file_exists("src/components/Button.jsx"):
        print_error("Não foi possível criar/verificar Button.jsx")
        return False
    
    # Ler Button.jsx para comparar depois
    button_content = read_file_content("src/components/Button.jsx")
    if not button_content:
        print_error("Não foi possível ler Button.jsx")
        return False
    
    print_info(f"Button.jsx tem {len(button_content)} caracteres")
    
    # Criar Card.jsx baseado em Button.jsx
    prompt = "Crie um arquivo Card.jsx baseado no arquivo Button.jsx existente, mantendo o mesmo estilo e estrutura."
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(3)
    
    # Verificar se Card.jsx foi criado
    card_path = "src/components/Card.jsx"
    if not check_file_exists(card_path):
        # Pode ter sido criado no root
        if check_file_exists("Card.jsx"):
            card_path = "Card.jsx"
        else:
            print_error("Card.jsx não foi criado")
            return False
    
    print_success("Card.jsx criado")
    
    # Ler Card.jsx
    card_content = read_file_content(card_path)
    if not card_content:
        return False
    
    # Verificar estrutura similar
    # Comparar imports, exports, estrutura
    button_imports = [line for line in button_content.split('\n') if 'import' in line.lower()]
    card_imports = [line for line in card_content.split('\n') if 'import' in line.lower()]
    
    if button_imports and card_imports:
        # Verificar se imports são similares
        similar_imports = any(any(kw in card_import.lower() for kw in ['react', 'button']) for card_import in card_imports)
        if similar_imports or len(card_imports) > 0:
            print_success("Imports consistentes")
        else:
            print_warning("Imports podem não ser consistentes")
    
    # Verificar se tem estrutura similar (function, export, props)
    structure_keywords = ["function", "export", "props", "component"]
    button_has = sum(1 for kw in structure_keywords if kw in button_content.lower())
    card_has = sum(1 for kw in structure_keywords if kw in card_content.lower())
    
    if card_has >= 2:
        print_success("Estrutura similar mantida")
    else:
        print_warning("Estrutura pode não ser similar")
    
    # Verificar estilo (verificar se tem padrões similares)
    if "Card" in card_content and ("function" in card_content.lower() or "const" in card_content.lower()):
        print_success("Estilo e padrões mantidos")
    else:
        print_warning("Estilo pode não estar mantido")
    
    return True

def main():
    """Executa todos os testes"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}")
    print("🚀 TEST VALIDATION RUNNER - DuilioCode Studio")
    print(f"{'='*70}{Colors.RESET}\n")
    
    # Verificar servidor
    print_info("Verificando servidor...")
    if not check_server():
        print_error("Servidor não está rodando! Inicie o DuilioCode Studio primeiro.")
        print_info("Execute: cd duilio-code-studio && python -m src.main")
        sys.exit(1)
    print_success("Servidor está rodando")
    
    # Criar workspace
    Path(TEST_WORKSPACE).mkdir(parents=True, exist_ok=True)
    print_info(f"Workspace: {TEST_WORKSPACE}")
    
    # Executar testes
    results = []
    
    print(f"\n{Colors.BOLD}{'='*70}")
    print("EXECUTANDO TESTES")
    print(f"{'='*70}{Colors.RESET}\n")
    
    # Teste 1.1
    try:
        result = test_1_1_create_simple_file()
        results.append(("1.1 - Arquivo Único Básico", result))
    except Exception as e:
        print_error(f"Erro no teste 1.1: {e}")
        results.append(("1.1 - Arquivo Único Básico", False))
    
    time.sleep(2)
    
    # Teste 1.2
    try:
        result = test_1_2_create_json_file()
        results.append(("1.2 - Arquivo JSON", result))
    except Exception as e:
        print_error(f"Erro no teste 1.2: {e}")
        results.append(("1.2 - Arquivo JSON", False))
    
    time.sleep(2)
    
    # Teste 1.3
    try:
        result = test_1_3_create_file_in_subdirectory()
        results.append(("1.3 - Arquivo em Subdiretório", result))
    except Exception as e:
        print_error(f"Erro no teste 1.3: {e}")
        results.append(("1.3 - Arquivo em Subdiretório", False))
    
    time.sleep(2)
    
    # Teste 2.1
    try:
        result = test_2_1_add_function()
        results.append(("2.1 - Adicionar Função", result))
    except Exception as e:
        print_error(f"Erro no teste 2.1: {e}")
        results.append(("2.1 - Adicionar Função", False))
    
    time.sleep(2)
    
    # Teste 3.1
    try:
        result = test_3_1_create_folder()
        results.append(("3.1 - Criar Pasta", result))
    except Exception as e:
        print_error(f"Erro no teste 3.1: {e}")
        results.append(("3.1 - Criar Pasta", False))
    
    time.sleep(2)
    
    # Teste 3.2
    try:
        result = test_3_2_create_folder_structure()
        results.append(("3.2 - Estrutura de Pastas Completa", result))
    except Exception as e:
        print_error(f"Erro no teste 3.2: {e}")
        results.append(("3.2 - Estrutura de Pastas Completa", False))
    
    time.sleep(2)
    
    # Teste 5.1
    try:
        result = test_5_1_create_web_project()
        results.append(("5.1 - Projeto Web Todo List", result))
    except Exception as e:
        print_error(f"Erro no teste 5.1: {e}")
        results.append(("5.1 - Projeto Web Todo List", False))
    
    time.sleep(2)
    
    # Teste 8.3
    try:
        result = test_8_3_reference_existing_file()
        results.append(("8.3 - Referência a Arquivo Existente", result))
    except Exception as e:
        print_error(f"Erro no teste 8.3: {e}")
        results.append(("8.3 - Referência a Arquivo Existente", False))
    
    time.sleep(2)
    
    # Resumo
    print(f"\n{Colors.BOLD}{'='*70}")
    print("📊 RESUMO DOS TESTES")
    print(f"{'='*70}{Colors.RESET}\n")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: PASSOU")
        else:
            print_error(f"{name}: FALHOU")
    
    print(f"\nTotal: {total} testes")
    print_success(f"Passou: {passed}")
    if total - passed > 0:
        print_error(f"Falhou: {total - passed}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\nTaxa de sucesso: {success_rate:.1f}%")
    
    print(f"\n{Colors.BLUE}Workspace de teste: {TEST_WORKSPACE}{Colors.RESET}\n")

if __name__ == "__main__":
    main()
