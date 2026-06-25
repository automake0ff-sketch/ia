"""
BaseAgent: clase base para todos los agentes del sistema multi-agente.
Cada agente tiene una responsabilidad única (principio de responsabilidad
única aplicado a agentes) y expone un método `run` como punto de entrada.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    name: str = "BaseAgent"

    def __init__(self):
        self.logger = logging.getLogger(f"agents.{self.name}")

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        ...

    def log_start(self, detail: str = "") -> None:
        self.logger.info("[%s] iniciando. %s", self.name, detail)

    def log_end(self, detail: str = "") -> None:
        self.logger.info("[%s] finalizado. %s", self.name, detail)

    def log_error(self, exc: Exception) -> None:
        self.logger.error("[%s] error: %s", self.name, exc)
