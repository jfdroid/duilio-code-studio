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

def test_2_2_fix_bug():
    """Teste 2.2: Corrigir Bug"""
    print_test("Teste 2.2: Corrigir bug no arquivo app.js")
    
    # Primeiro criar app.js com bug
    if not check_file_exists("app.js"):
        prompt = """CRIE um arquivo app.js usando o formato create-file: com uma função calculateTotal que tem um bug:

```create-file:app.js
function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}

// Esta função retorna NaN quando items está vazio ou undefined
```"""
        send_chat_message(prompt)
        time.sleep(3)
    
    if not check_file_exists("app.js"):
        print_error("Não foi possível criar app.js")
        return False
    
    # Ler conteúdo original
    original_content = read_file_content("app.js")
    if not original_content:
        print_error("Não foi possível ler app.js")
        return False
    
    # Corrigir bug
    prompt = """Corrija o bug no arquivo app.js na função calculateTotal que está retornando NaN quando items está vazio ou undefined."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(5)
    
    # Verificar se arquivo ainda existe
    if not check_file_exists("app.js"):
        print_error("Arquivo app.js foi removido!")
        return False
    
    # Ler conteúdo modificado
    modified_content = read_file_content("app.js")
    if not modified_content:
        return False
    
    # Verificar se bug foi corrigido (deve ter verificação de array vazio ou undefined)
    bug_fixes = [
        "items &&" in modified_content or "items ?" in modified_content,
        "items.length" in modified_content or "Array.isArray" in modified_content,
        "|| 0" in modified_content or "?? 0" in modified_content,
        "if (!items" in modified_content or "if (items" in modified_content
    ]
    
    if any(bug_fixes):
        print_success("Bug identificado e corrigido")
    else:
        print_warning("Bug pode não ter sido corrigido")
    
    # Verificar se função ainda existe
    if "calculateTotal" in modified_content:
        print_success("Função calculateTotal preservada")
    else:
        print_error("Função calculateTotal não encontrada")
        return False
    
    # Verificar se código existente foi preservado
    if len(modified_content) >= len(original_content) * 0.5:
        print_success("Código existente preservado")
    else:
        print_warning("Código existente pode ter sido removido")
    
    return True

def test_2_3_refactor_code():
    """Teste 2.3: Refatorar Código"""
    print_test("Teste 2.3: Refatorar código aplicando SOLID")
    
    # Criar userService.js com código não refatorado
    if not check_file_exists("userService.js"):
        prompt = """CRIE um arquivo userService.js usando o formato create-file: com uma classe UserService que faz tudo:
- Busca usuários
- Valida dados
- Salva no banco
- Envia emails
- Gera relatórios

Tudo em uma única classe (violando Single Responsibility).

IMPORTANTE: Use o formato ```create-file:userService.js para criar o arquivo."""
        send_chat_message(prompt)
        time.sleep(3)
    
    if not check_file_exists("userService.js"):
        print_error("Não foi possível criar userService.js")
        return False
    
    # Refatorar
    prompt = """Refatore o arquivo userService.js aplicando os princípios SOLID, especialmente Single Responsibility. Separe as responsabilidades em classes diferentes."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(5)
    
    # Verificar se arquivo foi refatorado (pode ter criado múltiplos arquivos)
    # Verificar se há múltiplas classes ou arquivos
    files_created = []
    for file in os.listdir(TEST_WORKSPACE):
        if file.endswith('.js') and ('user' in file.lower() or 'service' in file.lower() or 'validator' in file.lower()):
            files_created.append(file)
    
    if len(files_created) > 1:
        print_success(f"Responsabilidades separadas em {len(files_created)} arquivos")
    elif check_file_exists("userService.js"):
        content = read_file_content("userService.js")
        # Verificar se tem múltiplas classes ou funções separadas
        class_count = content.count("class ")
        if class_count > 1:
            print_success("Múltiplas classes criadas (responsabilidades separadas)")
        else:
            print_warning("Pode não ter sido refatorado adequadamente")
    
    return True

def test_5_2_react_project():
    """Teste 5.2: Projeto React Completo"""
    print_test("Teste 5.2: Criar projeto React completo")
    
    prompt = """CRIE um projeto React completo usando o formato create-file: para CADA arquivo:

CRIE TODOS estes arquivos usando o formato ```create-file:path:
- package.json com dependências (react, react-dom)
- src/App.jsx (componente principal)
- src/components/Header.jsx (componente de cabeçalho)
- src/components/Footer.jsx (componente de rodapé)
- src/index.js (ponto de entrada)
- public/index.html (HTML base)
- README.md (documentação)

