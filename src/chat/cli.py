"""
Chat CLI - Interactive terminal chat with Ollama
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.live import Live

from src.chat.ollama_client import OllamaClient


console = Console()


async def interactive_chat():
    """Run interactive chat session."""
    client = OllamaClient()
    
    console.print(Panel.fit(
        "[bold cyan]🤖 Local AI Studio - Chat[/]\n"
        "[dim]Type your message and press Enter. Commands:[/]\n"
        "[dim]  /clear - Clear history | /model <name> - Switch model[/]\n"
        "[dim]  /image <path> - Analyze image | /code <lang> - Code mode[/]\n"
        "[dim]  /quit - Exit[/]",
        border_style="cyan"
    ))
    
    # Check available models
    try:
        models = await client.list_models()
        model_names = [m["name"] for m in models]
        console.print(f"[dim]Available models: {', '.join(model_names[:5])}{'...' if len(model_names) > 5 else ''}[/]\n")
    except Exception as e:
        console.print(f"[yellow]⚠️ Could not connect to Ollama: {e}[/]")
        console.print("[dim]Make sure Ollama is running: ollama serve[/]\n")
        return
    
    current_model = client.model
    code_mode = False
    code_lang = "python"
    
    while True:
        try:
            # Get input
            prompt_text = f"[bold green]You ({current_model})[/]" if not code_mode else f"[bold yellow]Code ({code_lang})[/]"
            user_input = Prompt.ask(prompt_text)
            
            if not user_input.strip():
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                cmd = user_input.lower().split()
                
                if cmd[0] == "/quit" or cmd[0] == "/exit":
                    console.print("[cyan]Goodbye! 👋[/]")
                    break
                
                elif cmd[0] == "/clear":
                    client.clear_history()
                    console.print("[dim]History cleared.[/]")
                    continue
                
                elif cmd[0] == "/model":
                    if len(cmd) > 1:
                        current_model = cmd[1]
                        client.model = current_model
                        console.print(f"[dim]Switched to model: {current_model}[/]")
                    else:
                        console.print(f"[dim]Current model: {current_model}[/]")
                    continue
                
                elif cmd[0] == "/image":
                    if len(cmd) > 1:
                        image_path = " ".join(cmd[1:])
                        question = Prompt.ask("[dim]Question about image[/]", default="Describe this image")
                        console.print("[dim]Analyzing image...[/]")
                        try:
                            response = await client.chat_with_image(question, image_path=image_path)
                            console.print(Panel(Markdown(response), title="[cyan]AI[/]", border_style="cyan"))
                        except Exception as e:
                            console.print(f"[red]Error: {e}[/]")
                    else:
                        console.print("[dim]Usage: /image <path>[/]")
                    continue
                
                elif cmd[0] == "/code":
                    code_mode = not code_mode
                    if len(cmd) > 1:
                        code_lang = cmd[1]
                    console.print(f"[dim]Code mode: {'ON' if code_mode else 'OFF'} ({code_lang})[/]")
                    continue
                
                elif cmd[0] == "/help":
                    console.print(Panel(
                        "/clear - Clear conversation history\n"
                        "/model <name> - Switch model (e.g., /model codellama)\n"
                        "/image <path> - Analyze an image\n"
                        "/code [lang] - Toggle code mode\n"
                        "/quit - Exit",
                        title="Commands",
                        border_style="dim"
                    ))
                    continue
                
                else:
                    console.print(f"[dim]Unknown command. Type /help for help.[/]")
                    continue
            
            # Generate response with streaming
            console.print()
            response_text = ""
            
            with Live(Panel("[dim]Thinking...[/]", title="[cyan]AI[/]", border_style="cyan"), refresh_per_second=10) as live:
                if code_mode:
                    # Code generation (non-streaming for better formatting)
                    response_text = await client.code(user_input, language=code_lang)
                    live.update(Panel(Markdown(response_text), title="[cyan]AI[/]", border_style="cyan"))
                else:
                    # Chat with streaming
                    async for chunk in await client.chat(user_input, model=current_model, stream=True):
                        response_text += chunk
                        try:
                            live.update(Panel(Markdown(response_text), title="[cyan]AI[/]", border_style="cyan"))
                        except:
                            live.update(Panel(response_text, title="[cyan]AI[/]", border_style="cyan"))
            
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[cyan]Goodbye! 👋[/]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")


def main():
    """Entry point."""
    asyncio.run(interactive_chat())


if __name__ == "__main__":
    main()
