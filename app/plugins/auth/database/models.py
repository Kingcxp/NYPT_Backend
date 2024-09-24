from sqlalchemy import Column, String, Integer

from ...utils.database import Base


class User(Base):
    """
    表: users

    字段：
        uid: 用户唯一标识
        name: 用户名，由后台确定，用户无法更改，登录标识，必须保证唯一，为避免输入麻烦尽量不使用中文
        email: 联系人邮箱，唯一标识
        token: 用户密码(base64编码)
        identity: 用户身份
        contact: 联系人名称(身份非队伍无效)
        leaders: 领队信息(身份非队伍无效)格式：姓名 - 性别 - 手机号 - 身份证号 - 学院 - 专业 - QQ - 邮箱
        members: 队员信息(身份非队伍无效)格式同领队信息，每个队员用 ' | ' 隔开
        award: 奖项信息(身份非队伍无效)
    """
    __tablename__ = "users"

    uid = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), unique=True)
    email = Column(String(256), unique=True)
    token = Column(String(1024))
    identity = Column(String(128))
    contact = Column(String(128))
    leaders = Column(String(4096))
    members = Column(String(4096))
    award = Column(String(10485760))