from enum import Enum
from typing import Optional, Dict, Any


class TeamType(Enum):
    REPORTER = 0
    OPPONENT = 1
    REVIEWER = 2
    OBSERVER = 3


class QuestionType(Enum):
    OPTIONAL = "P"
    REPORTED = "R"
    OPPOSED  = "O"
    REFUSED  = "X"
    BAN      = "B"


class RuleType(Enum):
    CUPT     = 0
    JSYPT    = 1


class RoundType(Enum):
    NORMAL   = "正常模式"
    SPECIAL  = "自选题模式"


class WorkMode(Enum):
    OFFLINE  = 0
    ONLINE   = 1


class RecordData:
    def __init__(self, dic: Optional[Dict[str, Any]] = None) -> None:
        self.round: int = 0
        self.phase: int = 0
        self.roomID: int = 0
        self.questionID: int = 0
        self.masterID: int = 0
        self.role: str = ""
        self.score: float = 0.0
        self.weight: float = 0.0

        if dic is not None:
            self.load_dict(dic)

    def get_dict(self) -> Dict[str, Any]:
        return {
            "round": self.round,
            "phase": self.phase,
            "roomID": self.roomID,
            "questionID": self.questionID,
            "masterID": self.masterID,
            "role": self.role,
            "score": self.score,
            "weight": self.weight
        }
    
    def load_dict(self, dic: Dict[str, Any]) -> None:
        self.round = dic.get("round", 0)
        self.phase = dic.get("phase", 0)
        self.roomID = dic.get("roomID", 0)
        self.questionID = dic.get("questionID", 0)
        self.masterID = dic.get("masterID", 0)
        self.role = dic.get("rold", "")
        self.score = dic.get("score", 0.0)
        self.weight = dic.get("weight", 0.0)


class PlayerData:
    def __init__(self, dic: Optional[Dict[str, Any]] = None) -> None:
        self.id: int = 0
        self.name: str = ""
        self.gender: str = ""
