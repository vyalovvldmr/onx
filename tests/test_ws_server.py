import json
import unittest
import uuid

from aiohttp.test_utils import AioHTTPTestCase

from onx.server.app import get_application
from onx.server.game import BoxType
from onx.server.game import GameStatus
from onx.server.game import Player


class WebsocketServerTestCase(AioHTTPTestCase):
    async def get_application(self):
        return get_application()

    async def connect_player(self, player_id=None):
        player_id = player_id or str(uuid.uuid4())
        ws = await self.client.ws_connect(
            "/ws",
            headers={"Cookie": f"player_id={player_id}"},
        )
        return Player(id=player_id, ws=ws)

    async def connect_players(self):
        self.players = [await self.connect_player(), await self.connect_player()]
        self.assertDictEqual(
            json.loads((await self.players[0].ws.receive()).data),
            {
                "data": {
                    "payload": {
                        "whose_turn": None,
                        "grid": [BoxType.empty] * 9,
                        "winner": None,
                        "status": GameStatus.awaiting,
                    },
                    "event": "game_state",
                }
            },
        )

        response = json.loads((await self.players[0].ws.receive()).data)
        self.assertDictEqual(
            response, json.loads((await self.players[1].ws.receive()).data)
        )

        whose_turn = response["data"]["payload"]["whose_turn"]
        if self.players[0].id == whose_turn:
            self.acting, self.awaiting = self.players
        else:
            self.awaiting, self.acting = self.players

    async def turn(self, box_num, expected_game_status, expected_winner=None):
        await self.acting.ws.send_json(
            {"operation": "turn", "payload": {"turn": box_num}}
        )

        response_1 = json.loads((await self.acting.ws.receive()).data)
        response_2 = json.loads((await self.awaiting.ws.receive()).data)
        self.assertDictEqual(response_1, response_2)

        self.assertTrue(response_1["data"]["payload"]["grid"][box_num] != BoxType.empty)
        self.assertTrue(response_1["data"]["payload"]["winner"] == expected_winner)
        self.assertTrue(response_1["data"]["payload"]["status"] == expected_game_status)

        whose_turn = response_1["data"]["payload"]["whose_turn"]
        if self.players[0].id == whose_turn:
            self.acting, self.awaiting = self.players
        else:
            self.acting, self.awaiting = self.players[::-1]

    async def force_reconnect_random_player(self):
        player = self.players[0]
        await player.ws.close()
        if self.acting.id == player.id:
            self.players[0] = self.acting = await self.connect_player(player.id)
        else:
            self.players[0] = self.awaiting = await self.connect_player(player.id)
        response_1 = json.loads((await self.players[0].ws.receive()).data)
        response_2 = json.loads((await self.players[1].ws.receive()).data)
        self.assertDictEqual(response_1, response_2)

    async def test_winning_the_game(self):
        await self.connect_players()

        await self.turn(box_num=0, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=1, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=3, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=4, expected_game_status=GameStatus.in_progress)
        await self.turn(
            box_num=6,
            expected_game_status=GameStatus.finished,
            expected_winner=self.acting.id,
        )

    async def test_drawn_game(self):
        await self.connect_players()

        await self.turn(box_num=0, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=1, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=2, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=4, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=7, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=6, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=8, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=5, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=3, expected_game_status=GameStatus.finished)

    async def test_retrieve_game_after_disconnection(self):
        await self.connect_players()

        await self.turn(box_num=0, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=1, expected_game_status=GameStatus.in_progress)
        await self.force_reconnect_random_player()
        await self.turn(box_num=3, expected_game_status=GameStatus.in_progress)
        await self.turn(box_num=4, expected_game_status=GameStatus.in_progress)
        await self.turn(
            box_num=6,
            expected_game_status=GameStatus.finished,
            expected_winner=self.acting.id,
        )

    async def test_player_id_cookie_required_error(self):
        ws = await self.client.ws_connect("/ws")
        response_1 = json.loads((await ws.receive()).data)
        self.assertDictEqual(
            response_1,
            {
                "data": {
                    "event": "error",
                    "payload": {
                        "message": "('player_id',) field required value_error.missing"
                    },
                }
            },
        )

    async def test_not_your_turn_error(self):
        await self.connect_players()
        await self.awaiting.ws.send_json({"operation": "turn", "payload": {"turn": 0}})
        response = json.loads((await self.awaiting.ws.receive()).data)
        self.assertDictEqual(
            response,
            {"data": {"event": "error", "payload": {"message": "not your turn error"}}},
        )

    async def test_box_is_not_empty_error(self):
        await self.connect_players()
        await self.turn(box_num=0, expected_game_status=GameStatus.in_progress)
        await self.acting.ws.send_json({"operation": "turn", "payload": {"turn": 0}})
        response = json.loads((await self.acting.ws.receive()).data)
        self.assertDictEqual(
            response,
            {
                "data": {
                    "event": "error",
                    "payload": {"message": "box is not empty error"},
                }
            },
        )

    async def test_invalid_turn_number_error(self):
        await self.connect_players()
        await self.turn(box_num=0, expected_game_status=GameStatus.in_progress)
        await self.acting.ws.send_json({"operation": "turn", "payload": {"turn": 200}})
        response = json.loads((await self.acting.ws.receive()).data)
        self.assertDictEqual(
            response,
            {
                "data": {
                    "event": "error",
                    "payload": {"message": "invalid turn number error"},
                }
            },
        )

    async def test_turn_without_second_player_error(self):
        player = await self.connect_player()
        await player.ws.receive()
        await player.ws.send_json({"operation": "turn", "payload": {"turn": 1}})
        response = json.loads((await player.ws.receive()).data)
        self.assertDictEqual(
            response,
            {
                "data": {
                    "event": "error",
                    "payload": {"message": "turn without second player error"},
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
