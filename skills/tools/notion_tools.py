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
    description="Cria página em 'pessoal'|'trabalho'|'projetos' usando o modelo correspondente. Regras: (1) em 'pessoal', 'work_tasks' deve conter IDs de tarefas de trabalho; (2) em 'trabalho', 'project' deve conter o ID do projeto de trabalho. Antes de criar, resolva IDs com 'find_task_by_title' ou 'find_task_by_id'; se não encontrar/ambíguo, use 'list_tasks' e solicite confirmação ao usuário. name é obrigatório; priority, status, start, end opcionais; datas ISO 8601.",
)
def create_new_tasks(name: str, data: dict):
    """
    Cria uma nova página em um database do Notion a partir do grupo informado.

    Campos aceitos por database:
      - PersonalTask (pessoal): name*; priority; status; work_tasks (lista de IDs de tarefas de trabalho); start; end
      - WorkTask (trabalho): name*; project* (ID do projeto de trabalho); priority; status; start; end
      - WorkProject (projetos): name*; priority; tag; status; start; end
      Datas no formato ISO 8601 (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS).

    Regras CRÍTICAS para relações:
      1) work_tasks (pessoal): deve ser uma lista de IDs de tarefas do database "trabalho".
      2) project (trabalho): deve ser o ID de um projeto do database "projetos".
      3) Nunca invente IDs. Sempre resolva previamente conforme abaixo.

    Como resolver IDs antes de chamar esta tool:
      - Se o usuário informar nomes: use find_task_by_title no database adequado ("trabalho" para work_tasks; "projetos" para project).
        • 1 resultado → use o id.
        • 0 ou >1 resultados → chame list_tasks no database adequado e RETORNE opções ao usuário para confirmar; não crie até confirmar.
      - Se o usuário informar um ID: valide com find_task_by_id; se não existir, retorne erro.

    Exemplos rápidos:
      - create_new_tasks("pessoal", {"name": "Planejar semana", "work_tasks": ["<WORK_TASK_ID_1>", "<WORK_TASK_ID_2>"], "start": "2025-11-15"})
      - create_new_tasks("trabalho", {"name": "Implementar feature X", "project": "<WORK_PROJECT_ID>", "priority": "High"})
      - create_new_tasks("projetos", {"name": "Site Novo", "tag": "Consultant", "status": "Planning"})

    Returns:
        dict: Objeto da página criada (id, properties, url, etc.) ou None em caso de erro.
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
