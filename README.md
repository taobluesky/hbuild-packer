# 目的
HBuilder的基座给调试带来不少便利，但有些功能还是经常需要打包后才能进行调试。官方提供的云端打包在高峰期打包速度相当缓慢，漫长的等待非常不便于调试。为了让开发者能随心所欲进行编译打包，能做到可持续集成开发。

# 与云端打包的区别
- 云端打包所使用的的5+SDK版本较新
- 不检查manifest.xml配置，请使用HBuilder正确设置
- 暂时仅支持android端，iOS后续开发

# 对5+SDK版本的支持
打包工具将持续更新，当前支持5+SDK为：[2016年9月29日发布的Android平台](http://download.dcloud.net.cn/Android-SDK@1.9.9.26346_201609302.zip)

# 文件清单
待整理。。

# 系统环境依赖
- python 2.7+
- pip
- json-cfg
- jinja2

安装python及pip后，运行如下命令安装脚本所需库依赖:
```
$ pip install json-cfg
$ pip install jinja2
```

# config.json配置
打包之前，先对config.json进行正确的配置

# Android打包
## 打包准备环境
- JDK 1.8
- Android Studio v2.2.2
- Android SDK API v23(Android 6.0)
- 5+SDK for Android (http://ask.dcloud.net.cn/article/103)
## 创建AndroidStudio模板工程
启动Android Studio，选择`New Project`，按如下配置
```
Application Name:DCloudTemplate
Company Domain:yourdomain.com
```
点击`Next`；

点选`Phone and Tablet: API 9:Android 2.3`，点击`Next`；

选择`Add No Activity`，点击`Finish`；

菜单`Build->Build Apk`，如未提示`generated successfully`，请自行检查android studio的配置。

菜单`Build->Clean Project`，清理模板工程
## 执行打包命令
`$ python packer.py -p android`
如提示`BUILD SUCCESSFUL`，则打包成功。可打开`config.json`配置的`app_project_path`目录下`app\build\outputs\apk`查看打包后的apk。

# 命令行(CLI)
```
$ python packer.py -h
usage: packer.py [-h] -p {ios,android} [-c]

HBuilder离线打包器

optional arguments:
  -h, --help            show this help message and exit
  -p {ios,android}, --platform {ios,android}
                        选择平台，ios或者android，当前仅支持android
  -c, --only-create     仅创建工程，不进行编译
```