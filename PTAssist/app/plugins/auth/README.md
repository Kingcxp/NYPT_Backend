# Auth Plugin
### Author: Kingcq

## Plugin Description
登录插件，负责储存用户信息，管理用户登录状态。

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
```
