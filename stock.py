import time
import json
from create_image import create_price_image
import moomoo as mm

from logger import Logger

class Stock(mm.StockQuoteHandlerBase):
    def __init__(self, ws=None, contexts={}):
        super().__init__()
        self.ws = ws
        self.contexts = contexts

        self.first = False
        self.last_values = {}

    def set_contexts(self, contexts):
        self.contexts = contexts
        self.quote_ctx.unsubscribe_all()
        self.quote_ctx.subscribe(list(set([i['symbol'] for i in contexts.values()])), [mm.SubType.QUOTE])

    def run(self):
        self.quote_ctx = mm.OpenQuoteContext()
        self.quote_ctx.set_handler(self)

    def on_recv_rsp(self, rsp_pb):
        ret, data = super().on_recv_rsp(rsp_pb)
        if ret != mm.RET_OK:
            Logger.error("データ受取エラー:", data)
            return

        for row in data.to_dict('records'):
            change = 0
            if self.last_values.get(row["code"]) is None:
                change = 0
            elif self.last_values.get(row["code"]) > row["last_price"]:
                change = -1
            elif self.last_values.get(row["code"]) < row["last_price"]:
                change = 1

            self.last_values[row["code"]] = row["last_price"]

            for context, setting in self.contexts.items():
                if setting['symbol'] == row['code']:
                    price = row[setting['col']]
                    image = create_price_image(price=price, change=change if setting['col'] == 'last_price' else 0)
                    self.ws.send(json.dumps({ 'event': 'setImage', 'context': context, 'payload': { 'image': f'{image}' } }))

    def close(self):
        self.quote_ctx.close()
