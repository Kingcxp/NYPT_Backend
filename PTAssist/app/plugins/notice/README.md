# Notice Plugin
### Author: Kingcq

## Plugin Description
新闻插件，负责首页的滚动新闻信息展示
返回文件均为 `html` 文件，作为每一个新闻栏的 `innerHtml`

## Plugin Usage
Routers:
```
route:
    /notice/total
method:
    GET
input:
    None
output:
    200 OK:
        # total 总新闻数
        str(total): str

route:
    /notice/<int:page>
method:
    GET
input:
    page: int, 第 page 个新闻
output:
    200 OK:
        # lines 新闻正文（html）
        lines: str
    404 Not Found:
        "": str
```