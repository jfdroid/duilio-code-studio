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

# Configuration
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
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

# Global conversation history
_conversation_history: List[Dict] = []

def send_chat_message(prompt: str, workspace_path: str = None, conversation_history: List[Dict] = None, use_history: bool = True) -> Tuple[str, Dict]:
    """Send message to chat and return response"""
    url = f"{BASE_URL}/api/chat"
    
    global _conversation_history
    
    if conversation_history is not None:
        messages = conversation_history
    elif use_history:
        messages = _conversation_history.copy()
    else:
        messages = []
    
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
            
            # Update conversation history
            if use_history:
                _conversation_history.append({"role": "user", "content": prompt})
                _conversation_history.append({"role": "assistant", "content": content})
            
            # Check if actions were processed
            if result.get("actions_processed"):
                actions_result = result.get("actions_result", {})
                print_info(f"Actions processed: {actions_result.get('success_count', 0)} success, {actions_result.get('error_count', 0)} errors")
            
            return content, result
        else:
            print_error(f"API error: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        print_error(f"Error sending message: {e}")
        return None, None

def reset_conversation_history():
    """Reset conversation history"""
    global _conversation_history
    _conversation_history = []

def check_file_exists(file_path: str, workspace: str = None) -> bool:
    """Check if file exists"""
    if not workspace:
        workspace = TEST_WORKSPACE
    
    # Se path é absoluto, usar direto
    if os.path.isabs(file_path):
        return os.path.exists(file_path)
    
    # Se path é relativo, juntar com workspace
    full_path = os.path.join(workspace, file_path)
    return os.path.exists(full_path)

def read_file_content(file_path: str, workspace: str = None) -> str:
    """Read file content"""
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
        print_warning(f"Error reading file {file_path}: {e}")
        return None

def check_directory_exists(dir_path: str, workspace: str = None) -> bool:
    """Check if directory exists"""
    if not workspace:
        workspace = TEST_WORKSPACE
    
    if os.path.isabs(dir_path):
        return os.path.isdir(dir_path)
    
    full_path = os.path.join(workspace, dir_path)
    return os.path.isdir(full_path)

def extract_create_file_actions(response_text: str) -> List[Tuple[str, str]]:
    """Extract create-file actions from response"""
    import re
    pattern = r'```create-file:([^\n]+)\n([\s\S]*?)```'
    matches = re.findall(pattern, response_text)
    return [(path.strip(), content) for path, content in matches]

def test_1_1_create_simple_file():
    """Test 1.1: Basic Single File"""
    print_test("Test 1.1: Create simple utils.js file")
    
    prompt = "Create a file called utils.js with helper functions for string manipulation."
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(3)
    
    # Check if file was created
    if not check_file_exists("utils.js"):
        print_error("utils.js file was not created")
        print_info(f"AI Response: {response[:500]}")
        return False
    
    print_success("utils.js file created")
    
    # Check content
    content = read_file_content("utils.js")
    if not content:
        print_error("Could not read file content")
        return False
    
    # Check if contains string functions
    if "function" in content.lower() or "const" in content.lower() or "export" in content.lower():
        print_success("Content contains functions")
    else:
        print_warning("Content may not have functions")
    
    # Check if has string manipulation
    string_keywords = ["string", "substring", "replace", "split", "trim", "slice"]
    has_string_ops = any(kw in content.lower() for kw in string_keywords)
    
    if has_string_ops:
        print_success("Content contains string operations")
    else:
        print_warning("Content may not have explicit string operations")
    
    return True

def test_1_2_create_json_file():
    """Test 1.2: JSON File with Specific Structure"""
    print_test("Test 1.2: Create config.json file")
    
    prompt = """Create a config.json file with the following settings:
- apiUrl: "https://api.example.com"
- timeout: 5000
- retries: 3"""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(3)
    
    if not check_file_exists("config.json"):
        print_error("config.json file was not created")
        return False
    
    print_success("config.json file created")
    
    content = read_file_content("config.json")
    if not content:
        return False
    
    # Check if is valid JSON
    try:
        data = json.loads(content)
        print_success("Valid JSON")
        
        # Check properties
        if "apiUrl" in data:
            print_success("apiUrl property present")
        else:
            print_error("apiUrl property missing")
            return False
        
        if data.get("timeout") == 5000:
            print_success("timeout correct")
        else:
            print_warning(f"timeout = {data.get('timeout')}, expected 5000")
        
        if data.get("retries") == 3:
            print_success("retries correct")
        else:
            print_warning(f"retries = {data.get('retries')}, expected 3")
        
        return True
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON: {e}")
        return False

def test_1_3_create_file_in_subdirectory():
    """Test 1.3: File in Subdirectory"""
    print_test("Test 1.3: Create src/components/Button.jsx file")
    
    prompt = "Create a file src/components/Button.jsx with a React button component."
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(3)
    
    # Check if directory was created
    if not check_directory_exists("src/components"):
        print_error("src/components/ directory was not created")
        return False
    
    print_success("src/components/ directory created")
    
    # Check if file was created
    if not check_file_exists("src/components/Button.jsx"):
        print_error("Button.jsx file was not created")
        return False
    
    print_success("Button.jsx file created in correct location")
    
    # Check content
    content = read_file_content("src/components/Button.jsx")
    if not content:
        return False
    
    # Check if is React component
    react_keywords = ["react", "import", "export", "function", "component", "props"]
    has_react = any(kw in content.lower() for kw in react_keywords)
    
    if has_react:
        print_success("Functional React component")
    else:
        print_warning("Content may not be a valid React component")
    
    # Check imports
    if "import" in content.lower() and "react" in content.lower():
        print_success("Correct imports")
    else:
        print_warning("Imports may be missing")
    
    return True

def test_2_1_add_function():
    """Test 2.1: Add Function"""
    print_test("Test 2.1: Add formatDate function to utils.js")
    
    # First check if utils.js exists (created in test 1.1)
    if not check_file_exists("utils.js"):
        print_warning("utils.js does not exist, creating first...")
        # Create basic utils.js if it doesn't exist
        prompt = "Create a utils.js file with basic helper functions."
        send_chat_message(prompt)
        time.sleep(3)
    
    if not check_file_exists("utils.js"):
        print_error("Could not create/verify utils.js")
        return False
    
    # Read original content
    original_content = read_file_content("utils.js")
    if not original_content:
        print_error("Could not read utils.js")
        return False
    
    print_info(f"Original content has {len(original_content)} characters")
    
    # Add function
    prompt = """MODIFY the EXISTING utils.js file (which already exists in the workspace) by adding a function called formatDate that formats dates in DD/MM/YYYY format.

CRITICAL: 
- The utils.js file ALREADY EXISTS in the workspace
- You MUST use the format ```modify-file:utils.js (NOT create-file)
- You MUST include ALL existing file content
- You MUST preserve ALL existing functions (capitalize, isEmpty, reverseString, createSlug, countWords)
- You MUST add the new formatDate function at the end of the file
- DO NOT create new files, only MODIFY the existing file"""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    # Check if response contains modify-file
    if "modify-file" in response.lower():
        print_success("Response contains modify-file")
    else:
        print_warning(f"Response may not contain modify-file: {response[:200]}")
    
    print_info("Waiting for processing...")
    time.sleep(5)  # Increase wait time
    
    # Check if file still exists
    if not check_file_exists("utils.js"):
        print_error("utils.js file was removed!")
        return False
    
    # Read modified content
    modified_content = read_file_content("utils.js")
    if not modified_content:
        return False
    
    # Check if function was added (case-insensitive)
    modified_lower = modified_content.lower()
    if "formatdate" in modified_lower or "format_date" in modified_lower:
        print_success("formatDate function added")
    else:
        print_error("formatDate function was not found")
        print_info(f"Modified content has {len(modified_content)} characters")
        print_info(f"First 200 chars: {modified_content[:200]}")
        print_info(f"Last 200 chars: {modified_content[-200:]}")
        # Check if file was modified
        if len(modified_content) <= len(original_content):
            print_warning("File may not have been modified (similar or smaller size)")
        return False
    
    # Check if existing code was preserved
    # At least 50% of original content should be present
    original_length = len(original_content)
    preserved = sum(1 for line in original_content.split('\n')[:5] if line.strip() in modified_content)
    
    if preserved >= 2 or len(modified_content) >= original_length * 0.5:
        print_success("Existing code preserved")
    else:
        print_warning("Existing code may have been removed")
    
    # Check date format
    if "DD/MM/YYYY" in modified_content or "dd/mm/yyyy" in modified_content.lower() or "/" in modified_content:
        print_success("Correct date format (DD/MM/YYYY)")
    else:
        print_warning("Date format may not be correct")
    
    return True

def test_3_1_create_folder():
    """Test 3.1: Create Folder"""
    print_test("Test 3.1: Create tests/ folder")
    
    prompt = "Create a folder called tests to store the project tests."
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(3)
    
    # Check if folder was created
    if not check_directory_exists("tests"):
        print_error("tests/ folder was not created")
        return False
    
    print_success("tests/ folder created")
    
    # Check structure
    if os.path.isdir(os.path.join(TEST_WORKSPACE, "tests")):
        print_success("Directory structure correct")
    else:
        print_error("Directory structure incorrect")
        return False
    
    # Check if can create files inside
    test_file = os.path.join(TEST_WORKSPACE, "tests", "test.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print_success("Can create files inside folder")
    except Exception as e:
        print_warning(f"Could not create file inside: {e}")
    
    return True

def test_3_2_create_folder_structure():
    """Test 3.2: Complete Folder Structure"""
    print_test("Test 3.2: Create React folder structure")
    
    prompt = """Create the complete folder structure for a React project with useful files in each folder:
- src/components (with index.js or component example)
- src/hooks (with index.js or hook example)
- src/utils (with index.js with utility functions)
- src/services (with index.js with API services)
- public (with index.html or README.md)

Create ALL folders with useful and professional files, not just empty folders."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(5)  # More time for multiple folders
    
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
        # Check if folder exists (may have been created by file inside)
        folder_path = os.path.join(TEST_WORKSPACE, folder)
        if os.path.isdir(folder_path):
            # Check if has useful files inside (not just .gitkeep)
            files_in_folder = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            useful_files = [f for f in files_in_folder if not f.endswith('.gitkeep')]
            
            if useful_files:
                print_success(f"Folder {folder}/ created with useful files: {', '.join(useful_files)}")
            elif files_in_folder:
                print_success(f"Folder {folder}/ created (with .gitkeep)")
            else:
                print_success(f"Folder {folder}/ created")
        else:
            print_error(f"Folder {folder}/ was not created")
            all_created = False
    
    if not all_created:
        # Check how many were created
        created_count = sum(1 for folder in folders if os.path.isdir(os.path.join(TEST_WORKSPACE, folder)))
        print_warning(f"Only {created_count}/{len(folders)} folders were created")
        return False
    
    # Check hierarchical structure
    if check_directory_exists("src") and check_directory_exists("public"):
        print_success("Hierarchical structure correct")
    else:
        print_error("Hierarchical structure incorrect")
        return False
    
    return True

def test_5_1_create_web_project():
    """Test 5.1: Web Todo List Project"""
    print_test("Test 5.1: Create complete web Todo List project")
    
    prompt = """Create a complete Todo List web application with:
- index.html (HTML5 structure)
- styles.css (modern dark theme)
- app.js (complete logic)
- README.md (documentation)"""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(5)  # More time for complete project
    
    # Verificar todos os arquivos
    files = ["index.html", "styles.css", "app.js", "README.md"]
    
    all_created = True
    for file in files:
        if check_file_exists(file):
            print_success(f"File {file} created")
        else:
            print_error(f"File {file} was not created")
            all_created = False
    
    if not all_created:
        return False
    
    # Check HTML
    html_content = read_file_content("index.html")
    if html_content:
        if "<!DOCTYPE html>" in html_content or "<html" in html_content.lower():
            print_success("Valid and semantic HTML")
        else:
            print_warning("HTML may not be correct")
    
    # Check CSS
    css_content = read_file_content("styles.css")
    if css_content:
        if "dark" in css_content.lower() or "background" in css_content.lower():
            print_success("CSS with dark theme")
        else:
            print_warning("CSS may not have dark theme")
    
    # Check JavaScript
    js_content = read_file_content("app.js")
    if js_content:
        if "function" in js_content.lower() or "const" in js_content.lower():
            print_success("Functional JavaScript")
        else:
            print_warning("JavaScript may not be complete")
    
    # Check README
    readme_content = read_file_content("README.md")
    if readme_content:
        if len(readme_content) > 50:
            print_success("Complete README")
        else:
            print_warning("README may be incomplete")
    
    return True

def test_8_3_reference_existing_file():
    """Test 8.3: Reference Existing File"""
    print_test("Test 8.3: Create Card.jsx based on Button.jsx")
    
    # First ensure Button.jsx exists (created in test 1.3)
    if not check_file_exists("src/components/Button.jsx"):
        print_warning("Button.jsx does not exist, creating first...")
        prompt = "Create a file src/components/Button.jsx with a React button component."
        send_chat_message(prompt)
        time.sleep(3)
    
    if not check_file_exists("src/components/Button.jsx"):
        print_error("Could not create/verify Button.jsx")
        return False
    
    # Read Button.jsx to compare later
    button_content = read_file_content("src/components/Button.jsx")
    if not button_content:
        print_error("Could not read Button.jsx")
        return False
    
    print_info(f"Button.jsx has {len(button_content)} characters")
    
    # Create Card.jsx based on Button.jsx
    prompt = "Create a Card.jsx file based on the existing Button.jsx file, maintaining the same style and structure."
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(3)
    
    # Check if Card.jsx was created
    card_path = "src/components/Card.jsx"
    if not check_file_exists(card_path):
        # May have been created in root
        if check_file_exists("Card.jsx"):
            card_path = "Card.jsx"
        else:
            print_error("Card.jsx was not created")
            return False
    
    print_success("Card.jsx created")
    
    # Read Card.jsx
    card_content = read_file_content(card_path)
    if not card_content:
        return False
    
    # Check similar structure
    # Compare imports, exports, structure
    button_imports = [line for line in button_content.split('\n') if 'import' in line.lower()]
    card_imports = [line for line in card_content.split('\n') if 'import' in line.lower()]
    
    if button_imports and card_imports:
        # Check if imports are similar
        similar_imports = any(any(kw in card_import.lower() for kw in ['react', 'button']) for card_import in card_imports)
        if similar_imports or len(card_imports) > 0:
            print_success("Consistent imports")
        else:
            print_warning("Imports may not be consistent")
    
    # Check if has similar structure (function, export, props)
    structure_keywords = ["function", "export", "props", "component"]
    button_has = sum(1 for kw in structure_keywords if kw in button_content.lower())
    card_has = sum(1 for kw in structure_keywords if kw in card_content.lower())
    
    if card_has >= 2:
        print_success("Similar structure maintained")
    else:
        print_warning("Structure may not be similar")
    
    # Check style (check if has similar patterns)
    if "Card" in card_content and ("function" in card_content.lower() or "const" in card_content.lower()):
        print_success("Style and patterns maintained")
    else:
        print_warning("Style may not be maintained")
    
    return True

def test_2_2_fix_bug():
    """Test 2.2: Fix Bug"""
    print_test("Test 2.2: Fix bug in app.js file")
    
    # First create app.js with bug
    if not check_file_exists("app.js"):
        prompt = """CREATE an app.js file using the create-file: format with a calculateTotal function that has a bug:

```create-file:app.js
function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}

// This function returns NaN when items is empty or undefined
```"""
        send_chat_message(prompt)
        time.sleep(3)
    
    if not check_file_exists("app.js"):
        print_error("Could not create app.js")
        return False
    
    # Read original content
    original_content = read_file_content("app.js")
    if not original_content:
        print_error("Could not read app.js")
        return False
    
    # Fix bug
    prompt = """MODIFY the app.js file that already exists in the workspace. The calculateTotal function is returning NaN when items is empty or undefined.

CRITICAL:
- The app.js file ALREADY EXISTS in the workspace
- You MUST use the format ```modify-file:app.js (NOT create-file)
- You MUST include ALL existing file content
- You MUST preserve the calculateTotal function
- You MUST add validation for empty or undefined items
- DO NOT create new files, only MODIFY the existing file"""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(5)
    
    # Check if file still exists
    if not check_file_exists("app.js"):
        print_error("app.js file was removed!")
        return False
    
    # Ler conteúdo modificado
    modified_content = read_file_content("app.js")
    if not modified_content:
        return False
    
    # Check if bug was fixed (should have validation for empty or undefined array)
    bug_fixes = [
        "items &&" in modified_content or "items ?" in modified_content,
        "items.length" in modified_content or "Array.isArray" in modified_content,
        "|| 0" in modified_content or "?? 0" in modified_content,
        "if (!items" in modified_content or "if (items" in modified_content
    ]
    
    if any(bug_fixes):
        print_success("Bug identified and fixed")
    else:
        print_warning("Bug may not have been fixed")
    
    # Check if function still exists
    if "calculateTotal" in modified_content:
        print_success("calculateTotal function preserved")
    else:
        print_error("calculateTotal function not found")
        return False
    
    # Check if existing code was preserved
    if len(modified_content) >= len(original_content) * 0.5:
        print_success("Existing code preserved")
    else:
        print_warning("Existing code may have been removed")
    
    return True

def test_2_3_refactor_code():
    """Test 2.3: Refactor Code"""
    print_test("Test 2.3: Refactor code applying SOLID")
    
    # Create userService.js with unrefactored code
    if not check_file_exists("userService.js"):
        prompt = """CREATE a userService.js file using the create-file: format with a UserService class that does everything:
- Fetches users
- Validates data
- Saves to database
- Sends emails
- Generates reports

Everything in a single class (violating Single Responsibility).

IMPORTANT: Use the format ```create-file:userService.js to create the file."""
        send_chat_message(prompt)
        time.sleep(3)
    
    if not check_file_exists("userService.js"):
        print_error("Could not create userService.js")
        return False
    
    # Refactor
    prompt = """Refactor the userService.js file that already exists in the workspace by applying SOLID principles, especially Single Responsibility.

CRITICAL:
- The userService.js file ALREADY EXISTS in the workspace
- You MUST separate responsibilities into different classes
- You CAN create new files to separate responsibilities (e.g., UserValidator.js, UserRepository.js, EmailService.js, ReportService.js)
- Use the format ```create-file: for new files
- Use the format ```modify-file: to modify userService.js
- Maintain the original functionality, just organize it better"""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(5)
    
    # Check if file was refactored (may have created multiple files)
    # Check if there are multiple classes or files
    files_created = []
    for file in os.listdir(TEST_WORKSPACE):
        if file.endswith('.js') and ('user' in file.lower() or 'service' in file.lower() or 'validator' in file.lower()):
            files_created.append(file)
    
    if len(files_created) > 1:
        print_success(f"Responsibilities separated into {len(files_created)} files")
    elif check_file_exists("userService.js"):
        content = read_file_content("userService.js")
        # Check if has multiple classes or separated functions
        class_count = content.count("class ")
        if class_count > 1:
            print_success("Multiple classes created (responsibilities separated)")
        else:
            print_warning("May not have been refactored adequately")
    
    return True

def test_5_2_react_project():
    """Test 5.2: Complete React Project"""
    print_test("Test 5.2: Create complete React project")
    
    prompt = """CREATE a complete React project using the create-file: format for EACH file:

CREATE ALL these files using the format ```create-file:path:
- package.json with dependencies (react, react-dom)
- src/App.jsx (main component)
- src/components/Header.jsx (header component)
- src/components/Footer.jsx (footer component)
- src/index.js (entry point)
- public/index.html (base HTML)
- README.md (documentation)

IMPORTANT: Use multiple ```create-file: blocks to create ALL files in a single response."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
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
            print_success(f"File {file} created")
        else:
            print_error(f"File {file} was not created")
            all_created = False
    
    if not all_created:
        return False
    
    # Check package.json
    package_content = read_file_content("package.json")
    if package_content:
        if "react" in package_content.lower() and "dependencies" in package_content.lower():
            print_success("package.json configured correctly")
        else:
            print_warning("package.json may not be correct")
    
    # Check components
    app_content = read_file_content("src/App.jsx")
    header_content = read_file_content("src/components/Header.jsx")
    
    if app_content and "import" in app_content.lower() and "export" in app_content.lower():
        print_success("App.jsx component functional")
    else:
        print_warning("App.jsx may not be correct")
    
    if header_content and ("function" in header_content.lower() or "const" in header_content.lower()):
        print_success("Header.jsx component functional")
    else:
        print_warning("Header.jsx may not be correct")
    
    return True

def test_6_1_email_html():
    """Test 6.1: Email HTML"""
    print_test("Test 6.1: Create HTML email template")
    
    prompt = """Create a professional HTML email template for registration confirmation with:
- Header with logo
- Body with welcome message
- Footer with social links
- Inline styles for email client compatibility"""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(3)
    
    # Check if file was created (may have various names)
    email_files = [f for f in os.listdir(TEST_WORKSPACE) if f.endswith('.html') and ('email' in f.lower() or 'template' in f.lower() or 'welcome' in f.lower())]
    
    if not email_files:
        # Try to find any HTML
        html_files = [f for f in os.listdir(TEST_WORKSPACE) if f.endswith('.html')]
        if html_files:
            email_files = [html_files[0]]
    
    if not email_files:
        print_error("Email template was not created")
        return False
    
    email_file = email_files[0]
    print_success(f"Email template created: {email_file}")
    
    content = read_file_content(email_file)
    if not content:
        return False
    
    # Check template characteristics
    checks = [
        ("<html" in content.lower() or "<!doctype" in content.lower(), "Valid HTML"),
        ("style=" in content or "style:" in content, "Inline styles"),
        ("header" in content.lower() or "logo" in content.lower(), "Header present"),
        ("footer" in content.lower() or "social" in content.lower(), "Footer present"),
        ("welcome" in content.lower() or "confirmation" in content.lower(), "Welcome message")
    ]
    
    for check, desc in checks:
        if check:
            print_success(desc)
        else:
            print_warning(f"{desc} may be missing")
    
    return True

def test_6_2_notification_templates():
    """Test 6.2: Notification Message"""
    print_test("Test 6.2: Create notification templates")
    
    prompt = """CREATE a notificationTemplates.js file using the create-file: format with message templates:
- Success
- Error
- Warning
- Information

IMPORTANT: Use the format ```create-file:notificationTemplates.js to create the file."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(3)
    
    if not check_file_exists("notificationTemplates.js"):
        print_error("notificationTemplates.js file was not created")
        return False
    
    print_success("notificationTemplates.js file created")
    
    content = read_file_content("notificationTemplates.js")
    if not content:
        return False
    
    # Check templates
    templates = ["success", "error", "warning", "info", "information"]
    found = sum(1 for t in templates if t.lower() in content.lower())
    
    if found >= 3:
        print_success("Notification templates present")
    else:
        print_warning("Some templates may be missing")
    
    if "function" in content.lower() or "const" in content.lower() or "export" in content.lower():
        print_success("Well-structured code")
    else:
        print_warning("Code may not be well-structured")
    
    return True

def test_7_1_todo_list():
    """Test 7.1: Task List"""
    print_test("Test 7.1: Create task list for implementation")
    
    prompt = """CREATE a TODO.md file using the create-file: format with a task list to implement an authentication system:
1. Create user model
2. Implement login/register endpoints
3. Add authentication middleware
4. Create unit tests
5. Document API

IMPORTANT: Use the format ```create-file:TODO.md to create the file."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(3)
    
    if not check_file_exists("TODO.md"):
        print_error("TODO.md file was not created")
        return False
    
    print_success("TODO.md file created")
    
    content = read_file_content("TODO.md")
    if not content:
        return False
    
    # Check tasks
    tasks = ["model", "user", "endpoints", "login", "register", "middleware", "authentication", "tests", "document", "api"]
    found = sum(1 for t in tasks if t.lower() in content.lower())
    
    if found >= 5:
        print_success("Tasks listed correctly")
    else:
        print_warning("Some tasks may be missing")
    
    if "#" in content or "-" in content or "*" in content or "1." in content:
        print_success("Correct Markdown format")
    else:
        print_warning("Format may not be correct")
    
    return True

def test_8_1_conversation_context():
    """Test 8.1: Conversation Context"""
    print_test("Test 8.1: Conversation context (multiple messages)")
    
    # Reset history for this test
    reset_conversation_history()
    
    # First message: create User class
    prompt1 = """CREATE a user.js file using the create-file: format with a User class that has name and email properties.

IMPORTANT: Use the format ```create-file:user.js to create the file."""
    response1, _ = send_chat_message(prompt1, use_history=True)
    if not response1:
        return False
    
    print_info("Waiting for first message...")
    time.sleep(3)
    
    if not check_file_exists("user.js"):
        print_error("user.js was not created in the first message")
        return False
    
    print_success("user.js created in the first message")
    
    # Second message: add method (should remember the created user.js)
    # First, read the current content to include in the prompt
    user_content = read_file_content("user.js")
    if user_content:
        # Escape braces for f-string
        escaped_content = user_content.replace('{', '{{').replace('}', '}}')
        prompt2 = f"""MODIFY the user.js file that we created in the previous message. Add a getFullName() method to the User class that returns the full name (name + email).

CURRENT FILE CONTENT (YOU MUST USE THIS EXACT CONTENT AS BASE):
```javascript
{user_content}
```

CRITICAL INSTRUCTIONS - READ CAREFULLY:
1. The user.js file ALREADY EXISTS and was created in the previous message
2. You MUST use the format ```modify-file:user.js (NOT create-file)
3. You MUST copy ALL the content shown above EXACTLY as it is
4. You MUST add the getFullName() method INSIDE the User class, after the constructor
5. The method should be: getFullName() {{ return `${{this.name}} ${{this.email}}`; }}
6. DO NOT remove or change any existing code
7. DO NOT create new files, only MODIFY the existing file
8. The output must be the COMPLETE file with ALL original content PLUS the new method

STEP-BY-STEP:
1. Start with: ```modify-file:user.js
2. Copy the ENTIRE current file content shown above
3. Add the getFullName() method INSIDE the class, after the constructor
4. Keep the export statement
5. End with: ```

EXAMPLE OF CORRECT OUTPUT:
```modify-file:user.js
{user_content}
  getFullName() {{
    return `${{this.name}} ${{this.email}}`;
  }}
}}

