from rich.console import Group
from rich.table import Table


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
            args = []
            for arg_name, info in getattr(tool, "inputs", {}).items():
                arg_type = info.get("type", "Any")
                optional = ", optional" if info.get("optional") else ""
                description = info.get("description", "")
                arg_str = f"{arg_name} (`{arg_type}`{optional}): {description}"
                args.append(arg_str)
            table.add_row(name, tool.__doc__, "\n".join(args))

        return Group("🛠️ [italic #1E90FF]Tools:[/italic #1E90FF]", table)
