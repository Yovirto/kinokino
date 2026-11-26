package org.kivy.android;

import android.app.Activity;
import android.net.Uri;
import android.webkit.CookieManager;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.ByteArrayInputStream;
import java.util.Arrays;
import java.util.List;

/**
 * Removes obvious ad/tracker traffic and the most intrusive UI blocks from
 * Kinopoisk pages. It intentionally leaves the normal catalog, search and
 * navigation untouched.
 */
public final class KinopoiskCleaner {
    private static final String CLEANUP_CSS =
            "div[class*='adfox'],div[class*='ad-banner'],div[class*='adsbygoogle'],"
            + "div[class*='app-banner'],div[class*='appBanner'],div[class*='download-app'],"
            + "div[class*='downloadApp'],div[class*='install-app'],div[class*='installApp'],"
            + "div[class*='mobile-app'],div[class*='mobileApp'],div[class*='promo-banner'],"
            + "div[class*='promoBanner'],div[class*='sidebar-banner'],div[class*='sidebarBanner'],"
            + "div[class*='top-banner'],div[class*='topBanner'],div[class*='bottom-banner'],"
            + "div[class*='bottomBanner'],div[class*='promo-block'],div[class*='promoBlock']"
            + "{display:none !important}";

    private static final String CLEANUP_JS =
            "(function(){"
            + "var css='" + CLEANUP_CSS + "';"
            + "if(!document.getElementById('kinokino-clean-css')){"
            + "var style=document.createElement('style');"
            + "style.id='kinokino-clean-css';"
            + "style.textContent=css;"
            + "(document.head||document.documentElement).appendChild(style);"
            + "}"
            + "function hideNode(node){"
            + "node.style.setProperty('display','none','important');"
            + "node.setAttribute('data-kinokino-hidden','1');"
            + "}"
            + "function clean(){"
            + "var phrases=['скачать приложение','установить приложение','установите приложение',"
            + "'приложение kinopoisk','смотрите в приложении'];"
            + "var nodes=document.querySelectorAll('div,section,aside,nav,header,footer,a,button');"
            + "for(var i=0;i<nodes.length;i++){"
            + "var node=nodes[i];"
            + "if(!node||node.getAttribute('data-kinokino-hidden'))continue;"
            + "var text=(node.innerText||node.textContent||'').toLowerCase();"
            + "if(!text||text.length>260||node.children.length>6)continue;"
            + "for(var j=0;j<phrases.length;j++){"
            + "if(text.indexOf(phrases[j])!==-1){hideNode(node);break;}"
            + "}"
            + "}"
            + "}"
            + "function run(){clean();}"
            + "if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',run);}else{run();}"
            + "new MutationObserver(function(){run();}).observe(document.documentElement,{childList:true,subtree:true});"
            + "})();";

    private static final List<String> BLOCKED_HOST_FRAGMENTS = Arrays.asList(
            "adfox",
            "adsystem",
            "adriver",
            "doubleclick",
            "googlesyndication",
            "scorecardresearch",
            "taboola",
            "outbrain",
            "criteo",
            "moatads",
            "adnxs",
            "admob",
            "adsrvr",
            "casalemedia",
            "pubmatic",
            "rubiconproject",
            "openx",
            "bidswitch",
            "smartadserver",
            "spotxchange",
            "teads",
            "indexww",
            "sharethrough",
            "33across",
            "sonobi",
            "gumgum",
            "adyard",
            "adzero",
            "betweendigital",
            "lentainform",
            "top-fwz1.mail.ru",
            "mc.yandex.ru",
            "an.yandex.ru"
    );

    private KinopoiskCleaner() {
    }

    public static void apply(final Activity activity, final WebView webView) {
        if (activity == null || webView == null) {
            return;
        }

        enableWebViewDebuggingIfPossible(activity);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(
                    WebView view,
                    WebResourceRequest request
            ) {
                Uri url = request.getUrl();
                String host = url.getHost();
                if (host != null && isBlockedHost(host)) {
                    return new WebResourceResponse(
                            "text/plain",
                            "utf-8",
                            new ByteArrayInputStream(new byte[0])
                    );
                }
                return super.shouldInterceptRequest(view, request);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                CookieManager.getInstance().flush();
                injectCleanup(view, url);
            }

            @Override
            public void doUpdateVisitedHistory(WebView view, String url, boolean isReload) {
                super.doUpdateVisitedHistory(view, url, isReload);
                injectCleanup(view, url);
            }
        });
    }

    private static void injectCleanup(WebView view, String url) {
        if (url == null || !url.contains("kinopoisk.ru")) {
            return;
        }
        view.evaluateJavascript(CLEANUP_JS, null);
    }

    private static boolean isBlockedHost(String host) {
        String normalizedHost = host.toLowerCase();
        for (String fragment : BLOCKED_HOST_FRAGMENTS) {
            if (normalizedHost.contains(fragment)) {
                return true;
            }
        }
        return false;
    }

    private static void enableWebViewDebuggingIfPossible(Activity activity) {
        try {
            Class<?> buildConfig = Class.forName(activity.getPackageName() + ".BuildConfig");
            boolean debug = buildConfig.getField("DEBUG").getBoolean(null);
            WebView.setWebContentsDebuggingEnabled(debug);
        } catch (Exception ignored) {
            // WebView debugging is optional and must not break the app.
        }
    }
}