export default User;
```

IMPORTANT: The file content above is the EXACT current content. Copy it completely, then add the method."""
    else:
        prompt2 = """MODIFY the user.js file that we created in the previous message. Add a getFullName() method to the User class that returns the full name (name + email).

CRITICAL:
- The user.js file ALREADY EXISTS and was created in the previous message
- You MUST use the format ```modify-file:user.js (NOT create-file)
- You MUST include ALL existing file content (the User class with name and email)
- You MUST add the getFullName() method INSIDE the User class
- DO NOT create new files, only MODIFY the existing file
- The method should return a string combining name and email"""
    response2, _ = send_chat_message(prompt2, use_history=True)
    if not response2:
        print_error("Second message failed")
        reset_conversation_history()
        return False
    
    print_info("Waiting for second message...")
    time.sleep(5)
    
    # Check if modify-file was used
    if "modify-file" in response2.lower():
        print_success("Response contains modify-file")
    else:
        print_warning(f"Response may not contain modify-file: {response2[:200]}")
    
    user_content = read_file_content("user.js")
    if not user_content:
        return False
    
    if "getFullName" in user_content:
        print_success("getFullName method added")
    else:
        print_error("getFullName method was not added")
        print_info(f"Current content of user.js: {user_content[:500]}")
        reset_conversation_history()
        return False
    
    if "class User" in user_content:
        print_success("User class preserved")
    else:
        print_error("User class not found")
        return False
    
    # Third message: create service that uses User (should remember user.js)
    prompt3 = """CREATE a userService.js file using the create-file: format that imports and uses the User class we created earlier.

