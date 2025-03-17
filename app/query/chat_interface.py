"""
Módulo que proporciona una interfaz de chat para el sistema RAG.
"""

import cmd
import logging
import json
import os
import sys

# Añadir la ruta del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown

from app.query.rag_query import RAGQuerySystem
from app.utils.performance_metrics import PerformanceTracker
from app.core.document_manager import DocumentManager

logger = logging.getLogger(__name__)

class CommandLineChatInterface(cmd.Cmd):
    """Interfaz de chat en línea de comandos para el sistema RAG."""

    intro = "Bienvenido al sistema RAG. Escribe 'ayuda' para ver los comandos disponibles. Escribe 'salir' para salir."
    prompt = ">> "

    def __init__(self):
        super().__init__()
        self.console = Console()
        self.rag_system = RAGQuerySystem()
        self.document_manager = DocumentManager()
        self.performance_tracker = self.rag_system.performance_tracker
        self.conversation_history: List[Dict] = []
        self.similarity_threshold = 0.1  # Umbral predeterminado (modificado de 0.3 a 0.1)
        self._load_conversation_history()

    def default(self, line: str) -> bool:
        """Procesa una consulta del usuario."""
        if not line.strip():
            return False
        
        # Comandos especiales
        if line.lower() in ['salir', 'exit', 'quit']:
            return self.do_exit(line)
        
        if line.lower() in ['ayuda', 'help']:
            return self.do_help(line)
        
        # Procesar la consulta
        self.console.print(f"[bold blue]Procesando: {line}[/bold blue]")
        try:
            result = self.rag_system.query(line, similarity_threshold=self.similarity_threshold)
            
            # Extraer respuesta y fuentes del resultado
            response = result.get("answer", "No se pudo obtener una respuesta")
            sources = result.get("sources", [])
            
            # Guardar en el historial
            self.conversation_history.append({
                "question": line,
                "response": response,
                "sources": sources
            })
            self._save_conversation_history()
            
            # Mostrar la respuesta
            self.console.print("\n[bold green]Respuesta:[/bold green]")
            self.console.print(Markdown(response))
            
            # Mostrar las fuentes
            if sources:
                self.console.print("\n[bold yellow]Fuentes:[/bold yellow]")
                for idx, source in enumerate(sources, 1):
                    self.console.print(f"[yellow]{idx}.[/yellow] {source}")
            else:
                self.console.print("\n[yellow]No se encontraron fuentes relevantes.[/yellow]")
                
        except Exception as e:
            logger.error(f"Error al procesar la consulta: {e}")
            self.console.print(f"[bold red]Error al procesar la consulta: {e}[/bold red]")
        
        return False

    def do_exit(self, arg: str) -> bool:
        """Salir de la aplicación."""
        self.console.print("[bold]¡Hasta luego![/bold]")
        return True
    
    def do_statistics(self, arg: str) -> None:
        """Muestra estadísticas sobre los documentos y consultas."""
        stats = self.document_manager.get_document_statistics()
        
        table = Table(title="Estadísticas de Documentos")
        table.add_column("Métrica", style="cyan")
        table.add_column("Valor", style="magenta")
        
        table.add_row("Total de archivos", str(stats.get('total_files', 0)))
        table.add_row("Total de fragmentos", str(stats.get('total_chunks', 0)))
        table.add_row("Última actualización", str(stats.get('last_processed', 'N/A')))
        
        self.console.print(table)
    
    def do_history(self, arg: str) -> None:
        """Muestra el historial de consultas."""
        if not self.conversation_history:
            self.console.print("[yellow]No hay historial de consultas.[/yellow]")
            return
        
        try:
            limit = 5
            if arg and arg.isdigit():
                limit = int(arg)
            
            # Obtener el historial de la base de datos
            db_history = self.rag_system.get_query_history(limit)
            
            table = Table(title=f"Historial de Consultas (últimas {len(db_history)})")
            table.add_column("ID", style="cyan")
            table.add_column("Fecha", style="blue")
            table.add_column("Consulta", style="green")
            table.add_column("Fuentes", style="yellow")
            
            for item in db_history:
                sources_count = len(item.get('sources', []))
                table.add_row(
                    str(item.get('id', 'N/A')),
                    str(item.get('created_at', 'N/A')),
                    item.get('query', 'N/A'),
                    f"{sources_count} fuentes"
                )
            
            self.console.print(table)
            
        except Exception as e:
            logger.error(f"Error al obtener el historial: {e}")
            self.console.print(f"[bold red]Error al obtener el historial: {e}[/bold red]")
    
    def do_performance(self, arg: str) -> None:
        """Muestra estadísticas de rendimiento."""
        try:
            stats = self.performance_tracker.get_performance_stats()
            
            table = Table(title="Estadísticas de Rendimiento (ms)")
            table.add_column("Operación", style="cyan")
            table.add_column("Promedio", style="blue")
            table.add_column("Mínimo", style="green")
            table.add_column("Máximo", style="red")
            table.add_column("Mediana", style="yellow")
            table.add_column("P95", style="magenta")
            
            for op, metrics in stats.items():
                table.add_row(
                    op,
                    f"{metrics['avg']:.2f}",
                    f"{metrics['min']:.2f}",
                    f"{metrics['max']:.2f}",
                    f"{metrics['median']:.2f}",
                    f"{metrics['p95']:.2f}"
                )
            
            self.console.print(table)
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas de rendimiento: {e}")
            self.console.print(f"[bold red]Error al obtener estadísticas de rendimiento: {e}[/bold red]")
    
    def do_threshold(self, arg: str) -> None:
        """Establece el umbral de similitud para las búsquedas (valor entre 0 y 1)."""
        if not arg:
            self.console.print(f"[yellow]Umbral de similitud actual: {self.similarity_threshold}[/yellow]")
            return
        
        try:
            threshold = float(arg)
            if 0 <= threshold <= 1:
                self.similarity_threshold = threshold
                self.console.print(f"[green]Umbral de similitud establecido a: {threshold}[/green]")
            else:
                self.console.print("[red]El umbral debe estar entre 0 y 1.[/red]")
        except ValueError:
            self.console.print("[red]Por favor ingresa un número válido entre 0 y 1.[/red]")
    
    def do_clear(self, arg: str) -> None:
        """Limpia la pantalla."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def do_help(self, arg: str) -> None:
        """Muestra ayuda sobre los comandos disponibles."""
        commands = {
            "consulta": "Escribe cualquier texto para hacer una consulta al sistema RAG",
            "statistics": "Muestra estadísticas sobre los documentos procesados",
            "history [n]": "Muestra las últimas n consultas (predeterminado: 5)",
            "performance": "Muestra estadísticas de rendimiento",
            "threshold [valor]": "Establece el umbral de similitud (0-1)",
            "clear": "Limpia la pantalla",
            "help": "Muestra esta ayuda",
            "exit/quit/salir": "Sale de la aplicación"
        }
        
        table = Table(title="Comandos Disponibles")
        table.add_column("Comando", style="cyan")
        table.add_column("Descripción", style="green")
        
        for cmd, desc in commands.items():
            table.add_row(cmd, desc)
        
        self.console.print(table)
    
    def emptyline(self) -> bool:
        """No hacer nada al presionar Enter en una línea vacía."""
        return False
    
    def _save_conversation_history(self, max_history: int = 100) -> None:
        """Guarda el historial de conversación en un archivo JSON."""
        try:
            # Limitar el tamaño del historial
            if len(self.conversation_history) > max_history:
                self.conversation_history = self.conversation_history[-max_history:]
            
            with open("conversation_history.json", "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error al guardar el historial de conversación: {e}")
    
    def _load_conversation_history(self) -> None:
        """Carga el historial de conversación desde un archivo JSON."""
        try:
            if os.path.exists("conversation_history.json"):
                with open("conversation_history.json", "r", encoding="utf-8") as f:
                    self.conversation_history = json.load(f)
                logger.info(f"Historial de conversación cargado: {len(self.conversation_history)} entradas")
        except Exception as e:
            logger.error(f"Error al cargar el historial de conversación: {e}")
            self.conversation_history = []
    
    def run(self) -> None:
        """Inicia el intérprete de comandos."""
        try:
            # Mostrar comandos al inicio
            self.do_help("")
            
            # Usar una implementación personalizada del bucle de comandos para evitar problemas con readline
            while True:
                try:
                    line = input(self.prompt)
                    if not line:
                        self.emptyline()
                        continue
                    
                    if line.lower() in ('exit', 'quit', 'salir'):
                        return self.do_exit("")
                    
                    if line.startswith('help'):
                        self.do_help(line[4:].strip())
                        continue
                        
                    if line.startswith('statistics'):
                        self.do_statistics(line[10:].strip())
                        continue
                        
                    if line.startswith('history'):
                        self.do_history(line[7:].strip())
                        continue
                        
                    if line.startswith('performance'):
                        self.do_performance(line[11:].strip())
                        continue
                        
                    if line.startswith('threshold'):
                        self.do_threshold(line[9:].strip())
                        continue
                        
                    if line.startswith('clear'):
                        self.do_clear("")
                        continue
                    
                    # Cualquier otra entrada se trata como consulta
                    self.default(line)
                    
                except KeyboardInterrupt:
                    print("\nInterrumpido por el usuario.")
                    return
                except EOFError:
                    print("\nSaliendo...")
                    return
        except Exception as e:
            logger.error(f"Error en el intérprete de comandos: {str(e)}")
            print(f"Error: {str(e)}")


def main():
    """Función principal."""
    chat_interface = CommandLineChatInterface()
    chat_interface.run()


if __name__ == "__main__":
    main() 