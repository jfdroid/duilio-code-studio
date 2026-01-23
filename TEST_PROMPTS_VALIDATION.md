# Lista de Testes de Prompts - Validação DuilioCode Studio

## 🎯 Objetivo
Validar os principais fluxos de uso do DuilioCode Studio através de prompts de teste que cobrem todos os cenários críticos.

---

## 📋 Categorias de Testes

### 1. Criar Arquivo Simples

#### Teste 1.1: Arquivo Único Básico
**Prompt:**
```
Crie um arquivo chamado utils.js com funções auxiliares para manipulação de strings.
```

**Validações:**
- [ ] Arquivo `utils.js` foi criado
- [ ] Conteúdo contém funções de manipulação de strings
- [ ] Código está funcional e bem estruturado
- [ ] Path está correto (relativo ao workspace)

---

#### Teste 1.2: Arquivo com Estrutura Específica
**Prompt:**
```
Crie um arquivo config.json com as seguintes configurações:
- apiUrl: "https://api.example.com"
- timeout: 5000
- retries: 3
```

**Validações:**
- [ ] Arquivo `config.json` criado
- [ ] JSON válido
- [ ] Todas as propriedades presentes
- [ ] Valores corretos

---

#### Teste 1.3: Arquivo em Subdiretório
**Prompt:**
```
Crie um arquivo src/components/Button.jsx com um componente React de botão.
```

**Validações:**
- [ ] Diretório `src/components/` criado se não existir
- [ ] Arquivo `Button.jsx` criado no local correto
- [ ] Componente React funcional
- [ ] Imports corretos

---

### 2. Modificar Arquivo Existente

#### Teste 2.1: Adicionar Função
**Prompt:**
```
Adicione uma função chamada formatDate no arquivo utils.js que formata datas no formato DD/MM/YYYY.
```

**Validações:**
- [ ] Arquivo `utils.js` existe
- [ ] Função `formatDate` adicionada
- [ ] Código existente não foi removido
- [ ] Formato de data correto

---

#### Teste 2.2: Corrigir Bug
**Prompt:**
```
Corrija o bug no arquivo app.js na função calculateTotal que está retornando NaN.
```

**Validações:**
- [ ] Bug identificado e corrigido
- [ ] Função retorna valor correto
- [ ] Código existente preservado
- [ ] Sem erros de sintaxe

---

#### Teste 2.3: Refatorar Código
**Prompt:**
```
Refatore o arquivo userService.js aplicando os princípios SOLID, especialmente Single Responsibility.
```

**Validações:**
- [ ] Código refatorado seguindo SOLID
- [ ] Responsabilidades separadas
- [ ] Funcionalidade preservada
- [ ] Código mais limpo e organizado

---

### 3. Criar Pasta/Diretório

#### Teste 3.1: Pasta Simples
**Prompt:**
```
Crie uma pasta chamada tests para armazenar os testes do projeto.
```

**Validações:**
- [ ] Pasta `tests/` criada
- [ ] Estrutura de diretório correta
- [ ] Pode criar arquivos dentro

---

#### Teste 3.2: Estrutura de Pastas Completa
**Prompt:**
```
Crie a estrutura de pastas para um projeto React:
- src/components
- src/hooks
- src/utils
- src/services
- public
```

**Validações:**
- [ ] Todas as pastas criadas
- [ ] Estrutura hierárquica correta
- [ ] Nomes corretos

---

### 4. Criar Aplicativo Android

#### Teste 4.1: Projeto Android Básico
**Prompt:**
```
Crie um projeto Android completo com:
- Estrutura de pastas Kotlin
- MainActivity.kt
- activity_main.xml
- AndroidManifest.xml
- build.gradle.kts
- README.md com instruções
```

**Validações:**
- [ ] Estrutura de projeto Android criada
- [ ] Todos os arquivos essenciais presentes
- [ ] MainActivity funcional
- [ ] Build configurado corretamente
- [ ] README com instruções

