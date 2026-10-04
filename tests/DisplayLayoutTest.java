package org.portmaster.gunslugs2;

/** Standalone viewport and input checks; does not require purchased game data. */
public final class DisplayLayoutTest {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    private static void verify(DisplayLayout layout, int w, int h, int gameW,
                               int viewW, int viewH, int x, int y) {
        layout.resize(w, h);
        String label = w + "x" + h;
        check(layout.screenWidth == w && layout.screenHeight == h, label + " physical size");
        check(layout.gameWidth == gameW && layout.gameHeight == 540, label + " game view");
        check(layout.width == viewW && layout.height == viewH
            && layout.x == x && layout.y == y, label + " viewport");
        check(layout.viewportX(0) == x && layout.viewportY(0) == y, label + " viewport origin");
        check(layout.viewportWidth(gameW) == viewW && layout.viewportHeight(540) == viewH,
            label + " full viewport scaling");
        check(layout.inputX(layout.cursorX(0)) == 0 && layout.inputY(layout.cursorY(0)) == 0,
            label + " input origin");
        check(layout.inputX(layout.cursorX(gameW)) == gameW
            && layout.inputY(layout.cursorY(540)) == 540, label + " input endpoint");
        // Verify top-origin cursor coordinates even when the two bars differ by one pixel.
        check(layout.cursorY(0) == h - y - viewH, label + " top bar mapping");
        for (int gx = 0; gx <= gameW; gx += 27) {
            int mapped = layout.inputX(layout.cursorX(gx));
            check(Math.abs(mapped - gx) <= 1, label + " horizontal input round trip");
        }
        for (int gy = 0; gy <= 540; gy += 18) {
            int mapped = layout.inputY(layout.cursorY(gy));
            check(Math.abs(mapped - gy) <= 1, label + " vertical input round trip");
        }
        System.out.println("LAYOUT_OK " + label + " view=" + gameW + "x540 viewport=" + viewW + "x" + viewH);
    }
    public static void main(String[] args) {
        DisplayLayout layout = new DisplayLayout();
        verify(layout, 720, 480, 810, 720, 480, 0, 0);
        verify(layout, 640, 480, 810, 640, 427, 0, 26);
        verify(layout, 720, 720, 810, 720, 480, 0, 120);
        verify(layout, 1024, 768, 810, 1024, 683, 0, 42);
        verify(layout, 1280, 720, 960, 1280, 720, 0, 0);
        verify(layout, 1920, 1080, 960, 1920, 1080, 0, 0);
        verify(layout, 2560, 1080, 1280, 2560, 1080, 0, 0);
        verify(layout, 720, 720, 810, 720, 480, 0, 120);
        layout.resize(0, 0);
        check(layout.screenWidth == 720 && layout.screenHeight == 720
            && layout.gameWidth == 810 && layout.width == 720 && layout.height == 480,
            "Invalid resize changed the current view");
        System.out.println("DISPLAY_LAYOUT_OK aspect ratios, resize transitions, viewport and input scaling");
    }
}
