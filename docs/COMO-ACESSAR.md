# 📚 Como Acessar a Documentação

## Passo a Passo

### 1. Inicie o Servidor

```bash
cd /Users/jeffersonsilva/Desen/duilio-code-studio
./start.sh
```

Ou manualmente:

```bash
cd src
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8080 --reload
```

### 2. Acesse no Navegador

Abra seu navegador e acesse:

**Interface de Documentação:**
```
http://localhost:8080/docs
```

ou

```
http://localhost:8080/docs/viewer
```

**Interface Principal do DuilioCode:**
```
http://localhost:8080
```

**API Documentation (Swagger):**
```
http://localhost:8080/docs
```

### 3. URLs Disponíveis

| URL | Descrição |
|-----|-----------|
| `http://localhost:8080/docs` | Interface de documentação (HTML) |
| `http://localhost:8080/docs/viewer` | Interface de documentação (alternativa) |
| `http://localhost:8080/api/docs/list?lang=pt` | Lista documentos em PT |
| `http://localhost:8080/api/docs/list?lang=en` | Lista documentos em EN |
| `http://localhost:8080/api/docs/content?lang=pt&doc=00-indice` | Conteúdo de um documento |

## Recursos da Interface

### ✅ Navegação
- Sidebar com todos os documentos organizados por categoria
- Busca em tempo real
- Seletor de idioma (PT/EN)

### ✅ Visualização
- Design limpo e moderno
- Syntax highlighting em blocos de código
- Tipografia profissional
- Layout responsivo

### ✅ Funcionalidades
- Troca de idioma instantânea
- Busca em títulos e conteúdo
- Navegação por categorias
- Links entre documentos

## Troubleshooting

### Servidor não inicia
```bash
# Verifique se a porta 8080 está livre
lsof -i :8080

# Ou mude a porta no .env
PORT=8081
```

### Documentação não carrega
```bash
# Verifique se os arquivos existem
ls docs/pt/*.md

# Verifique se o servidor está rodando
curl http://localhost:8080/health
```

### Erro 404
- Certifique-se de que o servidor está rodando
- Verifique se está acessando a URL correta
- Confira se os arquivos de documentação existem em `docs/pt/` e `docs/en/`

## Dica

Adicione aos favoritos:
- `http://localhost:8080/docs` - Documentação completa
- `http://localhost:8080` - Interface principal