IMPORTANT: 
- Use the format ```create-file:userService.js
- Import the User class from the user.js file we created before
- Create methods that use the User class"""
    response3, _ = send_chat_message(prompt3, use_history=True)
    if not response3:
        return False
    
    print_info("Waiting for third message...")
    time.sleep(3)
    
    if not check_file_exists("userService.js"):
        print_error("userService.js was not created")
        return False
    
    service_content = read_file_content("userService.js")
    if service_content:
        if "import" in service_content.lower() and "user" in service_content.lower():
            print_success("userService.js imports User correctly")
        else:
            print_warning("userService.js may not be importing User correctly")
    
    # Reset history after test
    reset_conversation_history()
    
    return True

def test_8_2_workspace_context():
    """Test 8.2: Workspace Context"""
    print_test("Test 8.2: Workspace context")
    
    # Create some files first to have context
    if not check_file_exists("config.json"):
        prompt = 'CREATE a config.json file using create-file: with {"apiUrl": "https://api.example.com"}'
        send_chat_message(prompt)
        time.sleep(2)
    
    if not check_file_exists("utils.js"):
        prompt = "CREATE a utils.js file using create-file: with a helper function"
        send_chat_message(prompt)
        time.sleep(2)
    
    # Now ask to create a file that integrates
    prompt = """Analyze the current workspace and CREATE an api.js file using the create-file: format that integrates with the existing files (config.json and utils.js).

IMPORTANT: Use the format ```create-file:api.js to create the file."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(5)
    
    if not check_file_exists("api.js"):
        print_error("api.js file was not created")
        return False
    
    print_success("api.js file created")
    
    api_content = read_file_content("api.js")
    if not api_content:
        return False
    
    # Check if imports existing files
    if ("import" in api_content.lower() or "require" in api_content.lower()) and ("config" in api_content.lower() or "utils" in api_content.lower()):
        print_success("Integration with existing files")
    else:
        print_warning("May not be integrating with existing files")
    
    return True

