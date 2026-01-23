# Testes de Cenários de Chat - DuilioCode Studio

## 🎯 Objetivo
Validar diversos cenários de conversa que o usuário terá ao elaborar problemas e solicitar criação de arquivos.

---

## 📋 Cenários de Teste

### Cenário 1: Criação de Arquivo Simples
**Prompt do Usuário:**
```
Crie um arquivo chamado teste.js com um console.log("Hello World")
```

**Validações:**
- [ ] Arquivo criado no workspace atual
- [ ] Conteúdo correto
- [ ] Path normalizado corretamente
- [ ] Arquivo aparece no explorer
- [ ] Arquivo pode ser aberto no editor

---

### Cenário 2: Criação de Arquivo em Subpasta
**Prompt do Usuário:**
```
Crie um arquivo src/components/Button.jsx com um componente React básico
```

**Validações:**
- [ ] Pasta `src/components` criada se não existir
- [ ] Arquivo criado no local correto
- [ ] Código React válido
- [ ] Imports corretos
- [ ] Estrutura de pastas respeitada

---

### Cenário 3: Criação de Múltiplos Arquivos Relacionados
**Prompt do Usuário:**
```
Crie um sistema de autenticação com:
- src/auth/AuthService.js
- src/auth/AuthContext.jsx
- src/auth/useAuth.js
```

**Validações:**
- [ ] Todos os arquivos criados
- [ ] Imports entre arquivos corretos
- [ ] Estrutura consistente
- [ ] Código funcional e relacionado

---

### Cenário 4: Criação Baseada em Arquivo Existente
**Prompt do Usuário:**
```
Crie um componente UserCard.jsx similar ao ProductCard.jsx existente
```

**Validações:**
- [ ] AI analisa ProductCard.jsx
- [ ] Mantém padrão de estilo
- [ ] Usa mesmas dependências
- [ ] Estrutura similar
- [ ] Props adaptadas para User

---

### Cenário 5: Criação de Arquivo de Configuração
**Prompt do Usuário:**
```
Crie um package.json para um projeto Node.js com Express
```

**Validações:**
- [ ] package.json válido
- [ ] Dependências corretas
- [ ] Scripts apropriados
- [ ] Estrutura JSON válida

---

### Cenário 6: Criação de Arquivo Fora do Workspace
**Prompt do Usuário:**
```
Crie um arquivo no Desktop chamado backup.txt com a data atual
```

**Validações:**
- [ ] Path absoluto preservado
- [ ] Arquivo criado no Desktop
- [ ] Não duplica workspace path
- [ ] Conteúdo correto

---

### Cenário 7: Criação de Projeto Completo
**Prompt do Usuário:**
```
Crie um projeto React completo com:
- package.json
- src/App.jsx
- src/index.js
- public/index.html
- .gitignore
```

**Validações:**
- [ ] Todos os arquivos criados
- [ ] Estrutura de projeto válida
- [ ] Imports corretos
- [ ] Configurações apropriadas
- [ ] README se solicitado

---

### Cenário 8: Criação com Referência a Múltiplos Arquivos
**Prompt do Usuário:**
```
Crie um hook useProducts.js seguindo o padrão do useUsers.js e useOrders.js
```

**Validações:**
- [ ] Analisa ambos os arquivos de referência
- [ ] Mantém padrão consistente
- [ ] Adapta para Products
- [ ] Código funcional

---

### Cenário 9: Criação de Teste
**Prompt do Usuário:**
```
Crie testes unitários para a função calculateTotal em src/utils/calculations.js
```

**Validações:**
- [ ] Analisa arquivo de origem
- [ ] Cria arquivo de teste
- [ ] Testes completos
- [ ] Framework de teste correto (Jest/Vitest)
- [ ] Casos de teste adequados

---

### Cenário 10: Criação de Arquitetura
**Prompt do Usuário:**
```
Crie uma estrutura de Clean Architecture para um projeto Node.js
```

**Validações:**
- [ ] Camadas criadas (Domain, Application, Infrastructure, Presentation)
- [ ] Separação de responsabilidades
- [ ] Estrutura de pastas correta
- [ ] Arquivos de exemplo em cada camada

---

### Cenário 11: Criação com Path Relativo
**Prompt do Usuário:**
```
Crie um arquivo ./components/Header.jsx
```

**Validações:**
- [ ] Path relativo interpretado corretamente
- [ ] Criado em relação ao workspace
- [ ] Não duplica paths

---

### Cenário 12: Criação com Path Absoluto Dentro do Workspace
**Prompt do Usuário:**
```
Crie um arquivo /Users/username/projects/myapp/src/index.js
```

**Validações:**
- [ ] Path absoluto normalizado
- [ ] Workspace path não duplicado
- [ ] Arquivo criado no local correto

---

### Cenário 13: Criação de Pipeline CI/CD
**Prompt do Usuário:**
```
Crie um pipeline GitHub Actions para testes e deploy
```

**Validações:**
- [ ] .github/workflows criado
- [ ] YAML válido
- [ ] Jobs configurados
- [ ] Steps apropriados

---

### Cenário 14: Criação de Componente com TypeScript
**Prompt do Usuário:**
```
Crie um componente Button.tsx com TypeScript seguindo o padrão dos outros componentes
```

**Validações:**
- [ ] Analisa componentes TypeScript existentes
- [ ] Interfaces TypeScript corretas
- [ ] Props tipadas
- [ ] Estilos consistentes

---

### Cenário 15: Criação de Documentação
**Prompt do Usuário:**
```
Crie um README.md completo para o projeto
```

**Validações:**
- [ ] Markdown válido
- [ ] Seções apropriadas
- [ ] Informações relevantes
- [ ] Links funcionais

---

## ✅ Checklist de Validação Geral

Para cada cenário, verificar:

- [ ] **Análise do Codebase**: AI analisa código existente quando necessário?
- [ ] **Estrutura Respeitada**: Segue padrões do projeto?
- [ ] **Naming Conventions**: Nomes seguem convenções?
- [ ] **Coding Style**: Estilo de código consistente?
- [ ] **Dependências**: Usa dependências corretas?
- [ ] **Imports**: Imports corretos e organizados?
- [ ] **Documentação**: Código documentado quando necessário?
- [ ] **Path Handling**: Paths normalizados corretamente?
- [ ] **Multi-file**: Múltiplos arquivos criados corretamente?
- [ ] **Relacionamentos**: Dependências entre arquivos corretas?

---

## 🧪 Como Executar os Testes

1. Abra o DuilioCode Studio
2. Abra um workspace
3. Para cada cenário:
   - Envie o prompt no chat
   - Verifique as validações
   - Documente resultados
   - Capture screenshots se necessário

---

## 📊 Resultados Esperados

- ✅ **Sucesso**: Arquivo(s) criado(s) corretamente, código funcional, estrutura respeitada
- ⚠️ **Parcial**: Arquivo criado mas com problemas menores (estilo, imports, etc)
- ❌ **Falha**: Arquivo não criado ou criado incorretamente

---

**Última atualização**: 2024
**Status**: Em validação
