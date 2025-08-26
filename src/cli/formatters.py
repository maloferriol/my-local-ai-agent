


from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


class Formatters:
    def create_conversation_list_section(conversations):
        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", style="#1E90FF")
        table.add_column("Name")

        for conv in conversations:
            table.add_row(str(conv[0]), conv[1])

        return Group("🛠️ [italic #1E90FF]Conversations:[/italic #1E90FF]", table)

    def create_tools_list_section(tools_dict):
        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", style="#1E90FF")
        table.add_column("Description")
        table.add_column("Arguments")

        for name, tool in tools_dict.items():
            args = [
                f"{arg_name} (`{info.get('type', 'Any')}`{', optional' if info.get('optional') else ''}): {info.get('description', '')}"
                for arg_name, info in getattr(tool, "inputs", {}).items()
            ]
            table.add_row(name, tool.__doc__, "\n".join(args))

        return Group("🛠️ [italic #1E90FF]Tools:[/italic #1E90FF]", table)
