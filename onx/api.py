from typing import Literal

from pydantic import BaseModel

from onx import settings


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
    operation: Literal["turn"] = "turn"
    payload: WsOperationPayload


class WsCookie(BaseModel):
    player_id: str
    grid_size: int = settings.DEFAULT_GRID_SIZE
    winning_length: int = settings.DEFAULT_WINNING_LENGTH
