# -*- coding:utf-8 -*-

import os
import shutil
import json
import codecs
import logging
import jsoncfg
import copy
from jinja2 import Environment, FileSystemLoader

CURRENT_PATH = os.path.dirname(__file__)
HBUILD_PROJECT_PATH = r'C:\Users\timo\Documents\HBuilderProject\HelloH5' #r'C:\Users\timo\project\app-all\cph'
DCLOUD_PROJECT_PATH = r'C:\Users\timo\StudioProjects\DCloudBase'
APP_PROJECT_PATH = r'C:\Users\timo\Desktop\DCloudBase'
H5PLUS_SDK_PATH = r'F:\Android-SDK\SDK'
# 讯飞语音插件 官方默认APPKEY（云端打包）
# 为讯飞语音云网站申请的APPKEY，由于它是和libs目录下的jar包是绑定的，不要修改此值
# 新版HBuilder默认已经不存在该配置，需在manifest.xml中增加：
# plus.distribute.plugins.ifly.appid = "your_app_id"
# 参考：http://ask.dcloud.net.cn/article/94
DCLOUD_IFLY_APPKEY = '5177d8fe'


def _easy_get(obj, key):
    """
    从dict Object中快速取值
    :param obj: 需要取值的字典
    :param key: 字典的键值，多个键使用.连接，如:'google.permissions'
    :return 如有返回该值，无返回 None
    """
    for k in key.split('.'):
        obj = obj.get(k)
        if obj is None:
            break
    return obj


def _write_file(filename, content):
    """写文件使用utf-8编码，支持Unicode"""
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    f = codecs.open(filename, 'w', encoding='utf-8')
    f.write(content)
    f.close()


def _copy(src, dst):
    """复制文件"""
    dirname = os.path.dirname(dst)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    shutil.copy(src, dst)


class BasePacker(object):
    template_env = Environment(loader=FileSystemLoader(os.path.join(CURRENT_PATH, 'templates')))

    def __init__(self,
                 hbuild_project_path=HBUILD_PROJECT_PATH,
                 dcloud_project_path=DCLOUD_PROJECT_PATH,
                 h5plus_sdk_path=H5PLUS_SDK_PATH,
                 app_project_path=APP_PROJECT_PATH):
        self.hbuild_project_path = hbuild_project_path
        self.dcloud_project_path = dcloud_project_path
        self.h5plus_sdk_path = h5plus_sdk_path
        self.app_project_path = app_project_path
        self._hbuild_env_dict = self.get_hbuild_environment()
        # self.distribute_env = self._hbuild_env_dict['plus']['distribute']

    def get_hbuild_environment(self):
        """读取Hbuild项目的配置参数"""
        manifest_path = os.path.join(self.hbuild_project_path, 'manifest.json')
        f = codecs.open(manifest_path, 'r')
        env = jsoncfg.load(f)
        return env

    @property
    def distribute_env_dict(self):
        return self._hbuild_env_dict['plus']['distribute']

    def get_distribute_value(self, key):
        """
        获取plus.distribute中值的简易方法，避免出现KeyError异常
        :param key: 字典的键值，可连续如:'google.permissions'
        :return 如有返回该值，无返回 None
        """
        return _easy_get(self.distribute_env_dict, key)

    def copy_base_project(self):
        """复制基础项目"""
        if os.path.isdir(self.app_project_path):
            shutil.rmtree(self.app_project_path)
        shutil.copytree(self.dcloud_project_path, self.app_project_path)

    def _render_template(self, template_name, context):
        template = self.template_env.get_template(template_name)
        result = template.render(context)
        return result

    def _get_app_manifest_content(self):
        manifest_json = copy.deepcopy(self._hbuild_env_dict)
        manifest_json['plus'].pop('distribute')
        manifest_json.pop('dependencies')
        manifest_json.pop('unpackage')
        return json.dumps(manifest_json)

    def _create_app_manifest_json(self, filename, content):
        _write_file(filename, content)


