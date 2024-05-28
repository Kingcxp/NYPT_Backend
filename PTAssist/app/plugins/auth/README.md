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
```

Commands:
```
```