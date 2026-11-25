package org.kivy.android;

import android.app.Activity;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebView;
import android.widget.AbsoluteLayout;
import android.widget.Button;

/**
 * Adds a native floating button above the WebView used by the webview
 * bootstrap. URL validation and conversion intentionally remain in Python.
 */
public final class MirrorController {
    private static final int BUTTON_COLOR = 0xFFFF3B30;
    private static final int TEXT_COLOR = 0xFFFFFFFF;
    private static final int BUTTON_WIDTH_DP = 132;
    private static final int BUTTON_HEIGHT_DP = 44;
    private static final int RIGHT_MARGIN_DP = 8;

    private static Button floatingButton;

    private MirrorController() {
    }

    public static void install(final Activity activity) {
        if (activity == null) {
            return;
        }

        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                installOnUiThread(activity);
            }
        });
    }

    private static void installOnUiThread(final Activity activity) {
        final WebView webView = PythonActivity.mWebView;
        final ViewGroup layout = PythonActivity.mLayout;

        if (webView == null || layout == null) {
            // The WebView may not have been created yet. Retry shortly.
            activity.getWindow().getDecorView().postDelayed(new Runnable() {
                @Override
                public void run() {
                    installOnUiThread(activity);
                }
            }, 250);
            return;
        }

        if (floatingButton != null && floatingButton.getParent() == layout) {
            positionButton(layout, floatingButton);
            return;
        }

        final Button button = new Button(activity);
        button.setText("Смотреть");
        button.setTextColor(TEXT_COLOR);
        button.setTextSize(TypedValue.COMPLEX_UNIT_SP, 12);
        button.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        button.setAllCaps(false);
        button.setGravity(Gravity.CENTER);
        button.setPadding(0, 0, 0, 0);
        button.setMinWidth(0);
        button.setMinHeight(0);
        button.setRotation(-90f);
        button.setElevation(dp(activity, 8));
        button.setContentDescription("Открыть страницу KinoKino");

        GradientDrawable background = new GradientDrawable();
        background.setColor(BUTTON_COLOR);
        background.setCornerRadii(new float[]{
                dp(activity, 22),
                dp(activity, 22),
                dp(activity, 22),
                dp(activity, 22)
        });
        button.setBackground(background);

        button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                openMirror(webView);
            }
        });

        AbsoluteLayout.LayoutParams initialParams = new AbsoluteLayout.LayoutParams(
                dp(activity, BUTTON_WIDTH_DP),
                dp(activity, BUTTON_HEIGHT_DP),
                0,
                0
        );
        layout.addView(button, initialParams);
        floatingButton = button;

        layout.addOnLayoutChangeListener(new View.OnLayoutChangeListener() {
            @Override
            public void onLayoutChange(
                    View changedView,
                    int left,
                    int top,
                    int right,
                    int bottom,
                    int oldLeft,
                    int oldTop,
                    int oldRight,
                    int oldBottom
            ) {
                positionButton(layout, button);
            }
        });

        layout.post(new Runnable() {
            @Override
            public void run() {
                positionButton(layout, button);
            }
        });
    }

    private static void openMirror(WebView webView) {
        String currentUrl = webView.getUrl();
        if (currentUrl == null) {
            currentUrl = "";
        }

        Uri mirrorUri = Uri.parse("http://127.0.0.1:5000/mirror")
                .buildUpon()
                .appendQueryParameter("url", currentUrl)
                .build();
        webView.loadUrl(mirrorUri.toString());
    }

    private static void positionButton(ViewGroup layout, Button button) {
        int layoutWidth = layout.getWidth();
        int layoutHeight = layout.getHeight();
        if (layoutWidth <= 0 || layoutHeight <= 0) {
            return;
        }

        Activity activity = PythonActivity.mActivity;
        if (activity == null) {
            return;
        }

        int buttonWidth = dp(activity, BUTTON_WIDTH_DP);
        int buttonHeight = dp(activity, BUTTON_HEIGHT_DP);
        int visualWidth = buttonHeight;
        int rightMargin = dp(activity, RIGHT_MARGIN_DP);

        // The button is rotated by 90 degrees, so its visual width is its
        // layout height. Position it against the right edge of the WebView.
        int visualCenterX = layoutWidth - rightMargin - visualWidth / 2;
        int x = visualCenterX - buttonWidth / 2;
        int y = layoutHeight / 2 - buttonHeight / 2;

        ViewGroup.LayoutParams genericParams = button.getLayoutParams();
        if (!(genericParams instanceof AbsoluteLayout.LayoutParams)) {
            return;
        }

        AbsoluteLayout.LayoutParams params = (AbsoluteLayout.LayoutParams) genericParams;
        params.x = Math.max(0, x);
        params.y = Math.max(0, y);
        button.setLayoutParams(params);
    }

    private static int dp(Activity activity, int value) {
        return Math.round(value * activity.getResources().getDisplayMetrics().density);
    }
}
