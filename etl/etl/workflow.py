from dotenv import load_dotenv
from etl.utils.logger import Logger
import click

load_dotenv()

WORKFLOWS = {
    "daily": ["hello_today","byebye"],
}


@click.group()
def cli():
    pass

@cli.command()
@click.option("--workflow", "-w", required=True, help="Workflow name (ex: daily, monthly_report)")
def run_workflow(workflow):
    """Exécute un workflow défini dans WORKFLOWS"""
    tasks = WORKFLOWS.get(workflow)

    if not tasks:
        Logger.error(f"Workflow '{workflow}' introuvable. Options disponibles: {list(WORKFLOWS.keys())}")
        return

    for task in tasks:
        Logger.info(f"➡ Running task: {task}")
        func = globals().get(task)
        if func is None:
            Logger.error(f"Tâche '{task}' non définie dans le code.")
            continue
        try:
            func()
        except Exception as e:
            Logger.error(f"❌ Erreur pendant '{task}': {e}")
            continue

    Logger.info(f"Workflow '{workflow}' terminé")


def hello_today():
    Logger.info("👋 Hello from hello_today task!")

def byebye():
    Logger.info("👋 Bye bye ! See you soon")