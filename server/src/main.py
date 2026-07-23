import sys
from pathlib import Path

from fastapi import FastAPI

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.modules.ast_parser.api import router as ast_parser_router
from app.modules.repository.api import router as repository_router
from app.modules.workspace.api import router as workspace_router

app = FastAPI(title="CodeCompass AI - Repository Import Service")

app.include_router(repository_router)
app.include_router(workspace_router)
app.include_router(ast_parser_router)



@app.get("/health")
def health():
    return {"status": "ok"}
