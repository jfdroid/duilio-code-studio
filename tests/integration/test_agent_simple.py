#!/usr/bin/env python3
"""
Simple Agent Mode Test
======================
Quick test to verify Agent mode is working with system info.
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8080"

async def test_agent_mode():
    """Test Agent mode with system info question."""
    print("="*60)
    print("🧪 AGENT MODE TEST")
    print("="*60)
    print()
    
    # Get model
    async with httpx.AsyncClient(timeout=10.0) as client:
        models_resp = await client.get(f"{BASE_URL}/api/models")
        models = models_resp.json()['models']
        model = models[0]['name'] if models else 'qwen2.5-coder:14b'
        print(f"✅ Using model: {model}\n")
    
    # Test questions
    test_cases = [
        {
            "name": "System OS",
            "question": "Qual é o sistema operacional da minha máquina?",
            "keywords": ["darwin", "macos", "mac", "sistema operacional"]
        },
        {
            "name": "CPU Info",
            "question": "Qual é o processador da minha máquina?",
            "keywords": ["cpu", "processador", "processor", "apple", "intel"]
        },
        {
            "name": "Memory Info",
            "question": "Quantos GB de RAM tem minha máquina?",
            "keywords": ["gb", "ram", "memória", "memory"]
        },
        {
            "name": "User Info",
            "question": "Qual é o nome do usuário desta máquina?",
            "keywords": ["jeffersonsilva", "user", "usuário"]
        }
    ]
    
    results = []
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        for i, test in enumerate(test_cases, 1):
            print(f"Test {i}/{len(test_cases)}: {test['name']}")
            print(f"Question: {test['question']}")
            print("⏳ Waiting for response (this may take 30-60 seconds)...")
            
            start_time = datetime.now()
            
            try:
                payload = {
                    "messages": [{"role": "user", "content": test['question']}],
                    "model": model,
                    "temperature": 0.7,
                    "stream": False
                }
                
                response = await client.post(f"{BASE_URL}/api/chat", json=payload)
                
                elapsed = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']
                    
                    # Check if response contains expected keywords
                    content_lower = content.lower()
                    found_keywords = [kw for kw in test['keywords'] if kw in content_lower]
                    
                    passed = len(found_keywords) > 0
                    status = "✅ PASSED" if passed else "❌ FAILED"
                    
                    print(f"⏱️  Response time: {elapsed:.1f}s")
                    print(f"Status: {status}")
                    print(f"Response (first 200 chars): {content[:200]}...")
                    if found_keywords:
                        print(f"✅ Found keywords: {', '.join(found_keywords)}")
                    print()
                    
                    results.append({
                        "test": test['name'],
                        "status": status,
                        "passed": passed,
                        "response_time": elapsed,
                        "keywords_found": found_keywords,
                        "response_preview": content[:200]
                    })
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                    print()
                    results.append({
                        "test": test['name'],
                        "status": f"❌ HTTP {response.status_code}",
                        "passed": False,
                        "error": response.text[:200]
                    })
                    
            except httpx.ReadTimeout:
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"❌ TIMEOUT after {elapsed:.1f}s")
                print()
                results.append({
                    "test": test['name'],
                    "status": "❌ TIMEOUT",
                    "passed": False,
                    "response_time": elapsed
                })
            except Exception as e:
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"❌ ERROR: {str(e)}")
                print()
                results.append({
                    "test": test['name'],
                    "status": f"❌ ERROR: {str(e)[:100]}",
                    "passed": False,
                    "response_time": elapsed
                })
    
    # Summary
    print("="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print()
    
    passed = sum(1 for r in results if r.get('passed', False))
    total = len(results)
    avg_time = sum(r.get('response_time', 0) for r in results) / total if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    print(f"Average Response Time: {avg_time:.1f}s")
    print()
    
    print("Detailed Results:")
    print("-" * 60)
    for result in results:
        status_icon = "✅" if result.get('passed', False) else "❌"
        print(f"{status_icon} {result['test']}: {result['status']}")
        if result.get('response_time'):
            print(f"   Time: {result['response_time']:.1f}s")
        if result.get('keywords_found'):
            print(f"   Keywords: {', '.join(result['keywords_found'])}")
        if result.get('response_preview'):
            print(f"   Preview: {result['response_preview']}...")
        print()
    
    print("="*60)
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {total - passed} test(s) failed.")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_agent_mode())