class AndroidPacker(BasePacker):
    def __init__(self,
                 hbuild_project_path=HBUILD_PROJECT_PATH,
                 dcloud_project_path=DCLOUD_PROJECT_PATH,
                 h5plus_sdk_path=H5PLUS_SDK_PATH,
                 app_project_path=APP_PROJECT_PATH):
        super(AndroidPacker, self).__init__(hbuild_project_path=hbuild_project_path,
                                            dcloud_project_path=dcloud_project_path,
                                            h5plus_sdk_path=h5plus_sdk_path,
                                            app_project_path=app_project_path)
        self._h5plussdk_json = self.get_android_h5plussdk_json()
        self.distribute_google = self.distribute_env_dict['google']
        self.distribute_google['packagename'] = 'com.cn_etc.cph'
        self._installed_module = self.get_installed_module()
        self._lib_jar, self._lib_so, self._lib_assets = self.get_libs_desc()
        # 路径相关
        self._app_www_path = os.path.join(self.app_project_path,
                                         r'app\src\main\assets\apps\%s\www' % (self._hbuild_env_dict['id']))
        self._app_manifest_path = os.path.join(self._app_www_path, r'manifest.json')
        self._app_res_path = os.path.join(self.app_project_path, r'app\src\main\res')
        self._app_strings_path = os.path.join(self._app_res_path, r'values\strings.xml')
        self._app_control_path = os.path.join(self.app_project_path, r'app\src\main\assets\data\control.xml')
        self._app_android_manifest_path = os.path.join(self.app_project_path, r'app\src\main\AndroidManifest.xml')
        self._app_rinformation_path = os.path.join(self.app_project_path, r'app\src\main\java\io\dcloud\RInformation.java')
        self._app_build_gradle_path = os.path.join(self.app_project_path, r'app\build.gradle')

    def get_android_h5plussdk_json(self):
        h5_sdk_json = jsoncfg.load(os.path.join(CURRENT_PATH,'h5+_sdk_android.json'))
        return h5_sdk_json

    def get_installed_module(self):
        """获取需要安装的模块"""
        installed_module = []
        for module_name in self._hbuild_env_dict['permissions']:
            _module_name = module_name.lower()
            module = self._h5plussdk_json.get(_module_name)
            if module and module.get('plugin'):  # 模块是否为plugin
                _module_name = module.get('name')
                for plugin_name in self.get_distribute_value('plugins.'+_module_name):
                    plugin = self._h5plussdk_json['plugins'][_module_name][plugin_name]
                    if plugin:
                        installed_module.append('.'.join(['plugins', _module_name, plugin_name.lower()]))
                    else:
                        raise Exception(u'插件plugins.%s.%s不存在' % (_module_name, plugin_name))
                continue
            if module is not None:
                installed_module.append(_module_name)
            else:
                logging.warning(u'Warining:模块%s不存在，未做处理' % (_module_name,))
        # geolocation模块特殊处理
        if 'geolocation' in installed_module:
            if 'plugins.maps.baidu' in installed_module:
                installed_module.append('geolocation.baidu')
            if 'plugins.maps.amap' in installed_module:
                installed_module.append('geolocation.amap')

        return installed_module

    def get_libs_desc(self):
        jar = set()
        so = set()
        assets = set()
        for module_name in self._installed_module:
            module = _easy_get(self._h5plussdk_json, module_name)
            if module.get('jar'):
                jar = jar.union(module['jar'])
            if module.get('so'):
                so = so.union(module['so'])
            if module.get('assets'):
                assets = assets.union(module['assets'])
        return jar, so, assets

    def _copy_libs(self):
        """复制android模块的libs"""
        app_libs_path = os.path.join(self.app_project_path, r'app\libs')
        app_jni_libs_path = os.path.join(self.app_project_path, r'app\src\main\jniLibs')
        app_assets_path = os.path.join(self.app_project_path, r'app\src\main\assets')
        for jar_name in self._lib_jar:
            src = os.path.join(self.h5plus_sdk_path, 'libs\\'+jar_name)
            _copy(src, app_libs_path)
        for so_name in self._lib_so:
            src = os.path.join(self.h5plus_sdk_path, 'libs\\'+so_name)
            dst = os.path.join(app_jni_libs_path, so_name)
            _copy(src, dst)
        for asset_name in self._lib_assets:
            src = os.path.join(self.h5plus_sdk_path, 'assets\\'+asset_name)
            dst = os.path.join(app_assets_path, asset_name)
            _copy(src, dst)

    def _create_libs_code(self):
        """创建libs的java代码"""
        pkg_name = self.distribute_google['packagename']
        pkg_java = '\\'.join(pkg_name.split('.'))
        app_java_path = os.path.join(self.app_project_path, r'app\src\main\java')
        pkg_java_path = os.path.join(app_java_path, pkg_java)
        ctx = {'pkg_name': pkg_name}
        if self.__is_installed('payment', 'weixin'):
            template_name = 'wxapi/WXPayEntryActivity.java'
            result = self._render_template(template_name, ctx)
            filename = os.path.join(pkg_java_path, template_name)
            _write_file(filename, result)
        if self.__is_installed('share', 'weixin'):
            template_name = 'wxapi/WXEntryActivity.java'
            result = self._render_template(template_name, ctx)
            filename = os.path.join(pkg_java_path, template_name)
            _write_file(filename, result)
        # 文档并未写明 新浪微博分享 模块的细节：
        # 经逆向分析云端打包apk，需要处理SinaCallbackActivity.java文件
        if self.__is_installed('share', 'sina'):
            template_name = 'SinaCallbackActivity.java'
            result = self._render_template(template_name, ctx)
            filename = os.path.join(pkg_java_path, template_name)
            _write_file(filename, result)

    def copy_hbuild_to_app(self, www_dir):
        """
        复制h5+项目到app项目目录
        :param www_dir 目标目录
        """
        def ignore_file(src, names):
            ignore = []
            for name in names:
                if name.startswith('.'):
                    ignore.append(name)
                if src == self.hbuild_project_path and name == 'unpackage':  # 忽略unpackage目录
                    ignore.append('unpackage')
                path = os.path.join(src, name)
                _path = path.replace(self.hbuild_project_path + '\\', '').replace('\\','/')
                if _path in self._hbuild_env_dict['unpackage']:
                    ignore.append(name)
            return ignore

        if os.path.isdir(www_dir):
            shutil.rmtree(www_dir)
        shutil.copytree(self.hbuild_project_path, www_dir, ignore=ignore_file)

    def get_orientation_value(self):
        """计算android_manifest.xml中orientation属性值
        """
        orientation = self.distribute_env_dict['orientation']
        l = len(orientation)
        if l == 1:
            orientation_map = {
                'portrait-primary': 'portrait',
                'portrait-secondary': 'reversePortrait',
                'landscape-primary': 'landscape',
                'landscape-secondary': 'reverseLandscape'
            }
            return orientation_map[orientation[0]]
        elif l == 2:
            if set(orientation).issubset(['portrait-primary', 'portrait-secondary']):
                return 'sensorPortrait'
            elif set(orientation).issubset(['landscape-primary', 'landscape-secondary']):
                return 'sensorLandscape'
        return 'user'

    def __is_installed(self, module_name, plugin_name=None):
        """判断模块或者插件是否被安装
        """
        full_module_name = module_name.lower()
        if plugin_name:
            full_module_name = '.'.join(['plugins', full_module_name, plugin_name.lower()])
        return full_module_name in self._installed_module

    def _create_android_manifest_xml(self):
        result = self._render_template('android_manifest.xml', {
            'pkg_name': self.distribute_google['packagename'],
            'permissions': self.get_distribute_value('google.permissions'),
            'orientation': self.get_orientation_value(),
            'is_immersed': self.get_distribute_value('google.ImmersedStatusbar'),
            'gallery': self.__is_installed('gallery'),
            'speech':{
                'open': self.__is_installed('speech'),
                'appid': self.get_distribute_value('plugins.speech.ifly.appid') or DCLOUD_IFLY_APPKEY
            },
            'maps': {
                'baidu':{
                    'open': self.__is_installed('maps', 'baidu'),
                    'appkey': self.get_distribute_value('plugins.maps.baidu.appkey_android')
                },
                'amap': {
                    'open': self.__is_installed('maps','amap'),
                    'appkey': self.get_distribute_value('plugins.maps.amap.appkey_android')
                }
            },
            'payment': {
                'alipay': {
                    'open': self.__is_installed('payment', 'alipay'),

                },
                'weixin': {
                    'open': self.__is_installed('payment', 'alipay'),
                    'appid': self.get_distribute_value('plugins.payment.weixin.appid')
                }
            },
            'push': {
                'igexin':{
                    'open': self.__is_installed('push','igexin'),
                    'appid': self.get_distribute_value('plugins.push.igexin.appid'),
                    'appkey': self.get_distribute_value('plugins.push.igexin.appkey'),
                    'appsecret': self.get_distribute_value('plugins.push.igexin.appsecret')
                }
            },
            'share': {
                'sina': {
                    'open': self.__is_installed('share','sina'),
                    'appkey': self.get_distribute_value('plugins.share.sina.appkey'),
                    'appsecret': self.get_distribute_value('plugins.share.sina.appsecret'),
                    'redirect_uri': self.get_distribute_value('plugins.share.sina.redirect_uri')
                },
                'tencent': {
                    'open': self.__is_installed('share','tencent'),
                    'appkey': self.get_distribute_value('plugins.share.tencent.appkey'),
                    'appsecret': self.get_distribute_value('plugins.share.tencent.appsecret'),
                    'redirect_uri': self.get_distribute_value('plugins.share.tencent.redirect_uri')
                },
                'weixin': {
                    'open': self.__is_installed('share','weixin'),
                    'appid': self.get_distribute_value('plugins.share.weixin.appid'),
                    'appsecret': self.get_distribute_value('plugins.share.weixin.appsecret')
                },
                'qq': {
                    'open': self.__is_installed('share', 'qq'),
                    'appid': self.get_distribute_value('plugins.share.qq.appid')
                }
            },
            'statics': {
                'umeng': {
                    'open': self.__is_installed('statics', 'umeng'),
                    'appkey': self.get_distribute_value('plugins.statics.umeng.appkey_android'),
                    'channelid': self.get_distribute_value('plugins.statics.umeng.channelid_android')
                }
            },
            'oauth': {
                'qq': {
                    'open': self.__is_installed('oauth', 'qq'),
                    'appid': self.get_distribute_value('plugins.oauth.qq.appid')
                },
                'sina': {
                    'open': self.__is_installed('oauth', 'qq'),
                    'appkey': self.get_distribute_value('plugins.oauth.sina.appkey'),
                    'appsecret': self.get_distribute_value('plugins.oauth.sina.appsecret'),
                    'redirect_uri': self.get_distribute_value('plugins.oauth.sina.redirect_uri')
                },
                'weixin': {
                    'open': self.__is_installed('oauth', 'weixin'),
                    'appid': self.get_distribute_value('plugins.oauth.weixin.appid'),
                    'appsecret': self.get_distribute_value('plugins.oauth.weixin.appsecret'),
                }
            }
        })

        _write_file(self._app_android_manifest_path, content=result)

    def _create_control_xml(self):
        """创建control.xml文件"""
        result = self._render_template('control.xml', {
            'debug': self.distribute_env_dict['debug'],
            'app_id': self._hbuild_env_dict['id'],
            'app_ver': self._hbuild_env_dict['version']['name']
        })
        _write_file(self._app_control_path, content=result)

    def _create_rinformation_java(self):
        """创建RInformation.java文件"""
        result = self._render_template('RInformation.java', {
            'nativeui': self._hbuild_env_dict['permissions'].has_key('NativeUI'),
            'gallery': self._hbuild_env_dict['permissions'].has_key('Gallery')
        })
        _write_file(self._app_rinformation_path, content=result)

    def _copy_icon_and_splashscreen(self):
        """复制icon和splashscreen"""
        icon_android = self.distribute_env_dict['icons']['android']
        splashscreen_android = self.distribute_env_dict['splashscreen']['android']
        for k in icon_android:
            if icon_android[k]:
                src = os.path.join(self.hbuild_project_path, icon_android[k])
                dst = os.path.join(self._app_res_path, 'drawable-'+k+'\icon.png')
                shutil.copy(src, dst)
            if splashscreen_android[k]:
                src = os.path.join(self.hbuild_project_path, splashscreen_android[k])
                dst = os.path.join(self._app_res_path, 'drawable-'+k+'\splash.png')
                shutil.copy(src, dst)

    def _create_strings_xml(self):
        """创建strings.xml"""
        result = self._render_template('strings.xml', {
            'app_name': self._hbuild_env_dict['name'].decode('utf-8')
        })
        _write_file(self._app_strings_path, content=result)

    def _create_app_build_gradle(self):
        """创建app的build.gradle文件，用于gradle编译apk"""
        result = self._render_template('build.gradle', {
            'pkg_name': self.distribute_google['packagename'],
            'app_ver_name': self._hbuild_env_dict['version']['name'],
            'app_ver_code': self._hbuild_env_dict['version']['code'],
            'modules': self._lib_jar
        })
        _write_file(self._app_build_gradle_path, content=result)

    def build(self):
        # self.copy_base_project()
        # self.copy_hbuild_to_app(self._app_www_path)
        self._create_app_manifest_json(self._app_manifest_path, self._get_app_manifest_content())
        self._create_control_xml()
        self._copy_icon_and_splashscreen()
        self._create_strings_xml()
        self._create_rinformation_java()
        self._create_android_manifest_xml()

        self._copy_libs()
        self._create_libs_code()
        self._create_app_build_gradle()

    def test(self):
        pass

if __name__ == '__main__':
    p = AndroidPacker()
    p._create_android_manifest_xml()

    # www_dir = get_www_dir(cfg)
    # copy_hbuild_to_dest(cfg, www_dir)
