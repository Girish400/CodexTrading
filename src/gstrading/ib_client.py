from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Set

from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.ticktype import TickTypeEnum
from ibapi.wrapper import EWrapper

from gstrading.config import AppConfig

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class MarketSnapshot:
    symbol: str
    timestamp: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    close: Optional[float] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    last_size: Optional[int] = None
    volume: Optional[int] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


class AsyncIBMarketDataClient(EWrapper, EClient):
    def __init__(self, config: AppConfig, loop: asyncio.AbstractEventLoop) -> None:
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.config = config
        self.loop = loop
        self.queue: asyncio.Queue[MarketSnapshot] = asyncio.Queue()
        self._api_thread: Optional[threading.Thread] = None
        self._connected_event = threading.Event()
        self._disconnect_requested = threading.Event()
        self._request_id_to_symbol: dict[int, str] = {}
        self._latest_by_symbol: dict[str, MarketSnapshot] = {}
        self._output_path = Path(config.output_path) if config.output_path else None
        self._seen_symbols: Set[str] = set()
        self._received_data = False

    def nextValidId(self, order_id: int) -> None:  # noqa: N802
        LOGGER.debug("Received next valid id: %s", order_id)
        self._connected_event.set()

    def error(
        self,
        req_id: int,
        error_code: int,
        error_string: str,
        advanced_order_reject_json: str = "",
    ) -> None:
        level = logging.WARNING
        if error_code in {2104, 2106, 2158}:
            level = logging.INFO
        LOGGER.log(
            level,
            "IB error reqId=%s code=%s message=%s details=%s",
            req_id,
            error_code,
            error_string,
            advanced_order_reject_json,
        )

    def tickPrice(self, req_id: int, tick_type: int, price: float, attrib) -> None:  # noqa: N802
        symbol = self._request_id_to_symbol.get(req_id)
        if symbol is None or price <= 0:
            return
        label = TickTypeEnum.to_str(tick_type)
        snapshot = self._get_snapshot(symbol)
        snapshot.timestamp = time.time()
        if label == "BID":
            snapshot.bid = price
        elif label == "ASK":
            snapshot.ask = price
        elif label == "LAST":
            snapshot.last = price
        elif label == "CLOSE":
            snapshot.close = price
        self._publish_snapshot(snapshot)

    def tickSize(self, req_id: int, tick_type: int, size: int) -> None:  # noqa: N802
        symbol = self._request_id_to_symbol.get(req_id)
        if symbol is None or size < 0:
            return
        label = TickTypeEnum.to_str(tick_type)
        snapshot = self._get_snapshot(symbol)
        snapshot.timestamp = time.time()
        if label == "BID_SIZE":
            snapshot.bid_size = size
        elif label == "ASK_SIZE":
            snapshot.ask_size = size
        elif label == "LAST_SIZE":
            snapshot.last_size = size
        elif label == "VOLUME":
            snapshot.volume = size
        self._publish_snapshot(snapshot)

    def connect_and_start(self) -> None:
        LOGGER.info(
            "Connecting to Interactive Brokers at %s:%s with client id %s",
            self.config.host,
            self.config.port,
            self.config.client_id,
        )
        self.connect(self.config.host, self.config.port, self.config.client_id)
        self._api_thread = threading.Thread(target=self.run, name="ibapi-thread", daemon=True)
        self._api_thread.start()
        if not self._connected_event.wait(timeout=10):
            raise TimeoutError("Timed out waiting for Interactive Brokers API connection.")

    def request_market_data(self) -> None:
        for request_id, symbol in enumerate(sorted(self.config.symbols), start=1):
            contract = self._build_stock_contract(symbol)
            self._request_id_to_symbol[request_id] = symbol
            LOGGER.info("Subscribing to market data for %s", symbol)
            self.reqMktData(
                request_id,
                contract,
                self.config.generic_tick_list,
                self.config.snapshot,
                False,
                [],
            )

    def disconnect_and_stop(self) -> None:
        if self._disconnect_requested.is_set():
            return
        self._disconnect_requested.set()
        try:
            for request_id in list(self._request_id_to_symbol):
                self.cancelMktData(request_id)
        finally:
            self.disconnect()
        if self._api_thread and self._api_thread.is_alive():
            self._api_thread.join(timeout=5)

    async def consume(self) -> None:
        start_time = self.loop.time()
        while True:
            elapsed = self.loop.time() - start_time
            timed_out = elapsed >= self.config.duration_seconds
            if not self.config.snapshot and timed_out:
                duration_seconds = self.config.duration_seconds
                LOGGER.info("Reached requested duration of %s seconds", duration_seconds)
                break

            wait_timeout = 10.0
            if not self.config.snapshot:
                remaining = self.config.duration_seconds - elapsed
                wait_timeout = max(0.0, min(wait_timeout, remaining))
                if wait_timeout == 0.0:
                    continue

            try:
                snapshot = await asyncio.wait_for(self.queue.get(), timeout=wait_timeout)
            except TimeoutError as exc:
                if self._received_data and not self.config.snapshot:
                    LOGGER.info("No additional market data received before session end.")
                    break
                symbols = ",".join(sorted(self.config.symbols))
                message = f"No market data received within timeout for symbols: {symbols}"
                raise TimeoutError(message) from exc

            self._received_data = True
            self._write_snapshot(snapshot)
            self._log_snapshot(snapshot)
            if self.config.snapshot:
                self._seen_symbols.add(snapshot.symbol)
                if self._seen_symbols >= self.config.symbols:
                    break

    def _build_stock_contract(self, symbol: str) -> Contract:
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = self.config.exchange
        contract.currency = self.config.currency
        return contract

    def _get_snapshot(self, symbol: str) -> MarketSnapshot:
        snapshot = self._latest_by_symbol.get(symbol)
        if snapshot is None:
            snapshot = MarketSnapshot(symbol=symbol, timestamp=time.time())
            self._latest_by_symbol[symbol] = snapshot
        return snapshot

    def _publish_snapshot(self, snapshot: MarketSnapshot) -> None:
        cloned = MarketSnapshot(**asdict(snapshot))
        self.loop.call_soon_threadsafe(self.queue.put_nowait, cloned)

    def _log_snapshot(self, snapshot: MarketSnapshot) -> None:
        LOGGER.info(
            "symbol=%s last=%s bid=%s ask=%s volume=%s",
            snapshot.symbol,
            snapshot.last,
            snapshot.bid,
            snapshot.ask,
            snapshot.volume,
        )

    def _write_snapshot(self, snapshot: MarketSnapshot) -> None:
        if self._output_path is None:
            return
        self._output_path.parent.mkdir(parents=True, exist_ok=True)
        with self._output_path.open("a", encoding="utf-8") as handle:
            handle.write(snapshot.to_json())
            handle.write("\n")