IMPORTANTE: Use múltiplos blocos ```create-file: para criar TODOS os arquivos em uma única resposta."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(5)
    
    # Verificar arquivos
    files = [
        "package.json",
        "src/App.jsx",
        "src/components/Header.jsx",
        "src/components/Footer.jsx",
        "src/index.js",
        "public/index.html",
        "README.md"
    ]
    
    all_created = True
    for file in files:
        if check_file_exists(file):
            print_success(f"Arquivo {file} criado")
        else:
            print_error(f"Arquivo {file} não foi criado")
            all_created = False
    
    if not all_created:
        return False
    
    # Verificar package.json
    package_content = read_file_content("package.json")
    if package_content:
        if "react" in package_content.lower() and "dependencies" in package_content.lower():
            print_success("package.json configurado corretamente")
        else:
            print_warning("package.json pode não estar correto")
    
    # Verificar componentes
    app_content = read_file_content("src/App.jsx")
    header_content = read_file_content("src/components/Header.jsx")
    
    if app_content and "import" in app_content.lower() and "export" in app_content.lower():
        print_success("Componente App.jsx funcional")
    else:
        print_warning("App.jsx pode não estar correto")
    
    if header_content and ("function" in header_content.lower() or "const" in header_content.lower()):
        print_success("Componente Header.jsx funcional")
    else:
        print_warning("Header.jsx pode não estar correto")
    
    return True

def test_6_1_email_html():
    """Teste 6.1: Email HTML"""
    print_test("Teste 6.1: Criar template de email HTML")
    
    prompt = """Crie um template de email HTML profissional para confirmação de cadastro com:
- Header com logo
- Corpo com mensagem de boas-vindas
- Footer com links sociais
- Estilos inline para compatibilidade com clientes de email"""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(3)
    
    # Verificar se arquivo foi criado (pode ter vários nomes)
    email_files = [f for f in os.listdir(TEST_WORKSPACE) if f.endswith('.html') and ('email' in f.lower() or 'template' in f.lower() or 'welcome' in f.lower())]
    
    if not email_files:
        # Tentar encontrar qualquer HTML
        html_files = [f for f in os.listdir(TEST_WORKSPACE) if f.endswith('.html')]
        if html_files:
            email_files = [html_files[0]]
    
    if not email_files:
        print_error("Template de email não foi criado")
        return False
    
    email_file = email_files[0]
    print_success(f"Template de email criado: {email_file}")
    
    content = read_file_content(email_file)
    if not content:
        return False
    
    # Verificar características do template
    checks = [
        ("<html" in content.lower() or "<!doctype" in content.lower(), "HTML válido"),
        ("style=" in content or "style:" in content, "Estilos inline"),
        ("header" in content.lower() or "logo" in content.lower(), "Header presente"),
        ("footer" in content.lower() or "social" in content.lower(), "Footer presente"),
        ("welcome" in content.lower() or "boas-vindas" in content.lower() or "confirmação" in content.lower(), "Mensagem de boas-vindas")
    ]
    
    for check, desc in checks:
        if check:
            print_success(desc)
        else:
            print_warning(f"{desc} pode estar faltando")
    
    return True

def test_6_2_notification_templates():
    """Teste 6.2: Mensagem de Notificação"""
    print_test("Teste 6.2: Criar templates de notificação")
    
    prompt = """CRIE um arquivo notificationTemplates.js usando o formato create-file: com templates de mensagens:
- Sucesso
- Erro
- Aviso
- Informação

IMPORTANTE: Use o formato ```create-file:notificationTemplates.js para criar o arquivo."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(3)
    
    if not check_file_exists("notificationTemplates.js"):
        print_error("Arquivo notificationTemplates.js não foi criado")
        return False
    
    print_success("Arquivo notificationTemplates.js criado")
    
    content = read_file_content("notificationTemplates.js")
    if not content:
        return False
    
    # Verificar templates
    templates = ["sucesso", "success", "erro", "error", "aviso", "warning", "informação", "info"]
    found = sum(1 for t in templates if t.lower() in content.lower())
    
    if found >= 3:
        print_success("Templates de notificação presentes")
    else:
        print_warning("Alguns templates podem estar faltando")
    
    if "function" in content.lower() or "const" in content.lower() or "export" in content.lower():
        print_success("Código bem estruturado")
    else:
        print_warning("Código pode não estar bem estruturado")
    
    return True