---

#### Teste 4.2: App Android com Clean Architecture
**Prompt:**
```
Crie um aplicativo Android seguindo Clean Architecture:
- Estrutura de camadas (data, domain, presentation)
- Use cases
- Repositórios
- ViewModels
- Dependências configuradas
```

**Validações:**
- [ ] Estrutura Clean Architecture implementada
- [ ] Separação de camadas correta
- [ ] Use cases criados
- [ ] Repositórios implementados
- [ ] ViewModels configurados
- [ ] Dependências no build.gradle

---

### 5. Criar Aplicativo Web

#### Teste 5.1: Projeto Web Simples (HTML/CSS/JS)
**Prompt:**
```
Crie um aplicativo web completo de Todo List com:
- index.html (estrutura HTML5)
- styles.css (tema dark moderno)
- app.js (lógica completa)
- README.md (documentação)
```

**Validações:**
- [ ] Todos os arquivos criados
- [ ] HTML válido e semântico
- [ ] CSS com tema dark
- [ ] JavaScript funcional
- [ ] README completo

---

#### Teste 5.2: Projeto React Completo
**Prompt:**
```
Crie um projeto React completo com:
- package.json com dependências
- src/App.jsx
- src/components/Header.jsx
- src/components/Footer.jsx
- src/index.js
- public/index.html
- README.md
```

**Validações:**
- [ ] Estrutura React criada
- [ ] package.json configurado
- [ ] Componentes criados
- [ ] Imports/exports corretos
- [ ] README com instruções

---

#### Teste 5.3: API REST com Node.js/Express
**Prompt:**
```
Crie uma API REST completa com Express.js:
- Estrutura de pastas (routes, controllers, models, middleware)
- Rotas CRUD para usuários
- Middleware de autenticação
- package.json
- .env.example
- README.md
```

**Validações:**
- [ ] Estrutura de API criada
- [ ] Rotas CRUD implementadas
- [ ] Middleware configurado
- [ ] package.json correto
- [ ] README com documentação da API

---

### 6. Criar e Formatat Emails e Mensagens

#### Teste 6.1: Email HTML
**Prompt:**
```
Crie um template de email HTML profissional para confirmação de cadastro com:
- Header com logo
- Corpo com mensagem de boas-vindas
- Footer com links sociais
- Estilos inline para compatibilidade
```

**Validações:**
- [ ] Arquivo HTML criado
- [ ] Template profissional
- [ ] Estilos inline
- [ ] Estrutura semântica
- [ ] Compatível com clientes de email

---

#### Teste 6.2: Mensagem de Notificação
**Prompt:**
```
Crie um arquivo notificationTemplates.js com templates de mensagens:
- Sucesso
- Erro
- Aviso
- Informação
```

**Validações:**
- [ ] Arquivo criado
- [ ] Todos os templates presentes
- [ ] Código bem estruturado
- [ ] Fácil de usar

---

### 7. Criar Listas de Tarefa para o Próprio AI

#### Teste 7.1: Lista de Tarefas para Implementação
**Prompt:**
```
Crie um arquivo TODO.md com uma lista de tarefas para implementar um sistema de autenticação:
1. Criar modelo de usuário
2. Implementar endpoints de login/registro
3. Adicionar middleware de autenticação
4. Criar testes unitários
5. Documentar API
```

**Validações:**
- [ ] Arquivo TODO.md criado
- [ ] Todas as tarefas listadas
- [ ] Formato Markdown correto
- [ ] Estrutura clara

---

#### Teste 7.2: Plano de Implementação
**Prompt:**
```
Crie um arquivo IMPLEMENTATION_PLAN.md com um plano detalhado para criar um sistema de e-commerce:
- Fase 1: Estrutura base
- Fase 2: Autenticação
- Fase 3: Produtos
- Fase 4: Carrinho
- Fase 5: Checkout
```

