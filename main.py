import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from personal_notion_agent.infrastructure.cors import setup_cors
from personal_notion_agent.routes.manager import manager

# Carregar variáveis de ambiente ANTES de inicializar observabilidade
load_dotenv()


app = FastAPI(title="Notion Manager Bot")

setup_cors(app)

app.include_router(manager, tags=["Manager"], prefix="/manager")


# Redirect root to docs
@app.get("/")
def docs():
    return RedirectResponse(url="/docs")


@app.get("/")
def read_root():
    return {"message": "Hello World from FastAPI on Vercel!"}


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
