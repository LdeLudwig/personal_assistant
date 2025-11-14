import os
from dotenv import load_dotenv
from notion_client import (
    Client,
    APIResponseError,
    APIErrorCode,
)
from agno.tools import tool

# Utils
from ..utils.group_identify import group_identify

load_dotenv()

client = Client(auth=os.getenv("NOTION_API_KEY"))


@tool(
    name="find_task_by_id",
    description="Busca uma página de tarefa específica no Notion pelo ID da página.",
)
def find_task_by_id(id: str):
    """
    Busca uma tarefa específica no Notion pelo ID da página.

    Args:
        id (str): ID único da página no Notion

    Returns:
        dict: Objeto da página do Notion com id, properties, url, etc.
        None: Se houver erro
    """
    try:
        task = client.pages.retrieve(id)
        return task
    except APIResponseError as e:
        if e.code == APIErrorCode.ObjectNotFound:
            print(f"Page not found - {e}")
        else:
            print(f"Error - {e}")


@tool(
    name="list_tasks",
    description="Lista páginas de tarefas em um banco do Notion com base no grupo identificado a partir do nome informado (ex.: 'pessoal', 'trabalho', 'projetos'). Suporta filtragem por data (start/end).",
)
def list_tasks(name: str, start_date: str = None, end_date: str = None):
    """
    Lista tarefas de um database do Notion com filtragem opcional por data.

    Args:
        name (str): Nome do database ('pessoal', 'trabalho', 'projetos')
        start_date (str, optional): Data de início (ISO 8601: YYYY-MM-DD).
            Retorna tarefas que começam ou estão em andamento nessa data.
        end_date (str, optional): Data de término (ISO 8601: YYYY-MM-DD).
            Retorna tarefas que terminam ou estão em andamento nessa data.

    Returns:
        dict: Objeto com 'results' (lista de tarefas), 'has_more', 'next_cursor'
        None: Se houver erro
    """
    try:
        group = group_identify(name)
        if not group:
            raise ValueError(
                f"Grupo '{name}' não identificado, usando 'pessoal' como padrão"
            )

        # Construir filtro se datas forem fornecidas
        filter_conditions = []

        if start_date is not None:
            filter_conditions.append(
                {
                    "and": [
                        {"property": "Date", "date": {"on_or_before": start_date}},
                        {
                            "or": [
                                {
                                    "property": "Date",
                                    "date": {"on_or_after": start_date},
                                },
                                {"property": "Date", "date": {"equals": start_date}},
                            ]
                        },
                    ]
                }
            )

        if end_date is not None:
            filter_conditions.append(
                {
                    "and": [
                        {"property": "Date", "date": {"on_or_before": end_date}},
                        {"property": "Date", "date": {"on_or_after": end_date}},
                    ]
                }
            )

        # Montar query com ou sem filtro
        if filter_conditions:
            if len(filter_conditions) == 1:
                # Apenas um filtro
                query_filter = filter_conditions[0]
            else:
                # Múltiplos filtros (AND)
                query_filter = {"and": filter_conditions}

            tasks = client.databases.query(group["database_id"], filter=query_filter)
        else:
            # Sem filtros, retornar todas as tarefas
            tasks = client.databases.query(group["database_id"])

        return tasks

    except APIResponseError as e:
        if e.code == APIErrorCode.ObjectNotFound:
            print(f"Pages not found - {e}")
        else:
            print(f"Error - {e}")
    except ValueError as e:
        print(f"Error - {e}")


@tool(
    name="find_task_by_title",
    description="Busca tarefas no banco pessoal pelo título exato (propriedade 'Name').",
)
def find_task_by_title(name: str, title: str):
    """
    Busca tarefas em um database do Notion pelo título exato.

    Args:
        name (str): Nome do database ('pessoal', 'trabalho', 'projetos')
        title (str): Título exato da tarefa (case-sensitive)

    Returns:
        dict: Objeto com 'results' (lista de tarefas encontradas)
        None: Se houver erro
    """
    try:
        group = group_identify(name)

        task = client.databases.query(
            group["database_id"],
            filter={"property": "Name", "title": {"equals": title}},
        )
        return task
    except APIResponseError as e:
        if e.code == APIErrorCode.ObjectNotFound:
            print(f"Page not found - {e}")
        else:
            print(f"Error - {e}")


@tool(
    name="create_new_tasks",
    description="Cria uma nova tarefa no banco pessoal usando o modelo PersonalTask (name obrigatório; priority, status, relation, start, end opcionais).",
)
def create_new_tasks(name: str, data: dict):
    """
    Cria uma nova tarefa em um database do Notion.

    Args:
        name (str): Nome do database ('pessoal', 'trabalho', 'projetos')
        data (dict): Dados da tarefa. Campos por database:
            - PersonalTask: name* (obrigatório), priority, status, work_tasks, start, end
            - WorkTask: name*, project* (obrigatórios), priority, status, start, end
            - WorkProject: name* (obrigatório), priority, tag, status, start, end
            Datas no formato ISO 8601 (YYYY-MM-DD)

    Returns:
        dict: Objeto da página criada com id, properties, url, etc.
        None: Se houver erro
    """
    try:
        group = group_identify(name)

        model = group["model"](data)

        payload = model.to_create_payload(group["database_id"])
        task = client.pages.create(**payload)

        return task

    except APIResponseError as e:
        if e.code == APIErrorCode.ObjectNotFound:
            print(f"Database or related objects not found - {e}")
        else:
            print(f"Error creating Notion page - {e}")


@tool(
    name="update_task",
    description="Atualiza uma tarefa pessoal existente no Notion pelo ID, aplicando os campos fornecidos do modelo PersonalTask.",
)
def update_task(task_id: str, database_name: str, data: dict):
    """
    Atualiza uma tarefa existente em um database do Notion.

    Args:
        task_id (str): ID único da página/tarefa a ser atualizada
        database_name (str): Nome do database ('pessoal', 'trabalho', 'projetos')
        data (dict): Campos a serem atualizados (mesmos campos de create_new_tasks).
            Apenas os campos fornecidos serão atualizados.

    Returns:
        dict: Objeto da página atualizada com id, properties, url, etc.
        None: Se houver erro
    """
    try:
        group = group_identify(database_name)

        model = group["model"](data)

        payload = model.to_create_payload(group["database_id"])

        task = client.pages.update(task_id, **payload)
        return task
    except APIResponseError as e:
        if e.code == APIErrorCode.ObjectNotFound:
            print(f"Database or related objects not found - {e}")
        else:
            print(f"Error creating Notion page - {e}")
