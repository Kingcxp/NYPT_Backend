from typing import List, Tuple, Set

from .types import *
from .RuleInterface import RuleInterface
from ....manager import logger


class CUPTRule(RuleInterface):
    player_master_times_in_1_round_config = 2
    player_master_times_in_1_match_config = 5
    player_rep_times_in_1_match_config = 3
    max_refuse_question_count = 5

    def __init__(self) -> None:
        self.question_count = 5
        self.ban_rule_list_config: List[Tuple[Any, Any]] = [
            (TeamType.REPORTER, QuestionType.REFUSED),
            (TeamType.REPORTER, QuestionType.REPORTED),
            (TeamType.OPPONENT, QuestionType.OPPOSED),
            (TeamType.OPPONENT, QuestionType.REPORTED)
        ]
        self.special_ban_list_config: List[Tuple[Any, Any]] = [
            (TeamType.REPORTER, QuestionType.REPORTED)
        ]

    def get_type() -> str:
        return "CUPT"

    def get_optional_question_id_list(
        self,
        rep_team_record_data_list: List[RecordData],
        opp_team_record_data_list: List[RecordData],
        used_question_id_list: List[int],
        question_id_lib_list: List[int],
        round_type: RoundType
    ) -> List[int]:
        """
        获取当前对局的可选赛题
        当前的比赛赛题禁选规则为：
        【不可解锁规则】：
        在同一轮对抗赛中，题目只能被陈述一次。
        【可解锁规则】：
        1. 正方作为正方拒绝过的题目
        2. 正方作为正方拒绝过的题目
        3. 反方作为反方挑战过的题目
        4. 反方作为正方陈述过的题目

        Args:
            rep_team_record_data_list (List[RecordData]): 正方队伍比赛记录
            opp_team_record_data_list (List[RecordData]): 反方队伍比赛记录
            used_question_id_list (List[int]): 当前比赛轮次中已用的赛题
            question_id_lib_list (List[int]): 赛题库
            round_type (RoundType): 本轮比赛类型 普通轮次或自选题轮次

        Returns:
            List[int]: 赛题编号列表 包含了当前对局中的全部可选题
        """
        if len(question_id_lib_list) > self.question_count:
            temp_question_id_lib_list = list(set(question_id_lib_list) - set(used_question_id_list))
            logger.opt(colors=True).info(f"<b>当前比赛可用题库为：</b><y>{temp_question_id_lib_list}</y>")
            rep_qrecord_set = set([
                (it.questionID, (TeamType.REPORTER, it.role)) for it in rep_team_record_data_list
            ])
            logger.opt(colors=True).info(f"<b>repQRecordSet = </b><y>{rep_qrecord_set}</y>")
            opp_qrecord_set = set([
                (it.questionID, (TeamType.OPPONENT, it.role)) for it in opp_team_record_data_list
            ])
            logger.opt(colors=True).info(f"<b>oppQRecordSet = </b><y>{opp_qrecord_set}</y>")
            ban_rule_list = self.ban_rule_list_config
            if round_type == RoundType.SPECIAL:
                logger.opt(colors=True).info(f"<b>自选题轮次</b>")
                logger.opt(colors=True).info(f"<b>getOptionalQuestionIDList(tempQuestionIDLibList, repQRecordSet, oppQRecordSet, banRuleList)</b>")
                logger.opt(colors=True).info(f"<b>tempQuestionIDLibList = </b><y>{temp_question_id_lib_list}</y>")
                logger.opt(colors=True).info(f"<b>repQRecordSet = </b><y>{rep_qrecord_set}</y>")
                logger.opt(colors=True).info(f"<b>oppQRecordSet = </b><y>{opp_qrecord_set}</y>")
                logger.opt(colors=True).info(f"<b>specialBanRuleListConfig = </b><y>{self.special_ban_list_config}</y>")
                return self.getOptionalQuestionIDList(
                    temp_question_id_lib_list,
                    rep_qrecord_set,
                    opp_qrecord_set,
                    self.special_ban_list_config
                )
            elif round_type == RoundType.NORMAL:
                optional_question_id_list: List[int] = None
                while True:
                    logger.opt(colors=True).info(f"<b>正常题轮次</b>")
                    logger.opt(colors=True).info(f"<b>getOptionalQuestionIDList(tempQuestionIDLibList, repQRecordSet, oppQRecordSet, banRuleList)</b>")
                    logger.opt(colors=True).info(f"<b>tempQuestionIDLibList = </b><y>{temp_question_id_lib_list}</y>")
                    logger.opt(colors=True).info(f"<b>repQRecordSet = </b><y>{rep_qrecord_set}</y>")
                    logger.opt(colors=True).info(f"<b>oppQRecordSet = </b><y>{opp_qrecord_set}</y>")
                    logger.opt(colors=True).info(f"<b>banRuleList = </b><y>{ban_rule_list}</y>")
                    optional_question_id_list = self.getOptionalQuestionIDList(
                        temp_question_id_lib_list,
                        rep_qrecord_set,
                        opp_qrecord_set,
                        ban_rule_list
                    )
                    ban_rule_list = ban_rule_list[:-1]
                    if optional_question_id_list.size >= self.question_count:
                        break
                return optional_question_id_list
        else:
            logger.opt(colors=True).warning(f"<r>赛题小于 <y>{self.question_count}</y> 道，无法进行赛题的禁用与解放</r>")
            return question_id_lib_list
        
    def getOptionalQuestionIDList(
        self,
        question_id_list: List[int],
        rep_qrecord_list: Set[Tuple[int, Tuple[Any, Any]]],
        opp_qrecord_list: Set[Tuple[int, Tuple[Any, Any]]],
        ban_rule_list: List[Tuple[Any, Any]]
    ) -> List[int]:
        """获取当前可选题的题号列表

        Args:
            question_id_list (List[int]): 题号列表
            rep_qrecord_list (Set[Tuple[int, Tuple[Any, Any]]]): 正方已比赛的题目记录
            opp_qrecord_list (Set[Tuple[int, Tuple[Any, Any]]]): 反方已比赛的题目记录
            ban_rule_list (List[Tuple[Any, Any]]): 题目禁选规则

        Returns:
            List[int]: 当前禁选规则下的可选题号列表
        """
        rep_ban_question_id_list = [it[0] for it in rep_qrecord_list if it[1] in ban_rule_list]
        logger.opt(colors=True).info(f"<b>repBanQuestionIDList = </b><y>{rep_ban_question_id_list}</y>")
        opp_ban_question_id_list = [it[0] for it in opp_qrecord_list if it[1] in ban_rule_list]
        logger.opt(colors=True).info(f"<b>oppBanQuestionIDList = </b><y>{opp_ban_question_id_list}</y>")
        return list(set(question_id_list) - set(rep_ban_question_id_list) - set(opp_ban_question_id_list))
    
    def get_valid_player_id_list(
        self,
        round_player_record_list: List[int],
        team_record_data_list: List[RecordData],
        player_data_list: List[PlayerData]
    ) -> List[int]:
        """
        获取当前对局的可上场队员
        当前队员禁上场规则为：
        1. 在每轮比赛中，每个队员最多只能主控2次
        2. 在整个比赛中，每个队员最多只能主控5次
        3. 在整个比赛中，每个队员最多只能正方陈述3次

        Args:
            round_player_record_list (List[int]): 当前比赛轮次中上场主控的队员记录
            team_record_data_list (List[RecordData]): 队伍比赛记录
            player_data_list (List[PlayerData]): 队伍的队员列表

        Returns:
            List[int]: 当前可主控队员 包含了此队伍的当前可上场主控的全部队员
        """
        _player_data_list = player_data_list[:]
        temp_player_data_list: List[PlayerData] = []
        for player_data in _player_data_list:
            player_master_times_in_1_round: int = len([it for it in round_player_record_list if it == player_data.id])
            logger.opt(colors=True).info(f"<b>playerData = </b><y>{player_data}</y><b>, playerMasterTimesIn1Round = </b><y>{player_master_times_in_1_round}</y>")
            if player_master_times_in_1_round < self.player_master_times_in_1_round_config:
                temp_player_data_list.append(player_data)
        _player_data_list = temp_player_data_list

        temp_player_data_list = []
        for player_data in _player_data_list:
            player_master_times_in_1_match: int = len([it for it in team_record_data_list if it.masterID == player_data.id and it.role in ("R", "O", "V")])
            logger.opt(colors=True).info(f"<b>playerData = </b><y>{player_data}</y><b>, playerMasterTimesIn1Round = </b><y>{player_master_times_in_1_match}</y>")
            if player_master_times_in_1_match < self.player_master_times_in_1_match_config:
                temp_player_data_list.append(player_data)
        _player_data_list = temp_player_data_list
        
        temp_player_data_list = []
        for player_data in _player_data_list:
            player_rep_times_in_1_match: int = len([it for it in team_record_data_list if it.masterID == player_data.id and it.role == "R"])
            logger.opt(colors=True).info(f"<b>playerData = </b><y>{player_data}</y><b>, playerRepTimesIn1Match = </b><y>{player_rep_times_in_1_match}</y>")
            if player_rep_times_in_1_match < self.player_rep_times_in_1_match_config:
                temp_player_data_list.append(player_data)
        _player_data_list = temp_player_data_list

        return [it.id for it in _player_data_list]
    
    def get_score(self, score_list: List[int]) -> float:
        """
        获取本阶段的得分
        5裁判 -> ((最高分 + 最低分) / 2 + 其他分数求和)
        7裁判 -> 去掉一个最高分，去掉一个最低分，再取平均分

        Args:
            score_list (List[int]): 分数列表 传入各裁判打分

        Returns:
            float: 分数 获取最后的统计分数
        """
        match(len(score_list)):
            case 5:
                sorted_score_list = sorted(score_list)
                min_score = sorted_score_list[0]
                max_score = sorted_score_list[-1]
                return (float(sum(sorted_score_list)) - float(min_score + max_score) / 2.0) / float(len(sorted_score_list) - 1)
            case 7:
                sorted_score_list = sorted(score_list)
                min_score = sorted_score_list[0]
                max_score = sorted_score_list[-1]
                return (float(sum(sorted_score_list)) - float(min_score + max_score)) / float(len(sorted_score_list) - 1)
            case _:
                logger.opt(colors=True).warning("<y>暂未提供其他裁判数下的统分规则，默认采用平均分机制</y>")
                return float(sum(score_list)) / float(len(score_list))
            
    def get_rep_score_weight(self, team_record_data_list: List[RecordData], is_refuse: bool) -> float:
        """
        Get rep score weight
        CUPT规则 最多拒绝5题，每多拒一题，扣0.2正方系数

        Args:
            team_record_data_list (List[RecordData]): 队伍比赛记录
            is_refuse (bool): 是否拒题

        Returns:
            float: 正方计分权重
        """
        logger.opt(colors=True).info(f"<b>getRepScoreWeight(teamRecordDataList: List<RecordData>, isRefuse: Boolean)</b>")
        logger.opt(colors=True).info(f"<b>teamRecordDataList = </b><y>{team_record_data_list}</y>")
        logger.opt(colors=True).info(f"<b>isRefuse = </b><y>{is_refuse}</y>")
        old_rep_score_weight_list = [it.weight for it in team_record_data_list if it.role in ("R", "X")]
        if len(old_rep_score_weight_list) == 0:
            logger.opt(colors=True).info("<b>return </b><y>3.0</y>")
            return 3.0
        else:
            old_rep_score_weight = min(old_rep_score_weight_list)
            refused_question_count = len([it for it in team_record_data_list if it.role == "X"])
            weight = old_rep_score_weight - 0.2 if is_refuse and refused_question_count >= self.max_refuse_question_count else old_rep_score_weight
            logger.opt(colors=True).info(f"<b>return </b><y>{weight}</y>")
            return weight
            
    def get_opp_score_weight(self) -> float:
        return 2.0
    
    def get_rev_score_weight(self) -> float:
        return 1.0
