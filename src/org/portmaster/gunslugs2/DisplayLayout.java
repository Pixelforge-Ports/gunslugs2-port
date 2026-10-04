package org.portmaster.gunslugs2;

/** Use a 3:2 game view on narrow displays; retain 16:9 or wider on wide displays. */
public final class DisplayLayout {
    public int screenWidth = 640, screenHeight = 480;
    public int gameWidth = 810, gameHeight = 540;
    public int x, y = 26, width = 640, height = 427;
    public void resize(int w, int h) {
        if (w < 160 || h < 160) return;
        screenWidth = w; screenHeight = h;
        // Keep the same vertical game scale while selecting the horizontal field of view.
        gameWidth = (long)w * 9 < (long)h * 16
            ? 810 : Math.max(960, (int)Math.round(540.0 * w / h));
        double scale = Math.min((double)w / gameWidth, (double)h / gameHeight);
        width = (int)Math.round(gameWidth * scale);
        height = (int)Math.round(gameHeight * scale);
        x = (w - width) / 2; y = (h - height) / 2;
    }
    public int viewportX(int value) { return x + (int)Math.round((double)value * width / gameWidth); }
    public int viewportY(int value) { return y + (int)Math.round((double)value * height / gameHeight); }
    public int viewportWidth(int value) { return (int)Math.round((double)value * width / gameWidth); }
    public int viewportHeight(int value) { return (int)Math.round((double)value * height / gameHeight); }
    public int inputX(int value) { return (int)((double)(value - x) * gameWidth / width); }
    public int inputY(int value) {
        return (int)((double)(value - (screenHeight - y - height)) * gameHeight / height);
    }
    public int cursorX(int value) { return viewportX(value); }
    public int cursorY(int value) { return screenHeight - y - height + viewportHeight(value); }
}
