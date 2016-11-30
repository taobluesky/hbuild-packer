# 目的
HBuilder的基座给调试带来不少便利，但有些功能还是经常需要打包后才能进行调试。官方提供的云端打包在高峰期打包速度相当缓慢，漫长的等待非常不便于调试。为了让开发者能随心所欲进行编译打包，能做到可持续集成开发，写了此打包器。

# 与云端打包的区别
- 云端打包所使用的的5+SDK版本较新
- 不检查manifest.xml配置，请使用HBuilder正确设置
- 暂时仅支持android端，iOS后续开发

# 文件清单

# 系统依赖
- python 2.7+
- pip
- json-cfg
- jinja2
安装python及pip后，运行如下命令安装依赖:
```
> pip install json-cfg
> pip install jinja2
```

# config.json配置

# Android打包
## 打包准备环境
- JDK 1.8
- Android Studio v2.2.2
- Android SDK API v23(Android 6.0)

## 创建AndroidStudio模板工程
选择`File->New Project`，按如下配置
```
Application Name:DCloudTemplate
Company Domain:yourdomain.com
```
点击`Next`；

点选`Phone and Tablet: API 9:Android 2.3`，点击`Next`；

选择`Add No Activity`，点击`Finish`；

菜单`Build->Build Apk`，如未提示`generated successfully`，请自行检查android studio的配置。

## 执行命令

