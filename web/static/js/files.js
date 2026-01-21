/**
 * DuilioCode Studio - File Manager Module
 * File operations: open, save, create, delete
 */

const FileManager = {
    /**
     * Open a file
     */
    async open(path) {
        try {
            const data = await API.readFile(path);
            
            AppState.setCurrentFile({
                path: data.path,
                content: data.content,
                language: data.language
            });
            
            // Store original content for diff
            AppState.editor.originalContent = data.content;
            if (typeof DiffViewer !== 'undefined') {
                DiffViewer.setOriginal(data.content);
                DiffViewer.isActive = false;
                DiffViewer.hide();
                const toggleBtn = document.getElementById('diffToggleBtn');
                if (toggleBtn) toggleBtn.classList.remove('active');
            }
            
            // Add tab
            Tabs.add(path, data.language);
            
            // Show editor
            document.getElementById('welcomeScreen').style.display = 'none';
            document.getElementById('fileEditorContainer').style.display = 'flex';
            document.getElementById('editorPath').textContent = Utils.shortenPath(path);
            document.getElementById('fileLanguage').textContent = data.language;
            
            // Use Monaco Editor if available, fallback to textarea
            if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
                MonacoEditor.setContent(data.content, data.language);
            } else if (typeof MonacoEditor !== 'undefined' && !MonacoEditor.isReady) {
                // Monaco is loading, queue the content
                MonacoEditor.pendingContent = data.content;
                MonacoEditor.pendingLanguage = data.language;
            } else {
                // Fallback to textarea
                document.getElementById('codeEditor').value = data.content;
            }
            
            // Highlight in tree
            document.querySelectorAll('.tree-item').forEach(el => el.classList.remove('selected'));
            const treeItem = document.querySelector(`.tree-item[data-path="${path}"]`);
            if (treeItem) treeItem.classList.add('selected');
            
        } catch (error) {
            alert('Error opening file: ' + error.message);
        }
    },
    
    /**
     * Save current file
     */
    async save() {
        const file = AppState.editor.currentFile;
        if (!file) return;
        
        // Get content from Monaco or fallback textarea
        let content;
        if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
            content = MonacoEditor.getContent();
        } else {
            content = document.getElementById('codeEditor').value;
        }
        
        try {
            await API.writeFile(file.path, content);
            AppState.editor.originalContent = content;
            
            // Update Monaco's original content tracking
            if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
                MonacoEditor.originalContent = content;
            }
            
            // Remove modified indicator from tab
            const tab = document.querySelector(`.tab[data-path="${file.path}"]`);
            if (tab) tab.classList.remove('modified');
            
            Utils.showNotification('File saved successfully!', 'success');
        } catch (error) {
            alert('Error saving file: ' + error.message);
        }
    },
    
    /**
     * Revert to original content
     */
    revert() {
        if (AppState.editor.currentFile && AppState.editor.originalContent) {
            if (typeof MonacoEditor !== 'undefined' && MonacoEditor.isReady) {
                MonacoEditor.setContent(AppState.editor.originalContent, AppState.editor.currentFile.language);
            } else {
                document.getElementById('codeEditor').value = AppState.editor.originalContent;
            }
            
            // Remove modified indicator
            const tab = document.querySelector(`.tab[data-path="${AppState.editor.currentFile.path}"]`);
            if (tab) tab.classList.remove('modified');
            
            Utils.showNotification('Reverted to original', 'info');
        }
    },
    
    /**
     * Create new file modal
     */
    createNew(inPath = null) {
        document.getElementById('newFileModalTitle').textContent = '📄 New File';
        document.getElementById('newFileName').value = '';
        document.getElementById('newFileName').dataset.isDir = 'false';
        document.getElementById('newFileName').dataset.basePath = inPath || AppState.workspace.currentPath || '';
        document.getElementById('newFileModal').classList.add('active');
        setTimeout(() => document.getElementById('newFileName').focus(), 100);
    },
    
    /**
     * Create new folder modal
     */
    createNewFolder(inPath = null) {
        document.getElementById('newFileModalTitle').textContent = '📁 New Folder';
        document.getElementById('newFileName').value = '';
        document.getElementById('newFileName').dataset.isDir = 'true';
        document.getElementById('newFileName').dataset.basePath = inPath || AppState.workspace.currentPath || '';
        document.getElementById('newFileModal').classList.add('active');
        setTimeout(() => document.getElementById('newFileName').focus(), 100);
    },
    
    /**
     * Create in specific folder
     */
    createInFolder(path) {
        this.createNew(path);
    },
    
    /**
     * Confirm file/folder creation
     */
    async confirmCreate() {
        const input = document.getElementById('newFileName');
        const name = input.value.trim();
        const isDir = input.dataset.isDir === 'true';
        const basePath = input.dataset.basePath;
        
        if (!name) {
            alert('Please enter a name');
            return;
        }
        
        const fullPath = basePath ? `${basePath}/${name}` : name;
        
        try {
            await API.createFile(fullPath, isDir, '');
            this.closeModal();
            await Workspace.refresh();
            
            if (!isDir) {
                this.open(fullPath);
            }
        } catch (error) {
            alert('Error creating: ' + error.message);
        }
    },
    
    /**
     * Close new file modal
     */
    closeModal() {
        document.getElementById('newFileModal').classList.remove('active');
    },
    
    /**
     * Delete file or folder
     */
    async delete(path) {
        if (!confirm(`Are you sure you want to delete "${path}"?`)) return;
        
        try {
            await API.deleteFile(path);
            await Workspace.refresh();
            
            // Close tab if open
            if (AppState.editor.currentFile && AppState.editor.currentFile.path === path) {
                Tabs.close(path);
            }
        } catch (error) {
            alert('Error deleting: ' + error.message);
        }
    }
};