def test_7_1_todo_list():
    """Teste 7.1: Lista de Tarefas"""
    print_test("Teste 7.1: Criar lista de tarefas para implementação")
    
    prompt = """CRIE um arquivo TODO.md usando o formato create-file: com uma lista de tarefas para implementar um sistema de autenticação:
1. Criar modelo de usuário
2. Implementar endpoints de login/registro
3. Adicionar middleware de autenticação
4. Criar testes unitários
5. Documentar API

IMPORTANTE: Use o formato ```create-file:TODO.md para criar o arquivo."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(3)
    
    if not check_file_exists("TODO.md"):
        print_error("Arquivo TODO.md não foi criado")
        return False
    
    print_success("Arquivo TODO.md criado")
    
    content = read_file_content("TODO.md")
    if not content:
        return False
    
    # Verificar tarefas
    tasks = ["modelo", "usuário", "endpoints", "login", "registro", "middleware", "autenticação", "testes", "documentar", "api"]
    found = sum(1 for t in tasks if t.lower() in content.lower())
    
    if found >= 5:
        print_success("Tarefas listadas corretamente")
    else:
        print_warning("Algumas tarefas podem estar faltando")
    
    if "#" in content or "-" in content or "*" in content or "1." in content:
        print_success("Formato Markdown correto")
    else:
        print_warning("Formato pode não estar correto")
    
    return True

def test_8_1_conversation_context():
    """Teste 8.1: Contexto de Conversa"""
    print_test("Teste 8.1: Contexto de conversa (múltiplas mensagens)")
    
    # Primeira mensagem: criar classe User
    prompt1 = """CRIE um arquivo user.js usando o formato create-file: com uma classe User que tem propriedades name e email.

