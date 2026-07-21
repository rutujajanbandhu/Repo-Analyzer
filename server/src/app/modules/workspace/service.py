from typing import List

from app.modules.workspace.schemas import WorkspaceResponse


class WorkspaceService:
    def __init__(self) -> None:
        self._workspaces: List[dict] = []

    def create_workspace(self, name: str, owner_id: str, description: str | None = None) -> WorkspaceResponse:
        workspace = {
            "id": f"ws-{len(self._workspaces) + 1}",
            "name": name,
            "owner_id": owner_id,
            "description": description,
            "status": "active",
        }
        self._workspaces.append(workspace)
        return WorkspaceResponse(**workspace)

    def list_workspaces(self) -> List[WorkspaceResponse]:
        return [WorkspaceResponse(**workspace) for workspace in self._workspaces]
