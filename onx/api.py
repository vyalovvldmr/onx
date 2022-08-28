from typing import Literal

from pydantic import BaseModel


class WsErrorEventPayload(BaseModel):
    message: str


class WsErrorEvent(BaseModel):
    event: Literal["error"] = "error"
    payload: WsErrorEventPayload


class WsGameStatePayload(BaseModel):
    whose_turn: str | None
    grid: list[int]
    winner: str | None
    status: int


class WsGameStateEvent(BaseModel):
    event: Literal["game_state"] = "game_state"
    payload: WsGameStatePayload


class WsEvent(BaseModel):
    data: WsGameStateEvent | WsErrorEvent


class WsOperationPayload(BaseModel):
    turn: int


class WsOperation(BaseModel):
    operation: str = "turn"
    payload: WsOperationPayload