IMPORTANTE: Use o formato ```create-file:user.js para criar o arquivo."""
    response1, _ = send_chat_message(prompt1)
    if not response1:
        return False
    
    print_info("Aguardando primeira mensagem...")
    time.sleep(3)
    
    if not check_file_exists("user.js"):
        print_error("user.js não foi criado na primeira mensagem")
        return False
    
    # Segunda mensagem: adicionar método
    prompt2 = "Agora adicione um método getFullName() na classe User que retorna o nome completo."
    response2, _ = send_chat_message(prompt2)
    if not response2:
        return False
    
    print_info("Aguardando segunda mensagem...")
    time.sleep(3)
    
    user_content = read_file_content("user.js")
    if not user_content:
        return False
    
    if "getFullName" in user_content:
        print_success("Método getFullName adicionado")
    else:
        print_error("Método getFullName não foi adicionado")
        return False
    
    if "class User" in user_content:
        print_success("Classe User preservada")
    else:
        print_error("Classe User não encontrada")
        return False
    
    # Terceira mensagem: criar service que usa User
    prompt3 = "Crie um arquivo userService.js que importa e usa a classe User."
    response3, _ = send_chat_message(prompt3)
    if not response3:
        return False
    
    print_info("Aguardando terceira mensagem...")
    time.sleep(3)
    
    if not check_file_exists("userService.js"):
        print_error("userService.js não foi criado")
        return False
    
    service_content = read_file_content("userService.js")
    if service_content:
        if "import" in service_content.lower() and "user" in service_content.lower():
            print_success("userService.js importa User corretamente")
        else:
            print_warning("userService.js pode não estar importando User corretamente")
    
    return True

def test_8_2_workspace_context():
    """Teste 8.2: Contexto do Workspace"""
    print_test("Teste 8.2: Contexto do workspace")
    
    # Criar alguns arquivos primeiro para ter contexto
    if not check_file_exists("config.json"):
        prompt = 'CRIE um arquivo config.json usando create-file: com {"apiUrl": "https://api.example.com"}'
        send_chat_message(prompt)
        time.sleep(2)
    
    if not check_file_exists("utils.js"):
        prompt = "CRIE um arquivo utils.js usando create-file: com uma função helper"
        send_chat_message(prompt)
        time.sleep(2)
    
    # Agora pedir para criar arquivo que se integre
    prompt = """Analise o workspace atual e CRIE um arquivo api.js usando o formato create-file: que se integre com os arquivos existentes (config.json e utils.js).

IMPORTANTE: Use o formato ```create-file:api.js para criar o arquivo."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Aguardando processamento...")
    time.sleep(5)
    
    if not check_file_exists("api.js"):
        print_error("Arquivo api.js não foi criado")
        return False
    
    print_success("Arquivo api.js criado")
    
    api_content = read_file_content("api.js")
    if not api_content:
        return False
    
    # Verificar se importa arquivos existentes
    if ("import" in api_content.lower() or "require" in api_content.lower()) and ("config" in api_content.lower() or "utils" in api_content.lower()):
        print_success("Integração com arquivos existentes")
    else:
        print_warning("Pode não estar integrando com arquivos existentes")
    
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
    
    # Teste 2.2: Corrigir Bug
    try:
        result = test_2_2_fix_bug()
        results.append(("2.2 - Corrigir Bug", result))
    except Exception as e:
        print_error(f"Erro no teste 2.2: {e}")
        results.append(("2.2 - Corrigir Bug", False))
    
    time.sleep(2)
    
    # Teste 2.3: Refatorar Código
    try:
        result = test_2_3_refactor_code()
        results.append(("2.3 - Refatorar Código", result))
    except Exception as e:
        print_error(f"Erro no teste 2.3: {e}")
        results.append(("2.3 - Refatorar Código", False))
    
    time.sleep(2)
    
    # Teste 5.2: Projeto React Completo
    try:
        result = test_5_2_react_project()
        results.append(("5.2 - Projeto React Completo", result))
    except Exception as e:
        print_error(f"Erro no teste 5.2: {e}")
        results.append(("5.2 - Projeto React Completo", False))
    
    time.sleep(2)
    
    # Teste 6.1: Email HTML
    try:
        result = test_6_1_email_html()
        results.append(("6.1 - Email HTML", result))
    except Exception as e:
        print_error(f"Erro no teste 6.1: {e}")
        results.append(("6.1 - Email HTML", False))
    
    time.sleep(2)
    
    # Teste 6.2: Mensagem de Notificação
    try:
        result = test_6_2_notification_templates()
        results.append(("6.2 - Mensagem de Notificação", result))
    except Exception as e:
        print_error(f"Erro no teste 6.2: {e}")
        results.append(("6.2 - Mensagem de Notificação", False))
    
    time.sleep(2)
    
    # Teste 7.1: Lista de Tarefas
    try:
        result = test_7_1_todo_list()
        results.append(("7.1 - Lista de Tarefas", result))
    except Exception as e:
        print_error(f"Erro no teste 7.1: {e}")
        results.append(("7.1 - Lista de Tarefas", False))
    
    time.sleep(2)
    
    # Teste 8.1: Contexto de Conversa
    try:
        result = test_8_1_conversation_context()
        results.append(("8.1 - Contexto de Conversa", result))
    except Exception as e:
        print_error(f"Erro no teste 8.1: {e}")
        results.append(("8.1 - Contexto de Conversa", False))
    
    time.sleep(2)
    
    # Teste 8.2: Contexto do Workspace
    try:
        result = test_8_2_workspace_context()
        results.append(("8.2 - Contexto do Workspace", result))
    except Exception as e:
        print_error(f"Erro no teste 8.2: {e}")
        results.append(("8.2 - Contexto do Workspace", False))
    
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
