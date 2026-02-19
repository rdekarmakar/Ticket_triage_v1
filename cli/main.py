"""
CLI tool for the Ticket Triage System.
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Optional

app = typer.Typer(
    name="triage",
    help="Ticket Triage System CLI - Query runbooks and triage alerts"
)
console = Console()


@app.command()
def index(
    force: bool = typer.Option(False, "--force", "-f", help="Force full reindex")
):
    """
    Index or reindex the knowledge base runbooks.
    """
    from knowledge_base.indexer import KnowledgeBaseIndexer

    console.print("[bold blue]Indexing knowledge base...[/bold blue]\n")

    try:
        indexer = KnowledgeBaseIndexer()
        count = indexer.index_all_runbooks(force_reindex=force)
        console.print(f"\n[bold green]Successfully indexed {count} chunks[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def query(
    question: str = typer.Argument(..., help="Search query for runbooks"),
    limit: int = typer.Option(5, "--limit", "-l", help="Number of results"),
    type_filter: Optional[str] = typer.Option(
        None, "--type", "-t",
        help="Filter by type (infrastructure, application, monitoring)"
    )
):
    """
    Search the knowledge base for relevant runbook sections.
    """
    from knowledge_base.indexer import KnowledgeBaseIndexer

    console.print(f"[bold]Searching for:[/bold] {question}\n")

    try:
        indexer = KnowledgeBaseIndexer()
        results = indexer.search(
            query=question,
            n_results=limit,
            filter_type=type_filter
        )

        if not results:
            console.print("[yellow]No relevant runbook sections found.[/yellow]")
            return

        console.print(f"[bold green]Found {len(results)} relevant sections:[/bold green]\n")

        for i, result in enumerate(results, 1):
            console.print(Panel(
                Markdown(result.content[:1000] + ("..." if len(result.content) > 1000 else "")),
                title=f"[bold]{i}. {result.source_file}[/bold] (Score: {result.score:.0%})",
                subtitle=f"Section: {result.section}",
                border_style="blue"
            ))
            console.print()

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def suggest(
    alert: str = typer.Argument(..., help="Alert text to triage"),
    no_ticket: bool = typer.Option(False, "--no-ticket", "-n", help="Don't create a ticket, just show suggestion")
):
    """
    Generate a triage suggestion for an alert and create a ticket.
    """
    from db.database import get_db_context
    from app.services.triage_service import TriageService

    console.print("[bold blue]Generating triage suggestion...[/bold blue]\n")

    try:
        with get_db_context() as db:
            service = TriageService(db)

            if no_ticket:
                # Quick triage without creating ticket
                result = service.quick_triage(alert)

                # Display classification
                classification = result["classification"]
                console.print(Panel(
                    f"[bold]Type:[/bold] {classification['alert_type']}\n"
                    f"[bold]Severity:[/bold] {classification['severity']}\n"
                    f"[bold]Title:[/bold] {classification['title']}\n"
                    f"[bold]Source:[/bold] {classification.get('source_system', 'Unknown')}\n"
                    f"[bold]Component:[/bold] {classification.get('affected_component', 'Unknown')}",
                    title="[bold]Alert Classification[/bold]",
                    border_style="cyan"
                ))
                console.print()

                # Display runbook sources
                if result["runbook_sources"]:
                    console.print("[bold]Relevant Runbooks:[/bold]")
                    for src in result["runbook_sources"]:
                        console.print(f"  - {src['file']} ({src['score']:.0%})")
                    console.print()

                # Display suggestion
                console.print(Panel(
                    Markdown(result["suggestion"]),
                    title=f"[bold]Triage Suggestion[/bold] (Confidence: {result['confidence']})",
                    border_style="green"
                ))
            else:
                # Full triage with ticket creation
                ticket = service.process_alert(alert)

                # Display ticket info
                console.print(Panel(
                    f"[bold]Ticket ID:[/bold] #{ticket.id}\n"
                    f"[bold]Type:[/bold] {ticket.alert_type.value}\n"
                    f"[bold]Severity:[/bold] {ticket.severity.value}\n"
                    f"[bold]Title:[/bold] {ticket.title}\n"
                    f"[bold]Status:[/bold] {ticket.status.value}\n"
                    f"[bold]Source:[/bold] {ticket.source_system or 'Unknown'}",
                    title="[bold green]Ticket Created[/bold green]",
                    border_style="cyan"
                ))
                console.print()

                # Display runbook sources
                if ticket.runbook_sources:
                    console.print("[bold]Relevant Runbooks:[/bold]")
                    for src in ticket.runbook_sources:
                        console.print(f"  - {src}")
                    console.print()

                # Display suggestion
                if ticket.suggestion:
                    console.print(Panel(
                        Markdown(ticket.suggestion),
                        title=f"[bold]Triage Suggestion[/bold] (Confidence: {ticket.confidence_score or 'N/A'})",
                        border_style="green"
                    ))

                console.print(f"\n[bold green]View ticket:[/bold green] python -m cli.main show {ticket.id}")
                console.print(f"[bold green]Dashboard:[/bold green] http://localhost:8080/dashboard/ticket/{ticket.id}")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def tickets(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    severity: Optional[str] = typer.Option(None, "--severity", help="Filter by severity"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of tickets")
):
    """
    List recent tickets.
    """
    from db.database import get_db_context
    from db.repository import TicketRepository
    from db.models import TicketStatus, Severity

    try:
        with get_db_context() as db:
            repo = TicketRepository(db)

            # Convert filters
            db_status = None
            if status:
                try:
                    db_status = TicketStatus(status)
                except ValueError:
                    console.print(f"[red]Invalid status: {status}[/red]")
                    raise typer.Exit(code=1)

            db_severity = None
            if severity:
                try:
                    db_severity = Severity(severity)
                except ValueError:
                    console.print(f"[red]Invalid severity: {severity}[/red]")
                    raise typer.Exit(code=1)

            ticket_list = repo.get_all(
                limit=limit,
                status=db_status,
                severity=db_severity
            )

            if not ticket_list:
                console.print("[yellow]No tickets found.[/yellow]")
                return

            # Create table inside context manager
            table = Table(title="Recent Tickets")
            table.add_column("ID", style="cyan", justify="right")
            table.add_column("Severity", justify="center")
            table.add_column("Title", max_width=50)
            table.add_column("Type", justify="center")
            table.add_column("Status", justify="center")
            table.add_column("Created", justify="right")

            severity_colors = {
                "critical": "red",
                "high": "orange3",
                "medium": "yellow",
                "low": "green",
                "info": "blue"
            }

            for ticket in ticket_list:
                sev_color = severity_colors.get(ticket.severity.value, "white")
                table.add_row(
                    str(ticket.id),
                    f"[{sev_color}]{ticket.severity.value.upper()}[/{sev_color}]",
                    ticket.title[:50] + ("..." if len(ticket.title) > 50 else ""),
                    ticket.alert_type.value,
                    ticket.status.value.replace("_", " ").title(),
                    ticket.created_at.strftime("%Y-%m-%d %H:%M")
                )

            console.print(table)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def show(
    ticket_id: int = typer.Argument(..., help="Ticket ID to display")
):
    """
    Show details of a specific ticket.
    """
    from db.database import get_db_context
    from db.repository import TicketRepository

    try:
        with get_db_context() as db:
            repo = TicketRepository(db)
            ticket = repo.get(ticket_id)

            if not ticket:
                console.print(f"[red]Ticket #{ticket_id} not found[/red]")
                raise typer.Exit(code=1)

            # Display ticket details inside context manager
            console.print(Panel(
                f"[bold]Title:[/bold] {ticket.title}\n"
                f"[bold]Severity:[/bold] {ticket.severity.value.upper()}\n"
                f"[bold]Type:[/bold] {ticket.alert_type.value}\n"
                f"[bold]Status:[/bold] {ticket.status.value}\n"
                f"[bold]Created:[/bold] {ticket.created_at}\n"
                f"[bold]Source:[/bold] {ticket.source_system or 'Unknown'}",
                title=f"[bold]Ticket #{ticket.id}[/bold]",
                border_style="cyan"
            ))

            if ticket.suggestion:
                console.print(Panel(
                    Markdown(ticket.suggestion),
                    title=f"[bold]Triage Suggestion[/bold] (Confidence: {ticket.confidence_score or 'N/A'})",
                    border_style="green"
                ))

            if ticket.runbook_sources:
                console.print("\n[bold]Runbook Sources:[/bold]")
                for src in ticket.runbook_sources:
                    console.print(f"  - {src}")

            console.print(Panel(
                ticket.raw_message,
                title="[bold]Original Alert[/bold]",
                border_style="dim"
            ))

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def update(
    ticket_id: int = typer.Argument(..., help="Ticket ID to update"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="New status (open, in_progress, resolved, closed)"),
    severity: Optional[str] = typer.Option(None, "--severity", help="New severity (critical, high, medium, low, info)")
):
    """
    Update a ticket's status or severity.
    """
    from db.database import get_db_context
    from db.repository import TicketRepository
    from db.models import TicketStatus, Severity

    if not status and not severity:
        console.print("[yellow]Please specify --status or --severity to update[/yellow]")
        raise typer.Exit(code=1)

    try:
        with get_db_context() as db:
            repo = TicketRepository(db)
            ticket = repo.get(ticket_id)

            if not ticket:
                console.print(f"[red]Ticket #{ticket_id} not found[/red]")
                raise typer.Exit(code=1)

            updates = {}

            if status:
                try:
                    updates["status"] = TicketStatus(status)
                except ValueError:
                    console.print(f"[red]Invalid status: {status}[/red]")
                    console.print("[yellow]Valid statuses: open, in_progress, resolved, closed[/yellow]")
                    raise typer.Exit(code=1)

            if severity:
                try:
                    updates["severity"] = Severity(severity)
                except ValueError:
                    console.print(f"[red]Invalid severity: {severity}[/red]")
                    console.print("[yellow]Valid severities: critical, high, medium, low, info[/yellow]")
                    raise typer.Exit(code=1)

            updated_ticket = repo.update(ticket_id, **updates)

            console.print(Panel(
                f"[bold]Ticket ID:[/bold] #{updated_ticket.id}\n"
                f"[bold]Title:[/bold] {updated_ticket.title}\n"
                f"[bold]Status:[/bold] {updated_ticket.status.value}\n"
                f"[bold]Severity:[/bold] {updated_ticket.severity.value}",
                title="[bold green]Ticket Updated[/bold green]",
                border_style="green"
            ))

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def close(
    ticket_id: int = typer.Argument(..., help="Ticket ID to close")
):
    """
    Close a ticket (shortcut for update --status resolved).
    """
    from db.database import get_db_context
    from db.repository import TicketRepository
    from db.models import TicketStatus

    try:
        with get_db_context() as db:
            repo = TicketRepository(db)
            ticket = repo.get(ticket_id)

            if not ticket:
                console.print(f"[red]Ticket #{ticket_id} not found[/red]")
                raise typer.Exit(code=1)

            updated_ticket = repo.update(ticket_id, status=TicketStatus.RESOLVED)

            console.print(f"[bold green]Ticket #{ticket_id} has been resolved[/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def stats():
    """
    Show ticket statistics.
    """
    from db.database import get_db_context
    from db.repository import TicketRepository

    try:
        with get_db_context() as db:
            repo = TicketRepository(db)
            stat_data = repo.get_stats()

        console.print(Panel(
            f"[bold]Total Tickets:[/bold] {stat_data['total']}\n"
            f"[bold]Open:[/bold] {stat_data['open_count']}\n"
            f"[bold red]Critical:[/bold red] {stat_data['critical_count']}\n"
            f"[bold orange3]High:[/bold orange3] {stat_data['high_count']}",
            title="[bold]Ticket Statistics[/bold]",
            border_style="blue"
        ))

        # By status
        console.print("\n[bold]By Status:[/bold]")
        for status, count in stat_data['by_status'].items():
            console.print(f"  {status}: {count}")

        # By severity
        console.print("\n[bold]By Severity:[/bold]")
        for severity, count in stat_data['by_severity'].items():
            console.print(f"  {severity}: {count}")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def init_db():
    """
    Initialize the database.
    """
    from db.database import init_db as do_init_db

    console.print("[bold blue]Initializing database...[/bold blue]")

    try:
        do_init_db()
        console.print("[bold green]Database initialized successfully[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload")
):
    """
    Start the web server.
    """
    import uvicorn

    console.print(f"[bold blue]Starting server at http://{host}:{port}[/bold blue]")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload
    )


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