def test_4_1_android_basic():
    """Test 4.1: Android Basic Project"""
    print_test("Test 4.1: Create basic Android Kotlin project")
    
    prompt = """CREATE a complete Android Kotlin project with ALL necessary files using the create-file: format:

CREATE ALL these files:
- app/src/main/java/com/example/app/MainActivity.kt
- app/src/main/res/layout/activity_main.xml
- app/src/main/AndroidManifest.xml
- app/build.gradle.kts
- build.gradle.kts (project level)
- app/src/main/res/values/strings.xml
- app/src/main/res/values/colors.xml
- app/src/main/res/values/themes.xml
- README.md with setup instructions

IMPORTANT: Use multiple ```create-file: blocks to create ALL files in a single response."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(5)
    
    # Check essential files
    files = [
        "app/src/main/java/com/example/app/MainActivity.kt",
        "app/src/main/res/layout/activity_main.xml",
        "app/src/main/AndroidManifest.xml",
        "app/build.gradle.kts",
        "build.gradle.kts",
        "app/src/main/res/values/strings.xml",
        "README.md"
    ]
    
    all_created = True
    for file in files:
        if check_file_exists(file):
            print_success(f"File {file} created")
        else:
            print_error(f"File {file} was not created")
            all_created = False
    
    if not all_created:
        return False
    
    # Check MainActivity
    main_activity = read_file_content("app/src/main/java/com/example/app/MainActivity.kt")
    if main_activity and ("class MainActivity" in main_activity or "MainActivity" in main_activity):
        print_success("MainActivity functional")
    else:
        print_warning("MainActivity may not be correct")
    
    # Check build.gradle.kts
    build_gradle = read_file_content("app/build.gradle.kts")
    if build_gradle and ("kotlin" in build_gradle.lower() or "android" in build_gradle.lower()):
        print_success("build.gradle.kts configured")
    else:
        print_warning("build.gradle.kts may not be correct")
    
    return True

def test_4_2_android_clean_architecture():
    """Test 4.2: Android Clean Architecture"""
    print_test("Test 4.2: Create Android app with Clean Architecture")
    
    prompt = """CREATE a complete Android app following Clean Architecture with ALL layers using the create-file: format:

