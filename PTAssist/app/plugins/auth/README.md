# Auth Plugin
### Author: Kingcq

## Plugin Description
登录插件，负责储存用户信息，管理用户登录状态。
大概的报名流程：
1，参赛队员在指定网站上注册，登记姓名，学校，队伍名，邮箱，手机号。发起注册申请。
2，我们后台记录下来，工作人员审核注册信息，同意后，发邮件告知账号创建成功。
3，然后参赛队员开始填写相关的参赛信息。

在第二步里，就是会涉及，是我们重新分配一个账号，还是用原有账号填写。如果重新分配账号，就有一个好处，在这个阶段就可以给队伍进行匿名，告知对方队伍编号，还可以按照报名顺序给编号。

## Plugin Usage
Routers:
```
route:
    /auth/id
method:
    GET
input:
    None
output:
    200 OK:
        # user_id: 用户标识
        {user_id: int}
    400 Bad Request:
        # msg: 错误信息
        {msg: str}

route:
    /auth/logout
method:
    GET
input:
    None
output:
    200 OK:
        {}
    400 Bad Request:
        # msg: 错误信息
        {msg: str}

route:
    /auth/login
method:
    POST
input:
    {
        "name": str(对应数据表中的 REALNAME)
        "token": str(双层加密后的密码)
        "salt": str(加密密码中加的盐)
    }
output:
    200 OK:
        {}
    400 Bad Request:
        # msg: 错误信息
        {msg: str}

route:
    /auth/register
method:
    POST
input:
    {
        "school": str(学校名称)
        "name": str(队伍名称或志愿者名称)
        "email": str(邮箱地址)
        "tel": str(电话号码)
        "identity": str(用户身份)
        "captcha": str(验证码)
        "contact": str(联系人姓名，identity为Team时才存在)
    }
output:
    200 OK:
        {}
    400 Bad Request:
        # msg: 错误信息
        {msg: str}

route:
    /auth/userdata/<str:which>
method:
    GET
input:
    which 共有如下几种，其它的均无效
    user_id: UID
    user_name: NAME
    real_name: REALNAME
    tags: TAGS
    identity: IDENTITY
    leader: LEADER
    member: MEMBER
    award: AWARD
    all: 除 TOKEN 和 AWARD 外全部字段
output:
    200 OK:
        {根据 which 具体内容给定同样的字段，详见代码注释}
    400 Bad Request:
        # msg: 错误信息
        {msg: str}
    500 Internal Server Error:
        # msg: 错误信息
        {msg: str}
    404 Not Found:
        # msg: 错误信息
        {msg: str}
```

Commands:
```
command:
    new-user
description:
    创建一个新用户
usage:
    new-user <realname> <email> <password> [-identity=<identity>]
output:
    为数据库添加一条新的用户记录

command:
    delete-user
description:
    删除一个已存在的用户
usage:
    delete-user -id=<uid> 或者 delete-user -realname=<realname>  或者 delete-user -email=<email>
output:
    删除一条现存的符合条件的数据库记录

command:
    add-tag
description:
    为指定用户添加一个标签
usage:
    add-tag -id=<uid> <tag> 或者 add-tag -realname=<realname> <tag> 或者 add-tag -email=<email> <tag>
output:
    修改指定的记录行的 tag 字段

command:
    remove-tag
description:
    为指定用户移除一个标签
usage:
    remove-tag -id=<uid> <tag> 或者 remove-tag -realname=<realname> <tag> 或者 remove-tag -email=<email> <tag>
output:
    修改指定的记录行的 tag 字段

command:
    set-identity
description:
    为指定用户更改身份
usage:
    set-identity -id=<uid> <identity> 或者 set-identity -realname=<realname> <identity> 或者 set-identity -email=<email> <identity>
output:
    修改指定的记录行的 identity 字段

command:
    set-password
description:
    为指定用户更改密码
usage:
    set-password -id=<uid> <password> 或者 set-password -realname=<realname> <password> 或者 set-password -email=<email> <password>
output:
    修改指定的记录行的 password 字段

command:
    show-password
description:
    展示指定用户的密码
usage:
    show-password -id=<uid> 或者 show-password -realname=<realname> 或者 show-password -email=<email>
output:
    指定用户的密码

command:
    set-realname
description:
    为指定用户更改标识
usage:
    set-realname -id=<uid> <realname> 或者 set-realname -realname=<old_realname> <new_realname> 或者 set-realname -email=<email> <realname>
output:
    修改指定的记录行的 realname 字段

command:
    set-name
description:
    为指定用户更改用户名
usage:
    set-name -id=<uid> <name> 或者 set-name -realname=<realname> <name> 或者 set-name -email=<email> <name>
output:
    修改指定的记录行的 name 字段

command:
    user-info
description:
    获取指定用户的信息
usage:
    user-info -id=<uid> 或者 user-info -realname=<realname> 或者 user-info -email=<email>
output:
    输出指定用户的所有字段信息（除奖项信息以外，因为还没有确定奖项的存储形式，大概是奖状图片的base64字符串，长的一批根本没法展示在命令行中）

command:
    list-requests
description:
    列出所有的注册请求
usage:
    list-requests
output:
    所有请求的信息

command:
    accept-request
description:
    通过指定的请求，自动创建账号，并通过邮件告知用户
usage:
    accept-request -id=<rid>
output:
    指令执行是否成功及错误原因

command:
    reject-request
description:
    拒绝指定的请求，并通过邮件告知用户
usage:
    reject-request -id=<rid> [拒绝理由]
output:
    指令是否执行成功及错误原因

command:
    list-teams
description:
    获取 identity 为 Team 的用户信息
usage:
    list-teams
output:
    所有队伍的基础信息，要想详细查看，请借助这些信息使用 user-info 命令查找

command:
    list-volunteers
description:
    列出所有的指定类型志愿者
usage:
    list-volunteers -type=<type>
output:
    所有指定身份类型的志愿者的基础信息，要想详细查看，请借助这些信息使用 user-info 命令查找

command:
    list-all
description:
    同上，但列出所有用户，无论身份类型
usage:
    list-all
output:
    所有用户的基础信息
```
