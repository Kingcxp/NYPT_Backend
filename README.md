# NYPT

### By Kingcq 2024.5.31

## 介绍
TODO

## 测试运行项目
```
# 你应当在此之前先安装 python3 和 pip，或使用 python 的虚拟环境
pip install -r requirements.txt
python NYPT/launcher.py
```

## 软件架构
本项目暂时为网络应用项目，目前分为前端、后端以及衍生项目  
前端使用Node.js、Vue、Axios、Javascript、HTML、CSS、Element UI等组成成分，构建出造型美观，使用方便流畅的网页用户界面。  
后端使用Flask、pymysql等python软件包，构建一个完整的网络数据存取体系以及后台数据操作体系，为服务器的正常运行保驾护航。

## 环境配置教程
组内各成员使用的操作系统不同，  
我们根据成员可能使用的所有操作系统种类将安装方式分为以下几种类型：  
实际上，我们只关注一些关键内容的安装，其余小组成员可以自行安装。  
Vue项目初始化导引：[菜鸟教程](https://www.runoob.com/vue3/vue3-install.html)，别忘了安装axios和element-plus

## 1. Windows  
    对于Node.js安装：  
    前往[Node.js](https://nodejs.org/en)官网安装[18.16.1 LTS](https://nodejs.org/dist/v18.16.1/node-v18.16.1-x64.msi)版本，并基于此npm版本自行安装Vue、Axios等组分。  
    Node版本在之后可能有更新的选择，可以在不影响项目构建的情况下安装更新的版本。
    对于Python安装：  
    建议[Python](https://www.python.org/downloads/)版本为python3.10.x或者python3.9.x，这两个版本更加稳定，且不包含3.11.x及其之后的一些软件包的破坏性更新。不过实际上版本可在一定范围内随意，能用即可  

## 2. Chrome OS / Debian
    根据[Node.js Binary Distributions](https://github.com/nodesource/distributions)能找到，要安装Node.js LTS(v18.x)，对于Debian操作系统，需要执行如下指令：

    ```sh
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo bash - &&\
    sudo apt-get install -y nodejs
    ```

    卸载Node.js：  
    如果你不小心搞出了问题，你需要卸载掉npm并重新下载，则使用如下指令：

    ```sh
    sudo apt-get purge nodejs &&\
    sudo rm -r /etc/apt/sources.list.d/nodesource.list
    ```

## 3. Ubuntu
    根据[Node.js Binary Distributions](https://github.com/nodesource/distributions)能找到，要安装Node.js LTS(v18.x)，对于Ubuntu操作系统，需要执行如下指令：

    ```sh
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - &&\
    sudo apt-get install -y nodejs
    ```

    卸载Node.js：  
    如果你不小心搞出了问题，你需要卸载掉npm并重新下载，则使用如下指令：

    ```sh
    sudo apt-get purge nodejs &&\
    sudo rm -r /etc/apt/sources.list.d/nodesource.list
    ```

## 4. Chrome OS / Debian / Ubuntu
   之后一些环境的配置在这些系统上一致，所以在此合并。  
   对于Python安装：  
    直接使用apt安装即可  
    之后后端编写者可通过命令

    ```sh
    pip install -r requirements.txt
    ```

    来一键补全未安装的python软件包。

## 使用说明
因为一些成员可能是第一次使用Git进行多人协作项目，因此，在此我们以TestGit(<https://gitee.com/kingcq2004/test-git.git)测试仓库为例详细解释一下步骤：>  
第一次使用Git，可能采用的方法仍然不够安全，相信之后会做的更好。  
此处只使用Git Bash进行介绍，允许使用更加方便的工具（如Jetbrains）。

1. ### 克隆项目到本地
    我们选择先拉取项目master分支内容  
    需要注意的一点是，虽然每次继续项目上的工作不需要重新克隆项目到本地，但仍需要远程拉取一下仓库文件，确保master分支为最新。

    ```sh
    git init
    git pull https://gitee.com/kingcq2004/test-git.git
    git remote add origin https://gitee.com/kingcq2004/test-git.git
    ```

2. ### 创建属于自己的分支
    创建一个分支，然后做一点修改，将分支推送到远程仓库

    ```sh
    git checkout -b Test1
    (做一些修改)
    git add .
    git commit -m "Update"
    git push origin Test1
    ```

3. ### 回到master分支，尝试合并
    在这里需要注意的是，在合并之前需要先同步master分支，确保master分支为最新  
    在合并master和Test1时，如果发现文件冲突，需要手动完成文件内容的合并。
    确保无误之后，再推送至远程仓库

    ```sh
    git checkout master
    git pull origin master
    git merge Test1
    git push origin master
    ```

    如有需要，清除本地自己的分支

    ```sh
    git branch -d Test1
    ```

## 工作流程规范
对项目内容进行修改编写时，应当首先拉取更新远程仓库的master分支到本地master分支。  
随后将master分支合并到自己的分支，并对负责的内容进行编写，编写完成后，在指定的文件中填写好自己的更新日志，大致描述这次更新完成了什么内容。
依照上述Git流程完成本次更新的提交。
为了便于整理和查找，我们对 git 提交的规范也有一定的要求：
```sh
feat: 新增功能
fix: 修复bug
docs: 文档更新
style: 代码格式（不影响代码运行的变动）
refactor: 重构（即不是新增功能，也不是修改bug的代码变动）
perf: 性能优化
test: 增加测试
chore: 构建过程或辅助工具的变动
revert: 回滚到上一个版本
build: 构建系统升级
ci: 变更持续集成配置
```

## Flask项目结构及编写规范
根据研究，我们将Flask项目结构参照Nonebot机器人项目结构重新编排，组成了如下的插件式项目结构：

```sh
|-- Flask
|   |-- app
|   |   |-- plugins
|   |   |   |-- example_plugin1
|   |   |   |   |-- __init__.py
|   |   |   |   |-- example_plugin1.py
|   |   |   |-- example_plugin2
|   |   |       |-- __init__.py
|   |   |       |-- example_plugin2.py
|   |   |-- __init__.py
|   |   |-- manager.py
|   |-- launcher.py
|-- viewer.py
```

### Flask插件编写方式
我们假设有这样一个插件hello，它能够让Flask应用在路由'/hello'时返回'Hello World!'，那么我们能很容易构建出以下的插件结构：

```sh
|-- plugins
    |-- hello
        |-- __init__.py
        |-- hello.py
        |-- README.md
```

对于__init__.py的内容，我们可以作以下编写：

```python
from flask import Blueprint

hello = Blueprint('hello', __name__)
__blueprint__ = hello # 非常重要！没有这一项，插件无法正常被加载

from . import hello
```

对于hello.py，我们作以下编写：

```python
from . import hello

@hello.route("/hello")
def _hello():
    return "Hello World!"
```

实际上，我们也可以把这两个文件组合起来，只保留__init__.py：

```python
from flask import Blueprint

hello = Blueprint('hello', __name__)
__blueprint__ = hello # 非常重要！没有这一项，插件无法正常被加载

@hello.route("/hello")
def _hello():
    return "Hello World!"
```

特别需要提醒的是__init__.py中必须要有__blueprint__这个值且指向你所构建的Blueprint，插件的加载方式依赖这个进行，另外，包名以'_'为开头的插件不会被加载
更加详细的信息可以查看 `_template` 插件，它更全面，但并没有编写注释（反正你也肯定看得懂）

### Flask代码编写规范（待补充）
在插件文件夹中应当有README.md，详述此插件的功能用途。  
对于每个函数，应当简述其实现及参数含义，必要的话，展示几个示例以更清楚地说明函数的作用。  
对于一些关键性较为难理解的步骤，应当在语句块上方一行用单行注释简单解释。  
最外层函数/类的定义之间间隔两个空行，内部语句间空行不得超过一个空行。  
（下方仅作示例，实际可在一定范围内自由发挥）：
__init__.py:

```python
from flask import Blueprint

hello = Blueprint('hello', __name__)
__blueprint__ = hello


@hello.route('/hello/<name>')
def _hello(name: str) -> str:
    """
    Send certain greetings according to name of the user.
    Param:
        name: Name of the user
    Return:
        (str): The words

    >>> _hello("Kingcq")
    "Hello, Kingcq!"
    >>> _hello("zyt2048")
    "Hello, zyt2048!"
    """
    # 将name与固定字符串格式拼装
    return f"Hello, {name}!"


@hello.route('/hello_world')
def hello_world() -> str:
    """
    Send the classic "Hello, world!"
    Return:
        (str): The words

    >>> hello_world()
    "Hello, world!"
    """
    return "Hello, world!"
```

## Vue项目结构及编写规范
整体上我们使用Vue + Docker + Nginx的方式进行项目的构建，不过这是之后要考虑的事情。在开发初期我们先使用Dev Server对编写的内容进行测试。  
懒了，部署方式直接先甩几个网址，自行观看，有问题之后再补。  
[菜鸟教程](https://www.runoob.com/docker/docker-install-node.html)、[CSDN](https://blog.csdn.net/weixin_43484014/article/details/121376338)

### 项目结构
我们以运行npm init vue＠latest之后生成的目录的src文件夹为例：

```sh
|-- src
| |-- assets
|   |   |-- base.css
|   |   |-- logo.svg
|   |   |-- main.css
|   |-- components
|   |   |-- icons
|   |   |   |-- iconCommunity.vue
|   | |   |-- iconDocumentation.vue
|   |   |   |-- iconSupport.vue
|   |   |   |-- iconTooling.vue
|   |   |-- HelloWorld.vue
|   |   |-- TheWelcome.vue
|   |   |-- WelcomeItem.vue
|   |-- router
|   |   |-- index.js
|   |-- views
|   |   |-- AboutView.vue
|   |   |-- HomeView.vue
|   |-- App.vue
|   |-- main.js
|-- index.html
|-- public
    |-- favicon.ico
```

先看index.html：

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <link rel="icon" href="/favicon.ico">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vite App</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

在这里我们进行一些关键内容的引用和设置，比如标签页标题、标签页图标、全应用通用的Javascript和CSS等

router/index.js：

```js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue')
    }
  ]
})

export default router
```

需要在创建项目的时候选择使用router-view才会出现这个文件以及一些相关的设置，这是必要的，因为我们需要使用到它。  
在这里对路由相关的一些内容进行配置，示例当中我们能发现，每一个路由都指向一个单个的Vue组件。

assets/：  
没什么好说的，一些静态图片放在这里

public/favicon.ico
标签页图标在这里，大小与示例图片相同较为合适，且一般需要背景色以适应标签的不同颜色主题。

views/：  
views中的Vue组件一般是整合后的完整组件，每一个组件都可以完整地代表一个网页视图，具体内容自行观看，每个组件都是由components/文件夹中的一些小组件或者一些零散的HTML和CSS内容构成的。

components/：  
conponents中一般包含一些小型组件，如导航栏、侧边栏等，一般作为整个网页页面的一个部分出现，从自定义的按钮到整个侧边栏的编写，一般都在这里。

我们的项目还需要使用axios，在项目文件夹最外层使用：

```sh
npm install axios
```

为项目安装适合版本的axios。  
同时我们对示例项目做一些修改，以使得axios能够正常使用并保持session的一致性（尚未验证）：  
在src/文件夹下新建文件夹，命名为utils/  
新建一个文件，命名为axiosInstance.js，填入一下内容：

```js
import axios from "axios"

const API = axios.create({
    baseURL: "http://example.url",
    timeout: 2000,
    withCredentials: true
})

export default API
```

通过这样的方式创建axios实例并设置一些配置项，这个文件在必要时可以且应当被修改。  
同时，在main.js中添加一点内容，将这个axios实例挂载到全局：

```js
import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
// modified here!
import axios from "@/utils/axiosInstance"

const app = createApp(App)

app.use(router)

app.mount('#app')

// modified here!
app.config.globalProperties.$http = axios
```

我们允许并推荐使用Element UI组件库，针对我们使用的Vue3，我们使用以下指令安装Element UI：

```sh
npm install element-plus
```

随后参考[Element-Plus Quickstart](https://element-plus.org/zh-CN/guide/quickstart.html)对Element UI组件进行挂载。

Vue代码编写规范（待补充）：
代码编写使用 __组合式api__ ，且无论是否需要写script内容，都应当使用

```html
<script setup>
```

标签并在其中写上该组件的介绍和用途，格式随意但必须通俗易懂。
实例：HelloWorld.vue：

```html
<script setup>
/*
    Component: HelloWorld.vue
    Usage: Display certain greeting message plus some congratulation messages.
    props:
        msg(required): The greeting message
*/
defineProps({
  msg: {
    type: String,
    required: true
  }
})
</script>
```

同Python规范，在一些关键的步骤上方必须加上解释该步骤的单行注释。

以下是一个vue文件的 `<script setup>` 示例.

```html
<script setup>
// please place the <script setup> at the start of a .vue file.
// use **LOWER CAMEL CASE** for variable naming.


// place imports here
import {ref, onMounted} from 'vue'


// place data variables & constants here
// please make sure to use ref() to initialize variables so that vuejs framework can keep track of them. 
// see https://stackoverflow.com/questions/63623559/why-plain-constant-still-works-in-composition-api-vue-3
const count = ref(0)


// place custom functions here
function doSomething(){
    count.value++;
}

// place lifecycle hooks at the end of a <script setup>.
onMounted(() => {
    // use formatted strings only when necessary
    console.log(`the initial count is ${count.value}.`)
})
onUpdated(() => {
    console.log('component updated!')
})
</script>
```