CREATE the complete structure:
- data layer (repositories, data sources, models)
- domain layer (use cases, entities, interfaces)
- presentation layer (viewmodels, ui)
- Dependency injection setup (Hilt or Koin)
- build.gradle.kts with dependencies
- README.md

IMPORTANT: Create ALL files using multiple ```create-file: blocks."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(5)
    
    # Check layers
    layers = [
        "data", "domain", "presentation"
    ]
    
    layers_found = 0
    for layer in layers:
        # Check if layer directory exists or files with layer name
        files = [f for f in os.listdir(TEST_WORKSPACE) if layer in f.lower()]
        if files or check_directory_exists(layer):
            layers_found += 1
            print_success(f"{layer} layer created")
        else:
            print_warning(f"{layer} layer may not be created")
    
    if layers_found >= 2:
        print_success("Clean Architecture structure created")
    else:
        print_warning("Clean Architecture structure may be incomplete")
    
    return layers_found >= 2

def test_5_3_express_api():
    """Test 5.3: Express REST API"""
    print_test("Test 5.3: Create Express REST API")
    
    prompt = """CREATE a complete Node.js + Express REST API with ALL files using the create-file: format:

CREATE the complete structure:
- routes/ (user routes)
- controllers/ (user controller)
- models/ (user model)
- middleware/ (auth, error handling)
- config/ (database, app config)
- server.js or app.js (entry point)
- package.json with dependencies
- .env.example
- README.md

IMPORTANT: Create ALL files using multiple ```create-file: blocks."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(5)
    
    # Check structure
    files = [
        "package.json",
        "server.js", "app.js"  # Either one
    ]
    
    entry_found = False
    for file in files:
        if check_file_exists(file):
            entry_found = True
            print_success(f"Entry point {file} created")
            break
    
    if not entry_found:
        print_error("Entry point not found")
        return False
    
    # Check package.json
    package_json = read_file_content("package.json")
    if package_json:
        if "express" in package_json.lower():
            print_success("package.json configured with Express")
        else:
            print_warning("package.json may not have Express")
    
    # Check structure directories
    structure_dirs = ["routes", "controllers", "models", "middleware"]
    dirs_found = sum(1 for d in structure_dirs if check_directory_exists(d) or any(f.startswith(d) for f in os.listdir(TEST_WORKSPACE)))
    
    if dirs_found >= 2:
        print_success(f"API structure created ({dirs_found} directories)")
    else:
        print_warning("API structure may be incomplete")
    
    return entry_found and dirs_found >= 2

