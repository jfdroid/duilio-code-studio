#!/usr/bin/env python3
"""
Comprehensive Agent Mode Tests
===============================
Tests Agent mode capabilities:
- System information access
- File listing
- Machine-related questions
- Codebase access
"""

import asyncio
import httpx
import json
from typing import Dict, Any, List

BASE_URL = "http://127.0.0.1:8080"

class AgentModeTester:
    """Test suite for Agent mode."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.model = None
    
    async def setup(self):
        """Get available model."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{BASE_URL}/api/models")
                data = response.json()
                models = data.get('models', [])
                if models:
                    self.model = models[0].get('name', 'qwen2.5-coder:14b')
                    print(f"✅ Using model: {self.model}\n")
                else:
                    raise Exception("No models available")
            except Exception as e:
                print(f"❌ Failed to get models: {e}")
                raise
    
    async def test_system_info(self) -> Dict[str, Any]:
        """Test 1: Agent can answer about system OS."""
        print("="*60)
        print("TEST 1: System Information Access")
        print("="*60)
        
        result = {
            "test": "System Information Access",
            "status": "pending",
            "question": "Qual é o sistema operacional da minha máquina?",
            "expected": "Should mention macOS/Darwin",
            "actual": None,
            "passed": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "messages": [{"role": "user", "content": result["question"]}],
                "model": self.model,
                "temperature": 0.7,
                "stream": False
            }
            
            try:
                response = await client.post(f"{BASE_URL}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                
                content = data['choices'][0]['message']['content']
                result["actual"] = content[:200] + "..." if len(content) > 200 else content
                
                # Check if response mentions system info
                system_keywords = ['darwin', 'macos', 'mac', 'sistema operacional', 'operating system']
                has_info = any(kw in content.lower() for kw in system_keywords)
                
                result["passed"] = has_info
                result["status"] = "✅ PASSED" if has_info else "❌ FAILED"
                
                print(f"Question: {result['question']}")
                print(f"Response: {result['actual']}")
                print(f"Status: {result['status']}\n")
                
            except Exception as e:
                result["status"] = f"❌ ERROR: {str(e)}"
                result["actual"] = f"Error: {str(e)}"
                print(f"Error: {e}\n")
                import traceback
                traceback.print_exc()
        
        return result
    
    async def test_cpu_info(self) -> Dict[str, Any]:
        """Test 2: Agent can answer about CPU."""
        print("="*60)
        print("TEST 2: CPU Information Access")
        print("="*60)
        
        result = {
            "test": "CPU Information",
            "status": "pending",
            "question": "Qual é o processador da minha máquina?",
            "expected": "Should mention CPU/processor info",
            "actual": None,
            "passed": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "messages": [{"role": "user", "content": result["question"]}],
                "model": self.model,
                "temperature": 0.7,
                "stream": False
            }
            
            try:
                response = await client.post(f"{BASE_URL}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                
                content = data['choices'][0]['message']['content']
                result["actual"] = content[:200] + "..." if len(content) > 200 else content
                
                # Check if response mentions CPU
                cpu_keywords = ['cpu', 'processador', 'processor', 'apple', 'm4', 'intel', 'amd']
                has_info = any(kw in content.lower() for kw in cpu_keywords)
                
                result["passed"] = has_info
                result["status"] = "✅ PASSED" if has_info else "❌ FAILED"
                
                print(f"Question: {result['question']}")
                print(f"Response: {result['actual']}")
                print(f"Status: {result['status']}\n")
                
            except Exception as e:
                result["status"] = f"❌ ERROR: {str(e)}"
                result["actual"] = f"Error: {str(e)}"
                print(f"Error: {e}\n")
                import traceback
                traceback.print_exc()
        
        return result
    
    async def test_memory_info(self) -> Dict[str, Any]:
        """Test 3: Agent can answer about memory."""
        print("="*60)
        print("TEST 3: Memory Information Access")
        print("="*60)
        
        result = {
            "test": "Memory Information",
            "status": "pending",
            "question": "Quantos GB de RAM tem minha máquina?",
            "expected": "Should mention memory/RAM in GB",
            "actual": None,
            "passed": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "messages": [{"role": "user", "content": result["question"]}],
                "model": self.model,
                "temperature": 0.7,
                "stream": False
            }
            
            try:
                response = await client.post(f"{BASE_URL}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                
                content = data['choices'][0]['message']['content']
                result["actual"] = content[:200] + "..." if len(content) > 200 else content
                
                # Check if response mentions memory
                memory_keywords = ['gb', 'ram', 'memória', 'memory', '24', '16', '32']
                has_info = any(kw in content.lower() for kw in memory_keywords)
                
                result["passed"] = has_info
                result["status"] = "✅ PASSED" if has_info else "❌ FAILED"
                
                print(f"Question: {result['question']}")
                print(f"Response: {result['actual']}")
                print(f"Status: {result['status']}\n")
                
            except Exception as e:
                result["status"] = f"❌ ERROR: {str(e)}"
                result["actual"] = f"Error: {str(e)}"
                print(f"Error: {e}\n")
                import traceback
                traceback.print_exc()
        
        return result
    
    async def test_file_listing(self) -> Dict[str, Any]:
        """Test 4: Agent can list files in workspace."""
        print("="*60)
        print("TEST 4: File Listing in Workspace")
        print("="*60)
        
        result = {
            "test": "File Listing",
            "status": "pending",
            "question": "quantos arquivos voce ve? Liste cada um com nome e tipo.",
            "expected": "Should list files with names and types",
            "actual": None,
            "passed": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "messages": [{"role": "user", "content": result["question"]}],
                "model": self.model,
                "temperature": 0.7,
                "stream": False
            }
            
            try:
                response = await client.post(f"{BASE_URL}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                
                content = data['choices'][0]['message']['content']
                result["actual"] = content[:300] + "..." if len(content) > 300 else content
                
                # Check if response lists files or mentions file count
                has_files = 'arquivo' in content.lower() or 'file' in content.lower()
                has_count = any(char.isdigit() for char in content[:100])
                has_list = '\n' in content or '-' in content or '1.' in content or '*' in content
                mentions_workspace = 'workspace' in content.lower() or 'diretório' in content.lower() or 'directory' in content.lower()
                
                result["passed"] = (has_files and (has_count or has_list)) or mentions_workspace
                result["status"] = "✅ PASSED" if result["passed"] else "❌ FAILED"
                
                print(f"Question: {result['question']}")
                print(f"Response: {result['actual']}")
                print(f"Status: {result['status']}\n")
                
            except Exception as e:
                result["status"] = f"❌ ERROR: {str(e)}"
                result["actual"] = f"Error: {str(e)}"
                print(f"Error: {e}\n")
                import traceback
                traceback.print_exc()
        
        return result
    
    async def test_user_info(self) -> Dict[str, Any]:
        """Test 5: Agent can answer about user."""
        print("="*60)
        print("TEST 5: User Information Access")
        print("="*60)
        
        result = {
            "test": "User Information",
            "status": "pending",
            "question": "Qual é o nome do usuário desta máquina?",
            "expected": "Should mention user name",
            "actual": None,
            "passed": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "messages": [{"role": "user", "content": result["question"]}],
                "model": self.model,
                "temperature": 0.7,
                "stream": False
            }
            
            try:
                response = await client.post(f"{BASE_URL}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                
                content = data['choices'][0]['message']['content']
                result["actual"] = content[:200] + "..." if len(content) > 200 else content
                
                # Check if response mentions user
                user_keywords = ['jeffersonsilva', 'user', 'usuário', 'usuaria']
                has_info = any(kw in content.lower() for kw in user_keywords)
                
                result["passed"] = has_info
                result["status"] = "✅ PASSED" if has_info else "❌ FAILED"
                
                print(f"Question: {result['question']}")
                print(f"Response: {result['actual']}")
                print(f"Status: {result['status']}\n")
                
            except Exception as e:
                result["status"] = f"❌ ERROR: {str(e)}"
                result["actual"] = f"Error: {str(e)}"
                print(f"Error: {e}\n")
                import traceback
                traceback.print_exc()
        
        return result
    
    async def test_hostname(self) -> Dict[str, Any]:
        """Test 6: Agent can answer about hostname."""
        print("="*60)
        print("TEST 6: Hostname Information")
        print("="*60)
        
        result = {
            "test": "Hostname Information",
            "status": "pending",
            "question": "Qual é o hostname desta máquina?",
            "expected": "Should mention hostname",
            "actual": None,
            "passed": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "messages": [{"role": "user", "content": result["question"]}],
                "model": self.model,
                "temperature": 0.7,
                "stream": False
            }
            
            try:
                response = await client.post(f"{BASE_URL}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                
                content = data['choices'][0]['message']['content']
                result["actual"] = content[:200] + "..." if len(content) > 200 else content
                
                # Check if response mentions hostname
                hostname_keywords = ['hostname', 'jeffersons-macbook', 'macbook', 'local', 'mac.home', 'home']
                has_info = any(kw in content.lower() for kw in hostname_keywords)
                
                result["passed"] = has_info
                result["status"] = "✅ PASSED" if has_info else "❌ FAILED"
                
                print(f"Question: {result['question']}")
                print(f"Response: {result['actual']}")
                print(f"Status: {result['status']}\n")
                
            except Exception as e:
                result["status"] = f"❌ ERROR: {str(e)}"
                result["actual"] = f"Error: {str(e)}"
                print(f"Error: {e}\n")
                import traceback
                traceback.print_exc()
        
        return result
    
    async def test_chat_mode_comparison(self) -> Dict[str, Any]:
        """Test 7: Chat mode should NOT have system info."""
        print("="*60)
        print("TEST 7: Chat Mode (Should NOT have system info)")
        print("="*60)
        
        result = {
            "test": "Chat Mode Comparison",
            "status": "pending",
            "question": "Qual é o sistema operacional da minha máquina?",
            "expected": "Should say it doesn't know (Chat mode)",
            "actual": None,
            "passed": False
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "messages": [{"role": "user", "content": result["question"]}],
                "model": self.model,
                "temperature": 0.7,
                "stream": False
            }
            
            try:
                response = await client.post(f"{BASE_URL}/api/chat/simple", json=payload)
                response.raise_for_status()
                data = response.json()
                
                content = data['choices'][0]['message']['content']
                result["actual"] = content[:200] + "..." if len(content) > 200 else content
                
                # Chat mode should NOT know system info
                no_info_keywords = ['não sei', "don't know", 'cannot', 'não tenho acesso', 'não consigo']
                system_keywords = ['darwin', 'macos', 'mac']
                
                has_no_info = any(kw in content.lower() for kw in no_info_keywords)
                has_system_info = any(kw in content.lower() for kw in system_keywords)
                
                # Pass if it says it doesn't know OR doesn't mention specific system
                result["passed"] = has_no_info or not has_system_info
                result["status"] = "✅ PASSED" if result["passed"] else "❌ FAILED"
                
                print(f"Question: {result['question']}")
                print(f"Response: {result['actual']}")
                print(f"Status: {result['status']}\n")
                
            except Exception as e:
                result["status"] = f"❌ ERROR: {str(e)}"
                result["actual"] = f"Error: {str(e)}"
                print(f"Error: {e}\n")
                import traceback
                traceback.print_exc()
        
        return result
    
    async def run_all_tests(self):
        """Run all tests and generate report."""
        print("\n" + "="*60)
        print("🧪 AGENT MODE COMPREHENSIVE TESTS")
        print("="*60 + "\n")
        
        await self.setup()
        
        # Run all tests
        tests = [
            self.test_system_info(),
            self.test_cpu_info(),
            self.test_memory_info(),
            self.test_file_listing(),
            self.test_user_info(),
            self.test_hostname(),
            self.test_chat_mode_comparison()
        ]
        
        results = await asyncio.gather(*tests)
        self.results = results
        
        # Generate summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for r in self.results if r.get("passed", False))
        total = len(self.results)
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%\n")
        
        print("Detailed Results:")
        print("-" * 60)
        for i, result in enumerate(self.results, 1):
            status_icon = "✅" if result.get("passed", False) else "❌"
            print(f"{status_icon} Test {i}: {result['test']}")
            print(f"   Status: {result['status']}")
            if not result.get("passed", False):
                print(f"   Expected: {result.get('expected', 'N/A')}")
                actual = result.get('actual', 'N/A')
                if actual and isinstance(actual, str):
                    print(f"   Got: {actual[:100]}...")
                else:
                    print(f"   Got: {actual}")
            print()
        
        print("="*60)
        if passed == total:
            print("🎉 ALL TESTS PASSED! Agent mode is working correctly.")
        else:
            print(f"⚠️  {total - passed} test(s) failed. Review results above.")
        print("="*60 + "\n")

async def main():
    """Run test suite."""
    tester = AgentModeTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
