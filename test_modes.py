#!/usr/bin/env python3
"""
Test Chat and Agent Modes
==========================
Tests both simple (Chat) and complex (Agent) endpoints
"""

import asyncio
import httpx
import json

BASE_URL = "http://127.0.0.1:8080"

async def test_chat_mode():
    """Test Chat mode - simple endpoint"""
    print("\n" + "="*60)
    print("TESTING CHAT MODE (Simple Endpoint)")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test simple question
        payload = {
            "messages": [
                {"role": "user", "content": "Olá! Quantos arquivos você vê?"}
            ],
            "model": None,
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
            
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Model: {result.get('model', 'N/A')}")
            
            if result.get('choices') and result['choices'][0].get('message'):
                content = result['choices'][0]['message']['content']
                print(f"✅ Response length: {len(content)} chars")
                print(f"\n📝 Response preview:\n{content[:200]}...")
            else:
                print("❌ Unexpected response format")
                print(json.dumps(result, indent=2))
                
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_agent_mode():
    """Test Agent mode - complex endpoint"""
    print("\n" + "="*60)
    print("TESTING AGENT MODE (Complex Endpoint)")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test with workspace path
        payload = {
            "messages": [
                {"role": "user", "content": "Quantos arquivos tem no codebase? Liste cada um com nome e tipo."}
            ],
            "model": None,
            "temperature": 0.7,
            "stream": False,
            "workspace_path": None  # Will use default from workspace service
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/chat",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Status: {response.status_code}")
            print(f"✅ Model: {result.get('model', 'N/A')}")
            print(f"✅ Actions processed: {result.get('actions_processed', False)}")
            print(f"✅ Refresh explorer: {result.get('refresh_explorer', False)}")
            
            if result.get('choices') and result['choices'][0].get('message'):
                content = result['choices'][0]['message']['content']
                print(f"✅ Response length: {len(content)} chars")
                print(f"\n📝 Response preview:\n{content[:300]}...")
            else:
                print("❌ Unexpected response format")
                print(json.dumps(result, indent=2))
                
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    """Run all tests"""
    print("\n🧪 Testing DuilioCode Modes")
    print("="*60)
    
    # Test Chat mode (simple)
    await test_chat_mode()
    
    # Test Agent mode (complex)
    await test_agent_mode()
    
    print("\n" + "="*60)
    print("✅ Tests completed!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
