package io.dcloud;
{% if nativeui %}import io.dcloud.feature.ui.nativeui.NativeUIR;{% endif %}
{% if gallery %}import io.dcloud.js.gallery.GalleryR;{% endif %}
/**
 * 本文件是5+SDK使用的资源索引
 * 工程引入本文件的包名必须是“io.dcloud”
 * */
public class RInformation extends PdrR
{% if nativeui or gallery %}
    implements
    {% if nativeui %}NativeUIR{% if gallery %},{% endif %}{% endif %}{% if gallery %}GalleryR{% endif %}
{% endif %}
{
	
	//public static int VIEW_LAYOUT_SPLASH = 0;
}