**Validações:**
- [ ] Plano criado
- [ ] Fases bem definidas
- [ ] Detalhamento adequado
- [ ] Formato organizado

---

### 8. Entender Contexto de Conversa e Workspace

#### Teste 8.1: Contexto de Conversa
**Prompt (Sequência):**
```
1. "Crie um arquivo user.js com uma classe User"
2. "Agora adicione um método getFullName() nessa classe"
3. "Crie um arquivo userService.js que usa a classe User"
```

**Validações:**
- [ ] AI lembra da classe User criada anteriormente
- [ ] Método adicionado na classe correta
- [ ] userService.js importa User corretamente
- [ ] Contexto mantido entre mensagens

---

#### Teste 8.2: Contexto do Workspace
**Prompt:**
```
Analise o workspace atual e crie um arquivo que se integre com os arquivos existentes.
```

**Validações:**
- [ ] AI analisou estrutura do workspace
- [ ] Arquivo criado no local apropriado
- [ ] Imports/exports corretos
- [ ] Integração com código existente

---

#### Teste 8.3: Referência a Arquivos Existentes
**Prompt:**
```
Crie um arquivo Card.jsx baseado no arquivo Button.jsx existente, mantendo o mesmo estilo e estrutura.
```

**Validações:**
- [ ] AI encontrou Button.jsx
- [ ] Card.jsx criado com estrutura similar
- [ ] Estilo e padrões mantidos
- [ ] Imports consistentes

---

### 9. Entender Arquiteturas e Boas Práticas (SOLID)

#### Teste 9.1: Projeto com SOLID
**Prompt:**
```
Crie um projeto Python seguindo os princípios SOLID:
- Single Responsibility: cada classe com uma responsabilidade
- Open/Closed: extensível sem modificar código existente
- Liskov Substitution: subclasses substituíveis
- Interface Segregation: interfaces específicas
- Dependency Inversion: dependências invertidas
```

**Validações:**
- [ ] Estrutura SOLID implementada
- [ ] Cada princípio aplicado
- [ ] Código bem organizado
- [ ] Exemplos claros

---

#### Teste 9.2: Clean Architecture
**Prompt:**
```
Crie um projeto seguindo Clean Architecture:
- Camadas: Entities, Use Cases, Interface Adapters, Frameworks
- Dependências apontando para dentro
- Testes em cada camada
- README explicando a arquitetura
```

**Validações:**
- [ ] Estrutura Clean Architecture
- [ ] Camadas bem definidas
- [ ] Dependências corretas
- [ ] Testes criados
- [ ] Documentação presente

---

#### Teste 9.3: Design Patterns
**Prompt:**
```
Crie um exemplo de cada um destes padrões de design:
- Factory Pattern
- Observer Pattern
- Singleton Pattern
- Strategy Pattern
```

**Validações:**
- [ ] Todos os padrões implementados
- [ ] Exemplos funcionais
- [ ] Código bem documentado
- [ ] Estrutura clara

---

### 10. Criar Projetos Inteiros Sozinhos

#### Teste 10.1: Projeto Completo - Todo App
**Prompt:**
```
Crie um aplicativo completo de lista de tarefas (Todo List) com:
- Frontend React
- Backend Node.js/Express
- Banco de dados (configuração)
- Autenticação
- Testes
- README completo
- Docker (opcional)
```

**Validações:**
- [ ] Projeto completo criado
- [ ] Frontend e backend funcionais
- [ ] Estrutura organizada
- [ ] Testes incluídos
- [ ] README detalhado
- [ ] Pode ser executado

---

#### Teste 10.2: Projeto Completo - API REST
**Prompt:**
```
Crie uma API REST completa para gerenciamento de produtos:
- Estrutura de pastas profissional
- CRUD completo
- Validações
- Tratamento de erros
- Documentação (Swagger/OpenAPI)
- Testes
- README
```

**Validações:**
- [ ] API completa
- [ ] CRUD implementado
- [ ] Validações presentes
- [ ] Documentação criada
- [ ] Testes incluídos
- [ ] README completo

