#!/usr/bin/env python3
"""
Agent Mode File Listing Test
=============================
Tests Agent mode with the EXACT question from screenshot:
- Question: "quero ver os arquivos do path selecionado"
- Mode: AGENT (not Chat)
- Expected: Should list actual files, NOT provide Python code
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8080"

async def test_agent_mode_file_listing():
    """Test Agent mode with file listing question."""
    print("="*60)
    print("🧪 AGENT MODE FILE LISTING TEST")
    print("="*60)
    print()
    
    # Get model
    async with httpx.AsyncClient(timeout=10.0) as client:
        models_resp = await client.get(f"{BASE_URL}/api/models")
        models = models_resp.json()['models']
        model = models[0]['name'] if models else 'qwen2.5-coder:14b'
        print(f"✅ Using model: {model}\n")
    
    # EXACT question from screenshot
    test_question = "quero ver os arquivos do path selecionado"
    workspace_path = "/Users/jeffersonsilva/Desktop"
    
    print(f"Question: {test_question}")
    print(f"Workspace: {workspace_path}")
    print(f"Mode: AGENT (complex endpoint)")
    print()
    print("Expected: Should list actual files from Desktop")
    print("NOT expected: Python code to list files")
    print()
    print("⏳ Sending request to /api/chat (Agent mode endpoint)...")
    print()
    
    start_time = datetime.now()
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Simulate Agent mode request (with workspace_path)
        payload = {
            "messages": [{"role": "user", "content": test_question}],
            "model": model,
            "temperature": 0.7,
            "stream": False,
            "workspace_path": workspace_path
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/chat", json=payload)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                print(f"⏱️  Response time: {elapsed:.1f}s")
                print()
                print("="*60)
                print("RESPONSE:")
                print("="*60)
                print(content)
                print("="*60)
                print()
                
                # Analyze response
                content_lower = content.lower()
                
                # BAD indicators (what we DON'T want)
                bad_indicators = [
                    "import os",
                    "def listar",
                    "os.listdir",
                    "código python",
                    "python code",
                    "aqui está um exemplo",
                    "here's an example",
                    "você pode usar",
                    "you can use",
                    "primeiro, certifique-se",
                    "first, make sure"
                ]
                
                # GOOD indicators (what we DO want)
                good_indicators = [
                    "screenshot",
                    "arquivos",
                    "files",
                    "lista",
                    "list",
                    "11 arquivos",
                    "12 arquivos",
                    "png",
                    "imagens",
                    "diretório",
                    "directory"
                ]
                
                has_bad = any(indicator in content_lower for indicator in bad_indicators)
                has_good = any(indicator in content_lower for indicator in good_indicators)
                has_file_count = any(char.isdigit() for char in content[:300])
                has_actual_files = 'screenshot' in content_lower or 'png' in content_lower
                has_file_list = '\n' in content and ('screenshot' in content_lower or '1.' in content or '-' in content)
                
                print("="*60)
                print("ANALYSIS:")
                print("="*60)
                print(f"Contains Python code: {has_bad}")
                if has_bad:
                    found_bad = [i for i in bad_indicators if i in content_lower]
                    print(f"  ❌ Found: {', '.join(found_bad)}")
                
                print(f"Contains file information: {has_good}")
                if has_good:
                    found_good = [i for i in good_indicators if i in content_lower]
                    print(f"  ✅ Found: {', '.join(found_good)}")
                
                print(f"Has file count: {has_file_count}")
                print(f"Has actual file names: {has_actual_files}")
                print(f"Has file list format: {has_file_list}")
                print()
                
                # Determine result
                if has_bad and not has_good:
                    result = "❌ FAILED - Response provides Python code instead of file list"
                elif has_bad and has_good:
                    result = "⚠️  PARTIAL - Response has both code and file info (should only have file info)"
                elif has_good and has_actual_files and has_file_list:
                    result = "✅ PASSED - Response provides actual file list"
                elif has_good and has_actual_files:
                    result = "⚠️  PARTIAL - Mentions files but no formatted list"
                elif has_good:
                    result = "⚠️  PARTIAL - Mentions files but no actual file names"
                else:
                    result = "❌ FAILED - No file information provided"
                
                print("="*60)
                print(f"RESULT: {result}")
                print("="*60)
                
                return {
                    "question": test_question,
                    "status": result,
                    "response_time": elapsed,
                    "has_bad": has_bad,
                    "has_good": has_good,
                    "has_file_count": has_file_count,
                    "has_actual_files": has_actual_files,
                    "has_file_list": has_file_list,
                    "response": content,
                    "passed": result.startswith("✅")
                }
            else:
                print(f"❌ HTTP {response.status_code}")
                print(response.text[:500])
                return {
                    "question": test_question,
                    "status": f"❌ HTTP {response.status_code}",
                    "response_time": elapsed,
                    "passed": False,
                    "error": response.text[:500]
                }
                
        except httpx.ReadTimeout:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"❌ TIMEOUT after {elapsed:.1f}s")
            return {
                "question": test_question,
                "status": "❌ TIMEOUT",
                "response_time": elapsed,
                "passed": False
            }
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "question": test_question,
                "status": f"❌ ERROR: {str(e)[:100]}",
                "response_time": elapsed,
                "passed": False
            }

if __name__ == "__main__":
    result = asyncio.run(test_agent_mode_file_listing())
    
    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)
    if result.get('passed'):
        print("✅ TEST PASSED - Agent mode correctly lists files")
    else:
        print("❌ TEST FAILED - Agent mode needs fixes")
        print("\nIssues found:")
        if result.get('has_bad'):
            print("  - Response contains Python code (should list files instead)")
        if not result.get('has_good'):
            print("  - Response doesn't contain file information")
        if not result.get('has_actual_files'):
            print("  - Response doesn't list actual file names")
        if not result.get('has_file_list'):
            print("  - Response doesn't have formatted file list")
    print("="*60)