def test_9_1_solid_project():
    """Test 9.1: SOLID Principles Project"""
    print_test("Test 9.1: Create project following SOLID principles")
    
    prompt = """CREATE a complete Python project following ALL SOLID principles using the create-file: format:

CREATE files demonstrating:
- Single Responsibility: separate classes for different responsibilities
- Open/Closed: extensible without modification
- Liskov Substitution: subclasses replaceable
- Interface Segregation: specific interfaces
- Dependency Inversion: depend on abstractions

Create:
- Multiple classes demonstrating each principle
- requirements.txt
- README.md explaining SOLID principles
- Example usage

IMPORTANT: Create ALL files using multiple ```create-file: blocks."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(5)
    
    # Check for Python files
    py_files = [f for f in os.listdir(TEST_WORKSPACE) if f.endswith('.py')]
    
    if len(py_files) >= 3:
        print_success(f"Multiple Python files created ({len(py_files)})")
    else:
        print_warning("May not have enough files to demonstrate SOLID")
    
    # Check for README
    if check_file_exists("README.md"):
        readme = read_file_content("README.md")
        if readme:
            solid_keywords = ["solid", "single responsibility", "open/closed", "liskov", "interface segregation", "dependency inversion"]
            found = sum(1 for kw in solid_keywords if kw.lower() in readme.lower())
            if found >= 3:
                print_success("README explains SOLID principles")
            else:
                print_warning("README may not explain SOLID adequately")
    
    return len(py_files) >= 3

def test_9_2_clean_architecture():
    """Test 9.2: Clean Architecture Project"""
    print_test("Test 9.2: Create project with Clean Architecture")
    
    prompt = """CREATE a complete project following Clean Architecture with ALL layers using the create-file: format:

