# NYPT

### By Kingcq 2024.5.31

## 介绍
TODO

## 运行项目测试服务器
首先，你需要自行安装 git 版本控制工具、 python >= 3.10（低于该版本没试过，如可行也可）以及对应的 pip3 包管理器
之后，使用接下来的一连串命令来安装项目依赖：
```sh
git clone https://github.com/Kingcq/NYPT_Frontend.git
cd NYPT_Frontend
# 如果你的 pip 下载速度慢到了一定境界，你也许需要更换镜像源以获取极速体验：
pip config set global.index-url https://mirror.nju.edu.cn/pypi/web/simple
# 安装虚拟环境管理工具
pip install pyvenv
# 如果你正在使用禁止 pip 直接在全局安装的系统，请自行安装 python3-venv，例如 Debian
sudo apt install python3-venv

# 之后使用 venv 来管理虚拟环境，如果你会使用其他的虚拟环境管理工具，请自行替换
python3 -m venv serverenv
# 针对不同的系统类型，激活该虚拟环境
# Windows Powershell
.\serverenv\Scripts\Activate.ps1
# Bash
source serverenv/bin/activate
# Fish
source serverenv/bin/activate.fish

# 如果你需要使用邮箱功能，请新建 .env 文件，并设定类似下文注释中的环境变量，项目会自动加载
touch .env
vi .env
# .env
# EMAIL="your_email@address.com" # 如 123456789@163.com
# EMAIL_PASSKEY="your_smtp_passkey"
# EMAIL_HOST="your_smtp_host" # 如 smtp.163.com

# 安装依赖
pip install -r requirements.txt
# 启动项目
uvicorn app:app --host 0.0.0.0 --port 8081 --reload
# 如果你觉得 watchdog 一检测到文件就重启太烦了，你可以去掉 --reload 参数
```
之后，你可以在浏览器中访问 [http://localhost:8081/docs](http://localhost:8081/docs) 来查看项目 api 文档

如果你同时打开了前端测试服务器，它默认开启了反向代理，你也能通过 [http://localhost:5173/api/docs](http://localhost:5173/api/docs) 访问到同样的页面

## 关于 `.env` 文件配置
.env 文件目前包含邮箱配置和管理员密码配置两部分

当创建 .env 之后，我们希望看到类似如下内容：
```sh
# 当初始化用户数据库时，会自动创建第一个管理员账号，密码为这个环境变量设置的内容
ADMIN_PASSWORD="adminpass"

# 邮箱配置，如果你想要启用发送邮件的功能，你必须配置这个内容
EMAIL="your_email@address.com"
EMAIL_PASSKEY="your_smtp_passkey"
EMAIL_HOST="your_smtp_host"
```

## 关于其他插件可能需要修改的地方
### 1. PTAssist(app/plugins/PTAssist)
在 PTAssist 插件中，你需要修改 `config.py` 文件中的一些常量变量，使其指向你想要的存放比赛规则模板的路径

### 2. notice(app/plugins/notice)
在 notice 插件中，你需要修改 `notices/` 文件夹下的文件，依照 `notice{id}.html` 的格式一次编写 `.html` 文件，它会被按照顺序检测为首页的公告版面，编号从 `1` 开始，如果跳过某个编号，则之后的公告会被忽略
