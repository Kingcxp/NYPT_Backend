# _template Plugin
### Author: Kingcq

## Plugin Desctiption
插件模板，仅作参考用，在 `manager.py` 中设置了规则，文件夹名前面带 `_` 的插件会被忽略，在服务启动后的日志里也能看到

## Plugin Usage
Routers:
```
route:
    /template
method:
    GET
input:
    None
output:
    str: "This is a template plugin."
```

Commands:
```
command:
    template-test
usage:
    template-test
output:
    str: "Template test command!"
```