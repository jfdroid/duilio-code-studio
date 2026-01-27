#!/usr/bin/env python3
"""
Test: File Visibility Question
===============================
Tests the specific question: "voce consegue ver os arquivos do path?"
This test validates that the system correctly detects file listing intent
and provides file information even in Chat mode when workspace is available.
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8080"

async def test_file_visibility_question():
    """Test the exact question from the screenshot."""
    print("="*60)
    print("🧪 FILE VISIBILITY QUESTION TEST")
    print("="*60)
    print()
    
    # Get model
    async with httpx.AsyncClient(timeout=10.0) as client:
        models_resp = await client.get(f"{BASE_URL}/api/models")
        models = models_resp.json()['models']
        model = models[0]['name'] if models else 'qwen2.5-coder:14b'
        print(f"✅ Using model: {model}\n")
    
    # The exact question from the screenshot
    test_question = "voce consegue ver os arquivos do path?"
    
    print(f"Question: {test_question}")
    print("Expected: Should detect file listing intent and provide file information")
    print("⏳ Sending request to /api/chat...")
    print()
    
    start_time = datetime.now()
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Test in Chat mode (Agent mode endpoint but without explicit agent mode flag)
        payload = {
            "messages": [{"role": "user", "content": test_question}],
            "model": model,
            "temperature": 0.7,
            "stream": False,
            "workspace_path": "/Users/jeffersonsilva/Desktop"  # From screenshot
        }
        
        try:
            response = await client.post(f"{BASE_URL}/api/chat", json=payload)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                print(f"⏱️  Response time: {elapsed:.1f}s")
                print(f"Status Code: {response.status_code}")
                print()
                print("="*60)
                print("RESPONSE:")
                print("="*60)
                print(content)
                print("="*60)
                print()
                
                # Analyze response
                content_lower = content.lower()
                
                # Negative indicators (what we DON'T want)
                negative_phrases = [
                    "não tenho a capacidade",
                    "não posso acessar",
                    "não consigo ver",
                    "não tenho acesso",
                    "cannot access",
                    "do not have the ability",
                    "i cannot",
                    "i do not have"
                ]
                
                # Positive indicators (what we DO want)
                positive_phrases = [
                    "arquivos",
                    "files",
                    "lista",
                    "list",
                    "vejo",
                    "posso ver",
                    "consigo ver",
                    "i can see",
                    "here are",
                    "aqui estão"
                ]
                
                has_negative = any(phrase in content_lower for phrase in negative_phrases)
                has_positive = any(phrase in content_lower for phrase in positive_phrases)
                has_file_count = any(char.isdigit() for char in content[:200])
                has_file_list = '\n' in content or '-' in content or '*' in content
                
                # Result analysis
                print("="*60)
                print("ANALYSIS:")
                print("="*60)
                print(f"Contains negative phrases: {has_negative}")
                if has_negative:
                    found_negative = [p for p in negative_phrases if p in content_lower]
                    print(f"  Found: {', '.join(found_negative)}")
                
                print(f"Contains positive phrases: {has_positive}")
                if has_positive:
                    found_positive = [p for p in positive_phrases if p in content_lower]
                    print(f"  Found: {', '.join(found_positive)}")
                
                print(f"Has file count/numbers: {has_file_count}")
                print(f"Has file list format: {has_file_list}")
                print()
                
                # Determine result
                if has_negative and not has_positive:
                    result = "❌ FAILED - Response denies file access"
                elif has_positive and (has_file_count or has_file_list):
                    result = "✅ PASSED - Response provides file information"
                elif has_positive:
                    result = "⚠️  PARTIAL - Mentions files but no list/count"
                else:
                    result = "❌ FAILED - No clear file information"
                
                print("="*60)
                print(f"RESULT: {result}")
                print("="*60)
                
                return {
                    "question": test_question,
                    "status": result,
                    "response_time": elapsed,
                    "has_negative": has_negative,
                    "has_positive": has_positive,
                    "has_file_count": has_file_count,
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

async def test_variations():
    """Test variations of the file visibility question."""
    print("\n" + "="*60)
    print("🧪 TESTING QUESTION VARIATIONS")
    print("="*60)
    print()
    
    variations = [
        "voce consegue ver os arquivos do path?",
        "você consegue ver os arquivos do path?",
        "vc consegue ver os arquivos?",
        "voce ve os arquivos?",
        "você vê os arquivos?",
        "consegue ver arquivos?",
        "pode ver os arquivos?",
        "tem acesso aos arquivos?",
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        models_resp = await client.get(f"{BASE_URL}/api/models")
        model = models_resp.json()['models'][0]['name'] if models_resp.json()['models'] else 'qwen2.5-coder:14b'
    
    results = []
    
    for i, question in enumerate(variations, 1):
        print(f"Variation {i}/{len(variations)}: {question}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "messages": [{"role": "user", "content": question}],
                "model": model,
                "temperature": 0.7,
                "stream": False,
                "workspace_path": "/Users/jeffersonsilva/Desktop"
            }
            
            try:
                response = await client.post(f"{BASE_URL}/api/chat", json=payload)
                if response.status_code == 200:
                    content = response.json()['choices'][0]['message']['content']
                    content_lower = content.lower()
                    
                    has_negative = any(p in content_lower for p in ["não tenho", "cannot", "do not have"])
                    has_positive = any(p in content_lower for p in ["arquivos", "files", "posso", "consigo", "i can"])
                    
                    status = "✅" if has_positive and not has_negative else "❌"
                    print(f"  {status} Response: {content[:100]}...")
                    
                    results.append({
                        "question": question,
                        "status": status,
                        "has_negative": has_negative,
                        "has_positive": has_positive
                    })
                else:
                    print(f"  ❌ HTTP {response.status_code}")
                    results.append({"question": question, "status": "❌", "error": f"HTTP {response.status_code}"})
            except Exception as e:
                print(f"  ❌ Error: {str(e)[:50]}")
                results.append({"question": question, "status": "❌", "error": str(e)[:50]})
        
        print()
    
    print("="*60)
    print("VARIATIONS SUMMARY")
    print("="*60)
    passed = sum(1 for r in results if r.get('status') == '✅')
    print(f"Passed: {passed}/{len(variations)}")
    print()

if __name__ == "__main__":
    result = asyncio.run(test_file_visibility_question())
    asyncio.run(test_variations())
    
    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)
    if result.get('passed'):
        print("✅ TEST PASSED - System correctly handles file visibility questions")
    else:
        print("❌ TEST FAILED - System needs improvement")
        print("\nRecommendations:")
        print("1. Add more keywords to detect file visibility intent")
        print("2. Ensure file listing is provided even in Chat mode when workspace_path is available")
        print("3. Improve system prompt to explicitly tell AI it CAN see files")
    print("="*60)
