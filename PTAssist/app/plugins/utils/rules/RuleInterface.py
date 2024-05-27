from typing import List
from abc import ABCMeta, abstractmethod

from .types import *


class RuleInterface(metaclass=ABCMeta):
    @abstractmethod
    def get_optional_question_id_list(
        self,
        rep_team_record_data_list: List[RecordData],
        opp_team_record_data_list: List[RecordData],
        used_question_id_list: List[int],
        question_id_lib_list: List[int],
        round_type: RoundType
    ) -> List[int]:
        """获取当前对局的可选赛题

        Args:
            rep_team_record_data_list (List[RecordData]): 正方队伍比赛记录
            opp_team_record_data_list (List[RecordData]): 反方队伍比赛记录
            used_question_id_list (List[int]): 当前比赛轮次中已用的赛题
            question_id_lib_list (List[int]): 赛题库
            round_type (RoundType): 本轮比赛类型 普通轮还是自选题轮

        Returns:
            List[int]: 赛题编号列表 包含了当前对局中的全部可选题
        """
        pass

    def get_valid_player_id_list(
        self,
        round_player_record_list: List[int],
        team_record_data_list: List[RecordData],
        player_data_list: List[PlayerData]
    ) -> List[int]:
        """获取当前对局的可上场队员

        Args:
            round_player_record_list (List[int]): 当前比赛轮次中上场主控的队员记录
            team_record_data_list (List[RecordData]): 队伍比赛记录
            player_data_list (List[PlayerData]): 队伍的队员列表

        Returns:
            List[int]: 当前可主控队员 包含了此队伍的当前可上场主控的全部队员
        """
        pass

    def get_score(self, score_list: List[int]) -> float:
        """获取本阶段的得分

        Args:
            score_list (List[int]): 分数列表 传入各裁判打分

        Returns:
            float: 分数 获取最后的统计分数
        """
        pass

    def get_rep_score_weight(
        self,
        team_record_data_list: List[RecordData],
        is_refuse: bool
    ) -> float:
        """Get rep score weight

        Args:
            team_record_data_list (List[RecordData]): 队伍比赛记录
            is_refuse (bool): 是否拒题

        Returns:
            float: 正方计分权重
        """
        pass

    def get_opp_score_weight(
        self,
    ) -> float:
        """Get opp score weight

        Args:
            refused_question_id_list (List[RecordData]): 拒绝的题号列表

        Returns:
            float: 反方计分权重
        """
        pass

    def get_rev_score_weight(
        self,
    ) -> float:
        """Get rev score weight

        Args:
            refused_question_id_list (List[RecordData]): 拒绝的题号列表

        Returns:
            float: 评方计分权重
        """
        pass