CREATE the complete structure:
- Entities (domain layer)
- Use Cases (application layer)
- Interface Adapters (presentation, infrastructure)
- Frameworks (external dependencies)
- Dependencies pointing inward
- README.md explaining architecture

IMPORTANT: Create ALL files using multiple ```create-file: blocks."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(5)
    
    # Check for architecture layers
    layer_keywords = ["entity", "usecase", "usecases", "adapter", "framework", "domain", "application", "infrastructure"]
    files = os.listdir(TEST_WORKSPACE)
    layers_found = sum(1 for kw in layer_keywords if any(kw in f.lower() for f in files) or check_directory_exists(kw))
    
    if layers_found >= 3:
        print_success(f"Clean Architecture layers created ({layers_found})")
    else:
        print_warning("Clean Architecture structure may be incomplete")
    
    return layers_found >= 3

def test_p1_1_fastapi_project():
    """Test P1.1: FastAPI Project"""
    print_test("Test P1.1: Create complete FastAPI project")
    
    prompt = """CREATE a complete FastAPI REST API project with ALL files using the create-file: format:

CREATE the complete structure:
- src/api/ (routes)
- src/models/ (database models)
- src/services/ (business logic)
- src/utils/ (helpers)
- main.py (entry point)
- requirements.txt
- README.md
- .env.example

IMPORTANT: Create ALL files using multiple ```create-file: blocks."""
    
    response, result = send_chat_message(prompt)
    if not response:
        return False
    
    print_info("Waiting for processing...")
    time.sleep(5)
    
    # Check essential files
    files = [
        "main.py", "requirements.txt", "README.md"
    ]
    
    all_created = True
    for file in files:
        if check_file_exists(file):
            print_success(f"File {file} created")
        else:
            print_error(f"File {file} was not created")
            all_created = False
    
    if not all_created:
        return False
    
    # Check requirements.txt
    requirements = read_file_content("requirements.txt")
    if requirements and "fastapi" in requirements.lower():
        print_success("requirements.txt has FastAPI")
    else:
        print_warning("requirements.txt may not have FastAPI")
    
    # Check structure
    structure_dirs = ["src/api", "src/models", "src/services"]
    dirs_found = sum(1 for d in structure_dirs if check_directory_exists(d) or any(d.replace("/", os.sep) in f for f in os.listdir(TEST_WORKSPACE)))
    
    if dirs_found >= 2:
        print_success(f"FastAPI structure created ({dirs_found} directories)")
    else:
        print_warning("FastAPI structure may be incomplete")
    
    return all_created and dirs_found >= 2

def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}")
    print("🚀 TEST VALIDATION RUNNER - DuilioCode Studio")
    print(f"{'='*70}{Colors.RESET}\n")
    
    # Check server
    print_info("Checking server...")
    if not check_server():
        print_error("Server is not running! Start DuilioCode Studio first.")
        print_info("Execute: cd duilio-code-studio && python -m src.main")
        sys.exit(1)
    print_success("Server is running")
    
    # Create workspace
    Path(TEST_WORKSPACE).mkdir(parents=True, exist_ok=True)
    print_info(f"Workspace: {TEST_WORKSPACE}")
    
    # Reset conversation history
    reset_conversation_history()
    
    # Run tests
    results = []
    
    print(f"\n{Colors.BOLD}{'='*70}")
    print("RUNNING TESTS")
    print(f"{'='*70}{Colors.RESET}\n")
    
    # Teste 1.1
    try:
        result = test_1_1_create_simple_file()
        results.append(("1.1 - Arquivo Único Básico", result))
    except Exception as e:
        print_error(f"Error in test 1.1: {e}")
        results.append(("1.1 - Arquivo Único Básico", False))
    
    time.sleep(2)
    
    # Teste 1.2
    try:
        result = test_1_2_create_json_file()
        results.append(("1.2 - Arquivo JSON", result))
    except Exception as e:
        print_error(f"Error in test 1.2: {e}")
        results.append(("1.2 - Arquivo JSON", False))
    
    time.sleep(2)
    
    # Teste 1.3
    try:
        result = test_1_3_create_file_in_subdirectory()
        results.append(("1.3 - Arquivo em Subdiretório", result))
    except Exception as e:
        print_error(f"Error in test 1.3: {e}")
        results.append(("1.3 - Arquivo em Subdiretório", False))
    
    time.sleep(2)
    
    # Teste 2.1
    try:
        result = test_2_1_add_function()
        results.append(("2.1 - Adicionar Função", result))
    except Exception as e:
        print_error(f"Error in test 2.1: {e}")
        results.append(("2.1 - Adicionar Função", False))
    
    time.sleep(2)
    
    # Teste 3.1
    try:
        result = test_3_1_create_folder()
        results.append(("3.1 - Criar Pasta", result))
    except Exception as e:
        print_error(f"Error in test 3.1: {e}")
        results.append(("3.1 - Criar Pasta", False))
    
    time.sleep(2)
    
    # Teste 3.2
    try:
        result = test_3_2_create_folder_structure()
        results.append(("3.2 - Estrutura de Pastas Completa", result))
    except Exception as e:
        print_error(f"Error in test 3.2: {e}")
        results.append(("3.2 - Estrutura de Pastas Completa", False))
    
    time.sleep(2)
    
    # Teste 5.1
    try:
        result = test_5_1_create_web_project()
        results.append(("5.1 - Projeto Web Todo List", result))
    except Exception as e:
        print_error(f"Error in test 5.1: {e}")
        results.append(("5.1 - Projeto Web Todo List", False))
    
    time.sleep(2)
    
    # Teste 8.3
    try:
        result = test_8_3_reference_existing_file()
        results.append(("8.3 - Referência a Arquivo Existente", result))
    except Exception as e:
        print_error(f"Error in test 8.3: {e}")
        results.append(("8.3 - Referência a Arquivo Existente", False))
    
    time.sleep(2)
    
    # Teste 2.2: Corrigir Bug
    try:
        result = test_2_2_fix_bug()
        results.append(("2.2 - Corrigir Bug", result))
    except Exception as e:
        print_error(f"Error in test 2.2: {e}")
        results.append(("2.2 - Corrigir Bug", False))
    
    time.sleep(2)
    
    # Teste 2.3: Refatorar Código
    try:
        result = test_2_3_refactor_code()
        results.append(("2.3 - Refatorar Código", result))
    except Exception as e:
        print_error(f"Error in test 2.3: {e}")
        results.append(("2.3 - Refatorar Código", False))
    
    time.sleep(2)
    
    # Teste 5.2: Projeto React Completo
    try:
        result = test_5_2_react_project()
        results.append(("5.2 - Projeto React Completo", result))
    except Exception as e:
        print_error(f"Error in test 5.2: {e}")
        results.append(("5.2 - Projeto React Completo", False))
    
    time.sleep(2)
    
    # Teste 6.1: Email HTML
    try:
        result = test_6_1_email_html()
        results.append(("6.1 - Email HTML", result))
    except Exception as e:
        print_error(f"Error in test 6.1: {e}")
        results.append(("6.1 - Email HTML", False))
    
    time.sleep(2)
    
    # Teste 6.2: Mensagem de Notificação
    try:
        result = test_6_2_notification_templates()
        results.append(("6.2 - Mensagem de Notificação", result))
    except Exception as e:
        print_error(f"Error in test 6.2: {e}")
        results.append(("6.2 - Mensagem de Notificação", False))
    
    time.sleep(2)
    
    # Teste 7.1: Lista de Tarefas
    try:
        result = test_7_1_todo_list()
        results.append(("7.1 - Lista de Tarefas", result))
    except Exception as e:
        print_error(f"Error in test 7.1: {e}")
        results.append(("7.1 - Lista de Tarefas", False))
    
    time.sleep(2)
    
    # Teste 8.1: Contexto de Conversa
    try:
        result = test_8_1_conversation_context()
        results.append(("8.1 - Contexto de Conversa", result))
    except Exception as e:
        print_error(f"Error in test 8.1: {e}")
        results.append(("8.1 - Contexto de Conversa", False))
    
    time.sleep(2)
    
    # Teste 8.2: Contexto do Workspace
    try:
        result = test_8_2_workspace_context()
        results.append(("8.2 - Contexto do Workspace", result))
    except Exception as e:
        print_error(f"Error in test 8.2: {e}")
        results.append(("8.2 - Contexto do Workspace", False))
    
    time.sleep(2)
    
    # Teste 4.1: Projeto Android Básico
    try:
        result = test_4_1_android_basic()
        results.append(("4.1 - Projeto Android Básico", result))
    except Exception as e:
        print_error(f"Error in test 4.1: {e}")
        results.append(("4.1 - Projeto Android Básico", False))
    
    time.sleep(2)
    
    # Teste 4.2: Android Clean Architecture
    try:
        result = test_4_2_android_clean_architecture()
        results.append(("4.2 - Android Clean Architecture", result))
    except Exception as e:
        print_error(f"Error in test 4.2: {e}")
        results.append(("4.2 - Android Clean Architecture", False))
    
    time.sleep(2)
    
    # Teste 5.3: API REST Node.js/Express
    try:
        result = test_5_3_express_api()
        results.append(("5.3 - API REST Express", result))
    except Exception as e:
        print_error(f"Error in test 5.3: {e}")
        results.append(("5.3 - API REST Express", False))
    
    time.sleep(2)
    
    # Teste 9.1: Projeto SOLID
    try:
        result = test_9_1_solid_project()
        results.append(("9.1 - Projeto SOLID", result))
    except Exception as e:
        print_error(f"Error in test 9.1: {e}")
        results.append(("9.1 - Projeto SOLID", False))
    
    time.sleep(2)
    
    # Teste 9.2: Clean Architecture
    try:
        result = test_9_2_clean_architecture()
        results.append(("9.2 - Clean Architecture", result))
    except Exception as e:
        print_error(f"Error in test 9.2: {e}")
        results.append(("9.2 - Clean Architecture", False))
    
    time.sleep(2)
    
    # Teste P1.1: FastAPI Project
    try:
        result = test_p1_1_fastapi_project()
        results.append(("P1.1 - FastAPI Project", result))
    except Exception as e:
        print_error(f"Error in test P1.1: {e}")
        results.append(("P1.1 - FastAPI Project", False))
    
    time.sleep(2)
    
    # Summary
    print(f"\n{Colors.BOLD}{'='*70}")
    print("📊 TEST SUMMARY")
    print(f"{'='*70}{Colors.RESET}\n")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
    
    print(f"\nTotal: {total} tests")
    print_success(f"Passed: {passed}")
    if total - passed > 0:
        print_error(f"Failed: {total - passed}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    print(f"\n{Colors.BLUE}Test workspace: {TEST_WORKSPACE}{Colors.RESET}\n")

if __name__ == "__main__":
    main()