---

#### Teste 10.3: Projeto Completo - Mobile App
**Prompt:**
```
Crie um aplicativo mobile completo (React Native ou Flutter):
- Estrutura de projeto
- Navegação
- Estado global
- Integração com API
- Testes
- README
```

**Validações:**
- [ ] Projeto mobile criado
- [ ] Estrutura completa
- [ ] Navegação configurada
- [ ] Estado gerenciado
- [ ] Testes incluídos
- [ ] README com instruções

---

### 11. Criar Múltiplos Arquivos Relacionados

#### Teste 11.1: Múltiplos Componentes
**Prompt:**
```
Crie 3 componentes React relacionados:
- Button.jsx (componente base)
- PrimaryButton.jsx (estende Button)
- SecondaryButton.jsx (estende Button)
Todos devem seguir o mesmo padrão de estilo.
```

**Validações:**
- [ ] Todos os componentes criados
- [ ] Herança/extensão correta
- [ ] Padrão de estilo consistente
- [ ] Imports corretos

---

#### Teste 11.2: Módulo Completo
**Prompt:**
```
Crie um módulo completo de autenticação com:
- authService.js (lógica de autenticação)
- authController.js (controladores)
- authRoutes.js (rotas)
- authMiddleware.js (middleware)
- authModels.js (modelos)
```

**Validações:**
- [ ] Todos os arquivos criados
- [ ] Integração entre arquivos
- [ ] Imports/exports corretos
- [ ] Módulo funcional

---

### 12. Cenários Complexos

#### Teste 12.1: Migração de Código
**Prompt:**
```
Migre o código do arquivo oldService.js para TypeScript:
- Crie service.ts
- Adicione tipos
- Mantenha funcionalidade
- Atualize imports
```

**Validações:**
- [ ] Código migrado
- [ ] Tipos TypeScript adicionados
- [ ] Funcionalidade preservada
- [ ] Imports atualizados

---

#### Teste 12.2: Refatoração Completa
**Prompt:**
```
Refatore o projeto atual aplicando:
- Clean Code
- SOLID principles
- Design Patterns apropriados
- Melhorias de performance
```

**Validações:**
- [ ] Código refatorado
- [ ] Princípios aplicados
- [ ] Padrões implementados
- [ ] Performance melhorada
- [ ] Funcionalidade preservada

---

## 📊 Checklist de Validação Geral

Para cada teste, verificar:

### Funcionalidade
- [ ] Arquivo(s) criado(s) corretamente
- [ ] Código funcional
- [ ] Sem erros de sintaxe
- [ ] Imports/exports corretos

### Contexto
- [ ] AI entendeu o contexto da conversa
- [ ] AI analisou o workspace
- [ ] Referências a arquivos existentes corretas
- [ ] Estrutura respeitada

### Qualidade
- [ ] Código bem estruturado
- [ ] Comentários adequados
- [ ] Segue boas práticas
- [ ] Padrões do projeto respeitados

### Integração
- [ ] Arquivos se relacionam corretamente
- [ ] Dependências corretas
- [ ] Estrutura consistente
- [ ] Pronto para uso

---

## 🚀 Como Executar os Testes

1. **Abra o DuilioCode Studio**
2. **Abra um workspace** (crie um novo para cada categoria de teste)
3. **Execute os prompts** na ordem sugerida
4. **Valide cada item** do checklist
5. **Documente resultados** (sucesso/falha/observações)

---

## 📝 Notas de Teste

**Data:** _______________
**Workspace:** _______________
**Modelo usado:** _______________

**Resultados:**
- Total de testes: ___
- Passou: ___
- Falhou: ___
- Taxa de sucesso: ___%

**Observações:**
- [Anotar problemas encontrados]
- [Anotar melhorias necessárias]
- [Anotar funcionalidades que funcionaram bem]

---

**Última atualização**: 2024
**Status**: Pronto para validação
