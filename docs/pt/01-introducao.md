# Introdução ao DuilioCode Studio

## O que é o DuilioCode Studio?

DuilioCode Studio é um assistente de código com inteligência artificial que roda **localmente no seu computador**. Ele entende o que você quer fazer e pode **criar, modificar, deletar e ler arquivos** diretamente, sem você precisar fazer isso manualmente.

## Conceitos Fundamentais

### 🤖 Assistente de IA Local
- **Não usa internet**: Tudo roda no seu computador
- **Privacidade total**: Seus códigos nunca saem da sua máquina
- **Rápido**: Não depende de conexão com servidores externos

### 💬 Dois Modos de Conversa

#### Modo Chat (Simples)
- Para perguntas gerais
- Conversa direta, sem operações em arquivos
- Interface focada, similar ao Gemini ou DeepSeek

#### Modo Agent (Avançado)
- Pode **criar, ler, modificar e deletar** arquivos
- Entende o contexto do seu projeto
- Acessa informações do sistema (arquivos, pastas, etc.)

### 🔧 Como Funciona?

```
Você escreve: "crie um arquivo teste.txt com 'Hello World'"
    ↓
DuilioCode entende sua intenção
    ↓
Gera o código de ação: ```create-file:teste.txt
Hello World
```
    ↓
Action Processor executa a ação
    ↓
Arquivo criado no seu computador!
```

## Componentes Principais

### 1. **Ollama** - Motor de IA
- Servidor local que roda modelos de linguagem
- Comunica via API HTTP
- Suporta vários modelos (Qwen, Llama, etc.)

### 2. **Qwen2.5-Coder** - Modelo de IA
- Modelo especializado em código
- Entende Python, JavaScript, TypeScript, Kotlin, etc.
- Gera código funcional e correto

### 3. **FastAPI** - Framework Web
- Cria a API que conecta frontend e backend
- Gerencia requisições HTTP
- Processa e retorna respostas

### 4. **Action Processor** - Executor de Ações
- Lê as ações geradas pela IA
- Executa no sistema de arquivos
- Valida e protege contra operações perigosas

## Por que é Útil?

### Antes (Sem DuilioCode)
```
1. Você pensa: "Preciso criar um arquivo teste.txt"
2. Abre o editor
3. Cria o arquivo
4. Escreve o conteúdo
5. Salva
```

### Com DuilioCode
```
1. Você escreve: "crie teste.txt com 'Hello World'"
2. DuilioCode cria automaticamente
```

### Exemplos Reais

**Criar projeto completo:**
```
"crie um projeto React completo com componentes"
→ DuilioCode cria package.json, src/, componentes, etc.
```

**Modificar arquivo:**
```
"adicione uma função de validação no arquivo utils.js"
→ DuilioCode lê o arquivo, adiciona a função, salva
```

**Listar arquivos:**
```
"quais arquivos você vê na pasta src?"
→ DuilioCode lista todos os arquivos do projeto
```

## Tecnologias Usadas

- **Python 3.9+**: Linguagem principal
- **FastAPI**: Framework web moderno e rápido
- **Ollama**: Servidor de IA local
- **SQLAlchemy**: Banco de dados (SQLite)
- **JavaScript**: Frontend (Vanilla JS, sem frameworks)
- **SQLite**: Banco de dados local

## Próximos Passos

1. [Instalação Passo a Passo](02-instalacao.md)
2. [Primeiros Passos](03-primeiros-passos.md)
3. [Arquitetura do Sistema](04-arquitetura.md)
