from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Set


@dataclass(slots=True, frozen=True)
class AppConfig:
    symbols: Set[str]
    host: str = "127.0.0.1"
    port: int = 7497
    client_id: int = 101
    exchange: str = "SMART"
    currency: str = "USD"
    snapshot: bool = False
    duration_seconds: int = 15
    generic_ticks: Set[str] = field(default_factory=set)
    log_level: str = "INFO"
    output_path: Optional[str] = None

    @property
    def generic_tick_list(self) -> str:
        return ",".join(sorted(self.generic_ticks))
