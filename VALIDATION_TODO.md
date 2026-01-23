# DuilioCode Studio - Plano de Validação Completo

## 🎯 Objetivo
Validar sistematicamente todas as funcionalidades do DuilioCode Studio, especialmente a capacidade de criar projetos completos, arquiteturas, testes, pipelines e componentes através do chat/agent.

---

## ✅ Fase 1: Correção e Validação do Terminal

### 1.1 Terminal Básico
- [ ] **Namespace Fix**: Verificar se `window.__XTermJSClass` está sendo salvo corretamente
- [ ] **Criação de Terminal**: Testar se `Terminal.createNew()` funciona
- [ ] **Input Handler**: Verificar se `onKey` está capturando eventos corretamente
- [ ] **Foco do Terminal**: Garantir que terminal recebe foco ao clicar
- [ ] **Botão "+"**: Verificar se cria nova aba de terminal
- [ ] **Execução de Comandos**: Testar comandos básicos (ls, pwd, cd, clear)
- [ ] **Histórico**: Testar setas ↑/↓ para navegar histórico
- [ ] **Ctrl+C / Ctrl+L**: Testar atalhos de teclado

### 1.2 Terminal Avançado
- [ ] **Múltiplos Terminais**: Criar e alternar entre terminais
- [ ] **Resize**: Verificar se terminal se ajusta ao redimensionar painel
- [ ] **FitAddon**: Verificar se addon está funcionando
- [ ] **WebLinksAddon**: Verificar se links clicáveis funcionam

---

## 🏗️ Fase 2: Validação de Criação de Projetos

### 2.1 Projeto Simples
**Prompt**: "Crie um projeto Node.js simples com Express"
- [ ] Estrutura de diretórios criada corretamente
- [ ] `package.json` com dependências corretas
- [ ] `server.js` ou `index.js` com código funcional
- [ ] `.gitignore` apropriado
- [ ] `README.md` com instruções

### 2.2 Projeto React
**Prompt**: "Crie um projeto React com TypeScript e Vite"
- [ ] Configuração do Vite
- [ ] TypeScript configurado
- [ ] Estrutura de componentes
- [ ] `package.json` com scripts corretos
- [ ] Arquivos de configuração (tsconfig.json, etc)

### 2.3 Projeto Full-Stack
**Prompt**: "Crie um projeto full-stack com React frontend e Node.js backend"
- [ ] Separação clara entre frontend/backend
- [ ] Estrutura de pastas adequada
- [ ] Configurações de build
- [ ] Scripts de desenvolvimento

---

## 🏛️ Fase 3: Validação de Arquiteturas

### 3.1 Clean Architecture
**Prompt**: "Crie uma estrutura de Clean Architecture para um projeto Node.js"
- [ ] Camadas: Domain, Application, Infrastructure, Presentation
- [ ] Separação de responsabilidades
- [ ] Injeção de dependências
- [ ] Interfaces e contratos

### 3.2 MVC
**Prompt**: "Crie uma estrutura MVC para uma API REST"
- [ ] Models, Views (ou Responses), Controllers
- [ ] Rotas organizadas
- [ ] Middleware apropriado

### 3.3 Microservices
**Prompt**: "Crie uma estrutura de microserviços com 3 serviços"
- [ ] Separação de serviços
- [ ] Comunicação entre serviços
- [ ] Configurações independentes

---

## 🧩 Fase 4: Validação de Componentes

### 4.1 Componente Baseado em Referência
**Prompt**: "Crie um componente UserCard similar ao ProductCard existente"
- [ ] Analisa código existente
- [ ] Mantém padrão de estilo
- [ ] Usa mesmas dependências
- [ ] Estrutura similar

### 4.2 Componente com Props Tipadas
**Prompt**: "Crie um componente Button com TypeScript seguindo o padrão dos outros componentes"
- [ ] TypeScript interfaces
- [ ] Props tipadas
- [ ] Estilos consistentes

### 4.3 Componente Completo
**Prompt**: "Crie um componente de formulário de login completo"
- [ ] Validação
- [ ] Estados
- [ ] Estilos
- [ ] Integração com API

---

## 🧪 Fase 5: Validação de Testes

### 5.1 Testes Unitários
**Prompt**: "Crie testes unitários para a função calculateTotal"
- [ ] Jest/Vitest configurado
- [ ] Casos de teste completos
- [ ] Mocks quando necessário

### 5.2 Testes de Integração
**Prompt**: "Crie testes de integração para a API de usuários"
- [ ] Setup de banco de dados de teste
- [ ] Testes de endpoints
- [ ] Limpeza após testes

### 5.3 Testes E2E
**Prompt**: "Configure testes E2E com Playwright"
- [ ] Configuração do Playwright
- [ ] Testes de fluxos completos
- [ ] Screenshots em falhas

---

## 🔄 Fase 6: Validação de Pipelines CI/CD

