from __future__ import annotations

from osint.core.algorithms.email import EmailCorrelationAlgorithm
from osint.core.algorithms.metadata import MetadataCorrelationAlgorithm
from osint.core.algorithms.network import NetworkCorrelationAlgorithm
from osint.core.algorithms.temporal import TemporalCorrelationAlgorithm
from osint.core.algorithms.username import UsernameCorrelationAlgorithm

__all__ = [
    "UsernameCorrelationAlgorithm",
    "EmailCorrelationAlgorithm",
    "MetadataCorrelationAlgorithm",
    "NetworkCorrelationAlgorithm",
    "TemporalCorrelationAlgorithm",
]
