from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json

class Node:
    def __init__(self, id: str, type: str, name: str, properties: Dict[str, Any] = None):
        self.id = id
        self.type = type
        self.name = name
        self.properties = properties or {}

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "properties": self.properties
        }

class Edge:
    def __init__(self, id: str, type: str, source: str, target: str, properties: Dict[str, Any] = None):
        self.id = id
        self.type = type
        self.source = source
        self.target = target
        self.properties = properties or {}

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "target": self.target,
            "properties": self.properties
        }

class BaseConnector(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> tuple[List[Node], List[Edge]]:
        """
        Parses a configuration file and returns a list of Nodes and Edges.
        """
        pass