### 6.1 GitHub Actions
**Prompt**: "Crie um pipeline CI/CD com GitHub Actions"
- [ ] Workflow de testes
- [ ] Build e deploy
- [ ] Notificações

### 6.2 GitLab CI
**Prompt**: "Crie um pipeline GitLab CI para o projeto"
- [ ] `.gitlab-ci.yml` configurado
- [ ] Stages apropriados
- [ ] Cache de dependências

### 6.3 Docker
**Prompt**: "Crie Dockerfile e docker-compose para o projeto"
- [ ] Dockerfile otimizado
- [ ] docker-compose.yml
- [ ] Multi-stage builds quando apropriado

---

## 📋 Fase 7: Validação de Metodologias

### 7.1 Estrutura Agile
**Prompt**: "Crie estrutura de documentação para metodologia Agile"
- [ ] User Stories
- [ ] Sprint Planning
- [ ] Retrospectivas

### 7.2 Documentação de Projeto
**Prompt**: "Crie documentação completa do projeto"
- [ ] README detalhado
- [ ] CONTRIBUTING.md
- [ ] CHANGELOG.md
- [ ] Arquitetura documentada

---

## 🛠️ Fase 8: Validação de Instalação de Ferramentas

### 8.1 Dependências
**Prompt**: "Instale e configure ESLint e Prettier"
- [ ] Configurações criadas
- [ ] Scripts no package.json
- [ ] Integração com editor

### 8.2 Ferramentas de Build
**Prompt**: "Configure Webpack para o projeto"
- [ ] webpack.config.js
- [ ] Loaders apropriados
- [ ] Plugins necessários

---

## 📁 Fase 9: Validação de Paths e Estrutura

### 9.1 Paths Relativos
- [ ] Arquivos dentro do workspace
- [ ] Paths relativos corretos
- [ ] Imports funcionando

### 9.2 Paths Absolutos
- [ ] Arquivos fora do workspace (Desktop, etc)
- [ ] Paths absolutos preservados
- [ ] Criação em locais externos

### 9.3 Paths Especiais
- [ ] Paths com `~` (home directory)
- [ ] Paths com `..` (parent directory)
- [ ] Paths com espaços ou caracteres especiais

---

## 🔗 Fase 10: Validação de Múltiplos Arquivos

### 10.1 Arquivos Relacionados
**Prompt**: "Crie um sistema de autenticação completo"
- [ ] Múltiplos arquivos criados
- [ ] Dependências entre arquivos
- [ ] Imports corretos

### 10.2 Estrutura Completa
**Prompt**: "Crie uma aplicação CRUD completa"
- [ ] Models, Controllers, Routes
- [ ] Todos os arquivos relacionados
- [ ] Estrutura consistente

---

## 📊 Checklist de Validação por Cenário

Para cada teste acima, verificar:

- [ ] **Análise do Codebase**: AI analisa código existente?
- [ ] **Estrutura Respeitada**: Segue padrões do projeto?
- [ ] **Naming Conventions**: Nomes seguem convenções?
- [ ] **Coding Style**: Estilo de código consistente?
- [ ] **Dependências**: Usa dependências corretas?
- [ ] **Imports**: Imports corretos e organizados?
- [ ] **Documentação**: Código documentado quando necessário?
- [ ] **Testes**: Testes criados quando apropriado?
- [ ] **Configurações**: Arquivos de config criados?
- [ ] **README**: Documentação atualizada?

---

## 🚀 Ordem de Execução Recomendada

1. **Fase 1** (Terminal) - CRÍTICO
2. **Fase 9** (Paths) - Básico
3. **Fase 2** (Projetos Simples) - Validação básica
4. **Fase 4** (Componentes) - Validação de referências
5. **Fase 10** (Múltiplos Arquivos) - Validação avançada
6. **Fase 3** (Arquiteturas) - Validação complexa
7. **Fase 5** (Testes) - Validação de qualidade
8. **Fase 6** (Pipelines) - Validação de DevOps
9. **Fase 7** (Metodologias) - Validação de processos
10. **Fase 8** (Ferramentas) - Validação de setup

---

## 📝 Notas de Teste

Para cada teste, documentar:
- **Prompt usado**: Texto exato enviado
- **Resultado esperado**: O que deveria acontecer
- **Resultado obtido**: O que realmente aconteceu
- **Problemas encontrados**: Issues identificados
- **Screenshots/Logs**: Evidências

---

## ✅ Critérios de Sucesso

Um cenário é considerado **válido** quando:
1. ✅ Todos os arquivos são criados corretamente
2. ✅ Estrutura segue padrões do projeto
3. ✅ Código é funcional e segue boas práticas
4. ✅ Imports e dependências estão corretos
5. ✅ Documentação está presente quando necessário
6. ✅ AI demonstra compreensão do contexto

---

**Última atualização**: 2024
**Status**: Em validação
