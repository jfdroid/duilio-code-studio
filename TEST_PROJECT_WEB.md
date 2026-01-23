# Teste Prático - Projeto Web Simples

## 🎯 Objetivo
Criar um projeto web simples usando o DuilioCode Studio para validar:
- Criação de arquivos via chat
- Entendimento de contexto
- Estrutura de projeto
- Execução de testes

---

## 📋 Projeto: Todo List App

Vamos criar uma aplicação web simples de lista de tarefas (Todo List) com:
- HTML/CSS/JavaScript vanilla
- Estrutura organizada
- Funcionalidades básicas
- Testes simples

---

## 🧪 Fluxos de Teste

### Teste 1: Criar Estrutura Base do Projeto

**Prompt:**
```
Crie um projeto web simples de Todo List com a seguinte estrutura:
- index.html (página principal)
- styles.css (estilos)
- app.js (lógica da aplicação)
- README.md (documentação)

O projeto deve ter uma interface limpa e moderna.
```

**Validações:**
- [ ] Estrutura de pastas criada
- [ ] index.html criado com estrutura HTML5 válida
- [ ] styles.css criado com estilos modernos
- [ ] app.js criado com lógica básica
- [ ] README.md criado com instruções

---

### Teste 2: Implementar Funcionalidades Básicas

**Prompt:**
```
Implemente as funcionalidades básicas do Todo List:
- Adicionar tarefa
- Marcar como concluída
- Remover tarefa
- Contador de tarefas pendentes

Atualize o app.js com essas funcionalidades.
```

**Validações:**
- [ ] Função de adicionar tarefa implementada
- [ ] Função de marcar como concluída
- [ ] Função de remover tarefa
- [ ] Contador de tarefas pendentes
- [ ] Código funcional e bem estruturado

---

### Teste 3: Melhorar Estilos

**Prompt:**
```
Melhore os estilos do Todo List:
- Use um tema dark moderno
- Adicione animações suaves
- Torne responsivo para mobile
- Adicione hover effects nos botões
```

**Validações:**
- [ ] Tema dark aplicado
- [ ] Animações implementadas
- [ ] Responsivo (media queries)
- [ ] Hover effects funcionando
- [ ] Visual moderno e profissional

---

### Teste 4: Adicionar Persistência Local

**Prompt:**
```
Adicione persistência local usando localStorage:
- Salvar tarefas quando adicionadas/modificadas
- Carregar tarefas ao abrir a página
- Limpar tarefas concluídas
```

**Validações:**
- [ ] localStorage implementado
- [ ] Tarefas persistem após refresh
- [ ] Carregamento automático ao abrir
- [ ] Limpeza de tarefas concluídas funciona

---

### Teste 5: Criar Testes Básicos

**Prompt:**
```
Crie testes básicos para o Todo List:
- test/todo.test.js com testes usando um framework simples
- Teste adicionar tarefa
- Teste marcar como concluída
- Teste remover tarefa
```

**Validações:**
- [ ] Arquivo de teste criado
- [ ] Testes para adicionar tarefa
- [ ] Testes para marcar como concluída
- [ ] Testes para remover tarefa
- [ ] Testes executáveis

---

### Teste 6: Adicionar Funcionalidade de Filtros

**Prompt:**
```
Adicione filtros para as tarefas:
- Mostrar todas
- Mostrar apenas pendentes
- Mostrar apenas concluídas

Crie um arquivo filters.js para essa funcionalidade.
```

**Validações:**
- [ ] filters.js criado
- [ ] Filtro "todas" funciona
- [ ] Filtro "pendentes" funciona
- [ ] Filtro "concluídas" funciona
- [ ] Integração com app.js correta

---

### Teste 7: Melhorar README

**Prompt:**
```
Melhore o README.md com:
- Descrição completa do projeto
- Instruções de instalação/uso
- Lista de funcionalidades
- Screenshots (se possível)
- Tecnologias usadas
```

**Validações:**
- [ ] Descrição completa
- [ ] Instruções claras
- [ ] Lista de funcionalidades
- [ ] Tecnologias documentadas
- [ ] Formatação Markdown correta

---

### Teste 8: Adicionar Validação de Input

**Prompt:**
```
Adicione validação para o input de tarefas:
- Não permitir tarefas vazias
- Limitar tamanho máximo (ex: 200 caracteres)
- Mostrar mensagens de erro apropriadas

Atualize o app.js com essas validações.
```

**Validações:**
- [ ] Validação de tarefa vazia
- [ ] Limite de caracteres implementado
- [ ] Mensagens de erro exibidas
- [ ] UX amigável

---

### Teste 9: Criar Arquivo de Configuração

**Prompt:**
```
Crie um arquivo config.js para centralizar configurações:
- Tamanho máximo de tarefa
- Tema (dark/light)
- Idioma
- Outras configurações
```

**Validações:**
- [ ] config.js criado
- [ ] Configurações centralizadas
- [ ] Fácil de modificar
- [ ] Integrado com app.js

---

### Teste 10: Adicionar Funcionalidade de Edição

**Prompt:**
```
Adicione a funcionalidade de editar tarefas existentes:
- Duplo clique para editar
- Salvar ao pressionar Enter
- Cancelar com Escape
- Atualizar no localStorage
```

**Validações:**
- [ ] Edição por duplo clique
- [ ] Salvar com Enter
- [ ] Cancelar com Escape
- [ ] Persistência no localStorage
- [ ] UX intuitiva

---

## ✅ Checklist de Validação Geral

Para cada teste, verificar:

- [ ] **Arquivo Criado**: Arquivo foi criado no local correto?
- [ ] **Estrutura**: Estrutura de código está correta?
- [ ] **Funcionalidade**: Código funciona como esperado?
- [ ] **Integração**: Integra corretamente com outros arquivos?
- [ ] **Estilo**: Segue padrões do projeto?
- [ ] **Comentários**: Código está documentado?
- [ ] **Sem Erros**: Não há erros de sintaxe?
- [ ] **Contexto**: AI entendeu o contexto do projeto?

---

## 📊 Resultados Esperados

### Estrutura Final do Projeto:
```
todo-list-app/
├── index.html
├── styles.css
├── app.js
├── filters.js
├── config.js
├── test/
│   └── todo.test.js
└── README.md
```

### Funcionalidades Esperadas:
- ✅ Adicionar tarefas
- ✅ Marcar como concluída
- ✅ Remover tarefas
- ✅ Filtrar tarefas
- ✅ Editar tarefas
- ✅ Persistência local
- ✅ Validação de input
- ✅ Contador de pendentes
- ✅ Tema dark moderno
- ✅ Responsivo

---

## 🚀 Como Executar os Testes

1. Abra o DuilioCode Studio
2. Crie/abra um workspace (ex: `~/Desktop/todo-list-app`)
3. Para cada teste:
   - Envie o prompt no chat
   - Aguarde a criação dos arquivos
   - Verifique as validações
   - Teste manualmente se possível
   - Documente resultados

---

## 📝 Notas de Teste

**Data:** [Data do teste]
**Workspace:** [Caminho do workspace]
**Resultado Geral:** [✅ Sucesso / ⚠️ Parcial / ❌ Falha]

**Observações:**
- [Anotar problemas encontrados]
- [Anotar melhorias necessárias]
- [Anotar funcionalidades que funcionaram bem]

---

**Última atualização**: 2024
**Status**: Pronto para teste
