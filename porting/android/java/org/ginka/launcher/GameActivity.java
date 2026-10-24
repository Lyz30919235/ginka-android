package org.ginka.launcher;

import android.Manifest;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.provider.DocumentsContract;
import android.provider.Settings;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;
import java.io.File;
import org.cocos2dx.lib.Cocos2dxHelper;
import org.tvp.kirikiri2.KR2Activity;

/** GINKA resource selection and launch entry for the pinned runtime. */
public final class GameActivity extends KR2Activity {
    private final Handler handler = new Handler();
    private FrameLayout cover;
    private boolean launched;
    private String pendingPath;
    private int retries;
    private static native int nativeStartup(String path);

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        System.loadLibrary("ginkalaunch");
        cover = new FrameLayout(this);
        cover.setBackgroundColor(Color.rgb(6, 27, 48));
        TextView title = new TextView(this);
        title.setText("GINKA");
        title.setTextColor(Color.WHITE);
        title.setTextSize(36);
        title.setGravity(Gravity.CENTER);
        cover.addView(title, new FrameLayout.LayoutParams(-1, -1));
        addContentView(cover, new ViewGroup.LayoutParams(-1, -1));
        handler.postDelayed(this::prepare, 1500);
    }

    /** Requests the file access needed to read the separate resource directory. */
    private void prepare() {
        if (launched || isFinishing()) return;
        if (Build.VERSION.SDK_INT >= 30 && !Environment.isExternalStorageManager()) {
            new AlertDialog.Builder(this).setTitle("GINKA 资源访问")
                .setMessage("游戏资源单独存放。请允许访问资源目录，然后选择包含 data.xp3 的 GINKA 文件夹。")
                .setPositiveButton("前往设置", (d,w) -> startActivityForResult(new Intent(
                    Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION,
                    Uri.parse("package:" + getPackageName())), 11))
                .setNegativeButton("退出", (d,w) -> finish()).show();
            return;
        }
        if (Build.VERSION.SDK_INT < 30 && checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.READ_EXTERNAL_STORAGE, Manifest.permission.WRITE_EXTERNAL_STORAGE}, 13);
            return;
        }
        String saved = getPreferences(0).getString("resource", "");
        String requested = getIntent().getStringExtra("resource_path");
        String[] candidates = { requested == null ? "" : requested, saved,
            Environment.getExternalStorageDirectory() + "/Download/GINKA/data.xp3",
            Environment.getExternalStorageDirectory() + "/GINKA/data.xp3" };
        for (String path : candidates) {
            if (!path.isEmpty() && new File(path).isFile()) { launch(path); return; }
        }
        chooseResources();
    }

    /** Uses Android's folder picker without copying or deleting the chosen files. */
    private void chooseResources() {
        new AlertDialog.Builder(this).setTitle("GINKA")
            .setMessage("请先解压配套资源，再选择包含 data.xp3 的 GINKA 文件夹。")
            .setPositiveButton("选择资源目录", (d,w) -> startActivityForResult(
                new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE), 12))
            .setNegativeButton("退出", (d,w) -> finish()).show();
    }

    /** Converts the selected external-storage document directory to its file path. */
    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == 11) { prepare(); return; }
        if (request != 12 || result != RESULT_OK || data == null) return;
        Uri uri = data.getData();
        if (uri == null || !"com.android.externalstorage.documents".equals(uri.getAuthority())) {
            fail("请选择手机内部存储或 SD 卡中的本地资源文件夹。"); return;
        }
        String id = DocumentsContract.getTreeDocumentId(uri);
        int colon = id.indexOf(':');
        if (colon < 1) { fail("无法识别资源目录。"); return; }
        String volume = id.substring(0, colon);
        File root = volume.equals("primary") ? Environment.getExternalStorageDirectory() : new File("/storage", volume);
        try {
            File selected = new File(root, id.substring(colon + 1)).getCanonicalFile();
            if (!selected.toPath().startsWith(root.getCanonicalFile().toPath())) { fail("资源目录无效。"); return; }
            File archive = new File(selected, "data.xp3");
            if (!archive.isFile()) { fail("所选目录中没有 data.xp3，请选择解压后的 GINKA 文件夹。"); return; }
            launch(archive.getAbsolutePath());
        } catch (Exception e) { fail("无法读取资源目录：" + e.getMessage()); }
    }

    /** Resumes setup only when the requested storage permissions were granted. */
    @Override public void onRequestPermissionsResult(int request, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(request, permissions, results);
        if (request == 13) {
            for (int value : results) if (value != PackageManager.PERMISSION_GRANTED) { fail("未取得资源读取权限。"); return; }
            prepare();
        }
    }

    /** Calls the engine launch API on the engine's own GL thread. */
    private void launch(String path) {
        if (launched) return;
        pendingPath = path;
        Cocos2dxHelper.runOnGLThread(() -> {
            final int code = nativeStartup(pendingPath);
            runOnUiThread(() -> {
                if (code == 5 && retries++ < 3) { handler.postDelayed(() -> launch(pendingPath), 500); return; }
                if (code != 0) { fail("游戏引擎启动失败，代码：" + code); return; }
                launched = true;
                getPreferences(0).edit().putString("resource", pendingPath).apply();
                if (cover.getParent() instanceof ViewGroup) ((ViewGroup)cover.getParent()).removeView(cover);
            });
        });
    }

    /** Shows an actionable error instead of presenting an empty game screen. */
    private void fail(String message) {
        new AlertDialog.Builder(this).setTitle("GINKA").setMessage(message)
            .setPositiveButton("重新选择资源", (d,w) -> chooseResources())
            .setNegativeButton("退出", (d,w) -> finish()).show();
    }
}
