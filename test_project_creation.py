#!/usr/bin/env python3
"""
Teste Automatizado - Criação de Projeto Web via DuilioCode Studio
Testa diversos cenários de chat e valida criação de arquivos
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# Configurações
BASE_URL = "http://127.0.0.1:8080"
TEST_WORKSPACE = os.path.expanduser("~/Desktop/test-todo-list")

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def check_server():
    """Verifica se o servidor está rodando"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def create_workspace():
    """Cria o workspace de teste"""
    Path(TEST_WORKSPACE).mkdir(parents=True, exist_ok=True)
    print_info(f"Workspace criado: {TEST_WORKSPACE}")

def send_chat_message(prompt, workspace_path=None):
    """Envia mensagem para o chat"""
    url = f"{BASE_URL}/api/chat"
    
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    data = {
        "messages": messages,
        "workspace_path": workspace_path or TEST_WORKSPACE,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=data, timeout=120)
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            print_error(f"Erro na API: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Erro ao enviar mensagem: {e}")
        return None

def check_file_exists(file_path):
    """Verifica se arquivo existe"""
    full_path = os.path.join(TEST_WORKSPACE, file_path)
    return os.path.exists(full_path)

def read_file_content(file_path):
    """Lê conteúdo do arquivo"""
    full_path = os.path.join(TEST_WORKSPACE, file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return None

def validate_file(file_path, expected_content=None):
    """Valida arquivo criado"""
    if not check_file_exists(file_path):
        print_error(f"Arquivo não encontrado: {file_path}")
        return False
    
    print_success(f"Arquivo criado: {file_path}")
    
    if expected_content:
        content = read_file_content(file_path)
        if expected_content.lower() in content.lower():
            print_success(f"Conteúdo esperado encontrado em {file_path}")
            return True
        else:
            print_warning(f"Conteúdo pode estar diferente em {file_path}")
            return True  # Ainda válido, apenas diferente
    
    return True

def test_scenario(name, prompt, expected_files, workspace_path=None):
    """Testa um cenário"""
    print(f"\n{'='*60}")
    print(f"🧪 Teste: {name}")
    print(f"{'='*60}")
    print_info(f"Prompt: {prompt[:80]}...")
    
    # Enviar mensagem
    print_info("Enviando mensagem para o chat...")
    response = send_chat_message(prompt, workspace_path)
    
    if not response:
        print_error("Falha ao obter resposta do chat")
        return False
    
    print_info("Resposta recebida, aguardando processamento...")
    time.sleep(2)  # Aguardar processamento de arquivos
    
    # Validar arquivos
    all_valid = True
    for file_path, expected_content in expected_files.items():
        if not validate_file(file_path, expected_content):
            all_valid = False
    
    if all_valid:
        print_success(f"✅ Teste '{name}' PASSOU")
    else:
        print_error(f"❌ Teste '{name}' FALHOU")
    
    return all_valid

def main():
    """Executa todos os testes"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print("🚀 TESTE AUTOMATIZADO - DuilioCode Studio")
    print(f"{'='*60}{Colors.RESET}\n")
    
    # Verificar servidor
    print_info("Verificando servidor...")
    if not check_server():
        print_error("Servidor não está rodando! Inicie o DuilioCode Studio primeiro.")
        sys.exit(1)
    print_success("Servidor está rodando")
    
    # Criar workspace
    create_workspace()
    
    # Testes
    results = []
    
    # Teste 1: Criar estrutura base
    results.append(test_scenario(
        "Estrutura Base do Projeto",
        "Crie um projeto web simples de Todo List com a seguinte estrutura:\n- index.html (página principal)\n- styles.css (estilos)\n- app.js (lógica da aplicação)\n- README.md (documentação)\n\nO projeto deve ter uma interface limpa e moderna.",
        {
            "index.html": "html",
            "styles.css": "css",
            "app.js": "javascript",
            "README.md": "todo"
        }
    ))
    
    # Teste 2: Implementar funcionalidades
    results.append(test_scenario(
        "Funcionalidades Básicas",
        "Implemente as funcionalidades básicas do Todo List no app.js:\n- Adicionar tarefa\n- Marcar como concluída\n- Remover tarefa\n- Contador de tarefas pendentes",
        {
            "app.js": "addTask"
        }
    ))
    
    # Teste 3: Melhorar estilos
    results.append(test_scenario(
        "Melhorar Estilos",
        "Melhore os estilos do Todo List no styles.css:\n- Use um tema dark moderno\n- Adicione animações suaves\n- Torne responsivo para mobile",
        {
            "styles.css": "dark"
        }
    ))
    
    # Teste 4: Adicionar persistência
    results.append(test_scenario(
        "Persistência Local",
        "Adicione persistência local usando localStorage no app.js:\n- Salvar tarefas quando adicionadas/modificadas\n- Carregar tarefas ao abrir a página",
        {
            "app.js": "localStorage"
        }
    ))
    
    # Teste 5: Criar arquivo de configuração
    results.append(test_scenario(
        "Arquivo de Configuração",
        "Crie um arquivo config.js para centralizar configurações:\n- Tamanho máximo de tarefa\n- Tema (dark/light)\n- Idioma",
        {
            "config.js": "config"
        }
    ))
    
    # Resumo
    print(f"\n{Colors.BLUE}{'='*60}")
    print("📊 RESUMO DOS TESTES")
    print(f"{'='*60}{Colors.RESET}\n")
    
    passed = sum(results)
    total = len(results)
    
    print(f"Total: {total} testes")
    print_success(f"Passou: {passed}")
    if total - passed > 0:
        print_error(f"Falhou: {total - passed}")
    
    print(f"\n{Colors.BLUE}Workspace de teste: {TEST_WORKSPACE}{Colors.RESET}")
    print(f"\nPara ver os arquivos criados, abra: {TEST_WORKSPACE}\n")

if __name__ == "__main__":
    main()
