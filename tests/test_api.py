"""
DuilioCode Studio - API Tests
Tests for all backend API endpoints
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestHealthEndpoints:
    """Health check endpoint tests"""
    
    def test_health_basic(self, client):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data
    
    def test_health_full(self, client):
        """Test full health check with Ollama status"""
        response = client.get("/health/full")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "ollama" in data
        assert "features" in data


class TestWorkspaceEndpoints:
    """Workspace management endpoint tests"""
    
    def test_get_workspace(self, client):
        """Test getting current workspace"""
        response = client.get("/api/workspace")
        assert response.status_code == 200
        data = response.json()
        assert "path" in data
        assert "home_directory" in data
        assert "exists" in data
    
    def test_set_workspace_valid(self, client):
        """Test setting workspace to valid path"""
        response = client.post("/api/workspace", json={"path": "/tmp"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_set_workspace_invalid(self, client):
        """Test setting workspace to invalid path"""
        response = client.post("/api/workspace", json={"path": "/nonexistent/path/xyz"})
        assert response.status_code == 400
    
    def test_workspace_tree(self, client):
        """Test getting workspace tree"""
        response = client.get("/api/workspace/tree?path=/tmp&depth=2")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "path" in data


class TestFileEndpoints:
    """File operations endpoint tests"""
    
    def test_list_directory(self, client):
        """Test listing directory contents"""
        response = client.get("/api/files/list?path=/tmp")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_list_directory_invalid(self, client):
        """Test listing invalid directory"""
        response = client.get("/api/files/list?path=/nonexistent/path")
        # API returns 404 for non-existent paths
        assert response.status_code in [400, 404]
    
    def test_read_file_invalid(self, client):
        """Test reading non-existent file"""
        response = client.get("/api/files/read?path=/nonexistent/file.txt")
        # API returns 404 for non-existent files
        assert response.status_code in [400, 404]
    
    def test_autocomplete(self, client):
        """Test path autocomplete"""
        response = client.get("/api/files/autocomplete?partial=/tmp")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
    
    def test_create_and_delete_file(self, client):
        """Test creating and deleting a file"""
        test_path = "/tmp/duiliocode_test_file.txt"
        
        # Create file using write endpoint (create might not exist)
        response = client.post("/api/files/write", json={
            "path": test_path,
            "content": "test content"
        })
        assert response.status_code == 200
        
        # Verify file exists by reading it
        response = client.get(f"/api/files/read?path={test_path}")
        assert response.status_code == 200
        assert response.json()["content"] == "test content"
        
        # Delete file
        response = client.post("/api/files/delete", json={"path": test_path})
        assert response.status_code == 200
    
    def test_write_file(self, client):
        """Test writing to a file"""
        test_path = "/tmp/duiliocode_write_test.txt"
        
        # Write content
        response = client.post("/api/files/write", json={
            "path": test_path,
            "content": "initial content"
        })
        assert response.status_code == 200
        
        # Verify content
        response = client.get(f"/api/files/read?path={test_path}")
        assert response.json()["content"] == "initial content"
        
        # Write new content
        response = client.post("/api/files/write", json={
            "path": test_path,
            "content": "updated content"
        })
        assert response.status_code == 200
        
        # Verify updated content
        response = client.get(f"/api/files/read?path={test_path}")
        assert response.json()["content"] == "updated content"
        
        # Cleanup
        client.post("/api/files/delete", json={"path": test_path})


class TestModelsEndpoint:
    """AI Models endpoint tests"""
    
    def test_list_models(self, client):
        """Test listing available models"""
        response = client.get("/api/models")
        # Models endpoint might return 503 if Ollama is not running
        # In production, it should return 200
        if response.status_code == 200:
            data = response.json()
            assert "models" in data
            assert isinstance(data["models"], list)
        else:
            # Accept 503 if Ollama is not available in test environment
            assert response.status_code == 503


class TestGenerateEndpoint:
    """AI Generation endpoint tests"""
    
    def test_generate_requires_prompt(self, client):
        """Test that generate requires a prompt"""
        response = client.post("/api/generate", json={})
        assert response.status_code == 422  # Validation error
    
    def test_generate_basic(self, client):
        """Test basic generation (may take time)"""
        response = client.post("/api/generate", json={
            "prompt": "Say 'test' only",
            "model": "qwen2.5-coder:14b"
        })
        # This test may fail if Ollama is not running
        # In CI, we'd mock this
        if response.status_code == 200:
            data = response.json()
            assert "response" in data


class TestChatEndpoint:
    """Chat endpoint tests"""
    
    def test_chat_requires_messages(self, client):
        """Test that chat requires messages"""
        response = client.post("/api/chat", json={})
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
