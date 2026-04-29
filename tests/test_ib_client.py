import asyncio

from gstrading.config import AppConfig
from gstrading.ib_client import AsyncIBMarketDataClient, MarketSnapshot


def test_market_data_client_updates_bid_and_ask() -> None:
    loop = asyncio.new_event_loop()
    try:
        client = AsyncIBMarketDataClient(AppConfig(symbols={"AAPL"}), loop)
        client._request_id_to_symbol[1] = "AAPL"

        client.tickPrice(1, 1, 184.25, None)
        client.tickPrice(1, 2, 184.30, None)

        snapshot = client._latest_by_symbol["AAPL"]
        assert snapshot.bid == 184.25
        assert snapshot.ask == 184.30
    finally:
        loop.close()


def test_consume_stops_cleanly_after_duration_when_data_was_received() -> None:
    async def runner() -> None:
        config = AppConfig(symbols={"AAPL"}, duration_seconds=1)
        client = AsyncIBMarketDataClient(config, asyncio.get_running_loop())
        await client.queue.put(MarketSnapshot(symbol="AAPL", timestamp=1.0, last=184.25))
        await client.consume()

    asyncio.run(runner())


def test_consume_times_out_when_no_data_is_received() -> None:
    async def runner() -> None:
        config = AppConfig(symbols={"AAPL"}, duration_seconds=1)
        client = AsyncIBMarketDataClient(config, asyncio.get_running_loop())
        try:
            await client.consume()
        except TimeoutError as exc:
            assert "No market data received within timeout for symbols: AAPL" in str(exc)
        else:
            raise AssertionError("Expected TimeoutError when no market data is received.")

    asyncio.run(runner())
