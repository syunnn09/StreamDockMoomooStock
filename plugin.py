import json
import threading
from stock import Stock
import websocket
from typing import Any, Dict

from logger import Logger

class Plugin:
    """Stream Dock プラグインのコア クラスは、WebSocket 接続の管理と Stream Dock イベントの処理を担当します。

    このクラスは、Stream Dock ソフトウェアとの WebSocket 接続を維持し、さまざまなイベント (ボタンの出現、消滅、設定の変更など) を処理します。
    そしてプラグインのアクション(Action)インスタンスを管理します。各アクション インスタンスは、Stream Dock インターフェイスのボタンに対応します。
    """

    stock: Stock = None

    def __init__(self, port: int, plugin_uuid: str, event: str, info: Dict[str, Any]):
        """プラグインインスタンスの初期化

        Args:
            port: WebSocketサーバーのポート番号
            plugin_uuid: プラグインの一意の識別子
            event: イベントの種類
            info: プラグイン情報を含むオブジェクト
        """
        self.plugin_uuid = plugin_uuid

        self.contexts = {}

        self.ws = websocket.WebSocketApp(
            f'ws://127.0.0.1:{port}',
            on_open=lambda ws: self._on_open(ws, event, plugin_uuid),
            on_message=self._on_message,
            on_error=lambda ws, error: Logger.error(f"WebSocket error: {error}")
        )
        threading.Thread(target=self.ws.run_forever, daemon=True).start()

        self.stock = Stock(self.ws)
        threading.Thread(target=self.stock.run, daemon=True).start()

    def _on_open(self, ws, event: str, plugin_uuid: str):
        """WebSocket接続確立時のコールバック関数
        プラグインを Stream Dock に登録し、初期化イベントを送信します。

        Args:
            ws: WebSocket接続インスタンス
            event: イベントタイプ
            plugin_uuid: プラグインの UUID
        """

        ws.send(json.dumps({'event': event, 'uuid': plugin_uuid}))

    def _on_message(self, ws, message):
        """ストリーム ドックから受信した WebSocket メッセージを処理します

        受信したイベント タイプに基づいて、次のような対応する操作を実行します：
        - グローバル設定の更新を処理する
        - ボタンの出現/消滅イベントを処理する
        - ハンドルボタンの設定変更
        - タイトルパラメータの変更を処理します

        Args:
            ws: WebSocket接続インスタンス
            message: 受信した JSON メッセージ
        """
        data = json.loads(message)
        event = data.get('event')

        if event == 'willAppear':
            setting = self.get_setting(data)
            self.contexts[data['context']] = setting
            self.stock.set_contexts(self.contexts)
            self.ws.send(json.dumps({ 'event': 'setTitle', 'context': data['context'], 'payload': { 'title': setting['symbol'].replace('US.', '') } }))

        if event == 'willDisappear':
            del self.contexts[data['context']]

        if event == 'didReceiveSettings':
            setting = self.get_setting(data)
            self.contexts[data['context']] = setting
            self.stock.set_contexts(self.contexts)
            self.ws.send(json.dumps({ 'event': 'setTitle', 'context': data['context'], 'payload': { 'title': setting['symbol'].replace('US.', '') } }))

    def get_setting(self, data):
        payload = data.get('payload', {})
        settings = payload.get('settings', {})
        symbol = settings.get('symbol', 'US.SPCX')
        col = settings.get('col', 'last_price')
        return { 'symbol': symbol, 'col': col }
