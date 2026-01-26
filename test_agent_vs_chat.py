#!/usr/bin/env python3
"""
Test Agent vs Chat Mode Differences
====================================
Tests that Agent mode has system info and Chat mode doesn't
"""

import asyncio
import httpx
import json

BASE_URL = "http://127.0.0.1:8080"

async def test_chat_mode():
    """Test Chat mode - should NOT have system info"""
    print("\n" + "="*60)
    print("TESTING CHAT MODE (Simple - NO system info)")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get models
        models_response = await client.get(f"{BASE_URL}/api/models")
        models_data = models_response.json()
        model = models_data.get('models', [{}])[0].get('name', 'qwen2.5-coder:14b')
        
        payload = {
            "messages": [
                {"role": "user", "content": "Qual é o sistema operacional da minha máquina?"}
            ],
            "model": model,
            "temperature": 0.7,
            "stream": False
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/chat/simple",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            content = result['choices'][0]['message']['content']
            print(f"✅ Response (should NOT know system info):")
            print(f"{content[:300]}...")
            
            # Check if it says it doesn't know (expected for Chat mode)
            if "não sei" in content.lower() or "don't know" in content.lower() or "cannot" in content.lower():
                print("✅ CORRECT: Chat mode doesn't have system info")
            else:
                print("⚠️  WARNING: Chat mode might have system info (unexpected)")
                
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_agent_mode():
    """Test Agent mode - SHOULD have system info"""
    print("\n" + "="*60)
    print("TESTING AGENT MODE (Complex - WITH system info)")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get models
        models_response = await client.get(f"{BASE_URL}/api/models")
        models_data = models_response.json()
        model = models_data.get('models', [{}])[0].get('name', 'qwen2.5-coder:14b')
        
        payload = {
            "messages": [
                {"role": "user", "content": "Qual é o sistema operacional da minha máquina?"}
            ],
            "model": model,
            "temperature": 0.7,
            "stream": False,
            "workspace_path": None
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/chat",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            content = result['choices'][0]['message']['content']
            print(f"✅ Response (SHOULD know system info):")
            print(f"{content[:400]}...")
            
            # Check if it mentions system info
            system_keywords = ['darwin', 'macos', 'mac', 'linux', 'windows', 'sistema operacional', 'operating system']
            has_system_info = any(kw in content.lower() for kw in system_keywords)
            
            if has_system_info:
                print("✅ CORRECT: Agent mode has system info and can answer!")
            else:
                print("⚠️  WARNING: Agent mode might not have system info")
                
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    """Run all tests"""
    print("\n🧪 Testing Agent vs Chat Mode Differences")
    print("="*60)
    
    await test_chat_mode()
    await test_agent_mode()
    
    print("\n" + "="*60)
    print("✅ Tests completed!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
