package org.portmaster.gunslugs2;

import com.badlogic.gdx.*;
import com.badlogic.gdx.backends.lwjgl3.*;
import com.badlogic.gdx.graphics.*;
import com.badlogic.gdx.graphics.glutils.HdpiMode;
import com.orangepixel.gunslugs2.myCanvas;
import com.orangepixel.gunslugs2.Globals;
import com.orangepixel.social.Social;
import java.lang.reflect.*;
import java.nio.file.*;

/** Native desktop libGDX host. All original game code stays in the owner's jar. */
public class Main extends myCanvas {
    public final DisplayLayout layout = new DisplayLayout();
    protected Graphics physicalGraphics;
    private GL20 physicalGl;
    private boolean ready;
    private boolean profileReady;
    private long lastFrame;
    private int frames;
    private long start;

    public static Lwjgl3ApplicationConfiguration configuration() throws Exception {
        int width = Integer.getInteger("gunslugs2.width",640), height = Integer.getInteger("gunslugs2.height",480);
        if (width < 160 || height < 160 || width > 8192 || height > 8192)
            throw new IllegalArgumentException("Display dimensions must be 160..8192 pixels");
        Path saves = Paths.get(System.getProperty("gunslugs2.saves","saves")).toAbsolutePath();
        java.nio.file.Files.createDirectories(saves);
        Lwjgl3ApplicationConfiguration cfg = new Lwjgl3ApplicationConfiguration();
        cfg.setTitle("Gunslugs 2"); cfg.setWindowedMode(width,height);
        cfg.setHdpiMode(HdpiMode.Pixels); cfg.setResizable(false);
        cfg.setForegroundFPS(60); cfg.setIdleFPS(30); cfg.useVsync(false);
        cfg.setPreferencesConfig(saves.toString(), com.badlogic.gdx.Files.FileType.Absolute);
        cfg.setOpenGLEmulation(Lwjgl3ApplicationConfiguration.GLEmulation.GL20,2,0);
        cfg.disableAudio(Boolean.getBoolean("gunslugs2.noAudio"));
        cfg.setInitialVisible(!Boolean.getBoolean("gunslugs2.hidden"));
        if (Boolean.getBoolean("gunslugs2.fullscreen")) cfg.setFullscreenMode(Lwjgl3ApplicationConfiguration.getDisplayMode());
        return cfg;
    }

    public static void main(String[] args) throws Exception {
        VerifyGame.check(Paths.get(System.getProperty("gunslugs2.jar","Gunslugs2.jar")));
        System.out.println("Gunslugs 2 PortMaster host 0.1.0 | " + System.getProperty("os.arch") + " | 60 updates/s");
        new Lwjgl3Application(new Main(),configuration());
    }

    @Override public void create() {
        physicalGraphics = Gdx.graphics; physicalGl = Gdx.gl20;
        layout.resize(physicalGraphics.getWidth(),physicalGraphics.getHeight());
        installDisplayBridge();
        Globals.useNOINTERNET = true;
        // Use the game's offline path; never construct the desktop Steam launcher.
        mySocial = (Social)Proxy.newProxyInstance(Main.class.getClassLoader(),new Class<?>[]{Social.class},(self,method,args)-> {
            Class<?> type = method.getReturnType();
            if (type == boolean.class) return false;
            if (type == int.class) return 0;
            if (type == String.class) return "";
            if (type == String[].class) return new String[0];
            return null;
        });
        argument_noController = true;
        super.create();
        InputProcessor input = Gdx.input.getInputProcessor();
        Gdx.input.setInputProcessor((InputProcessor)Proxy.newProxyInstance(Main.class.getClassLoader(),new Class<?>[]{InputProcessor.class},(self,method,args)-> {
            if (method.getName().startsWith("touch") || method.getName().equals("mouseMoved")) {
                args = args.clone(); args[0] = layout.inputX((Integer)args[0]); args[1] = layout.inputY((Integer)args[1]);
            }
            return delegate(input,method,args);
        }));
        ready = true;
        resize(physicalGraphics.getWidth(),physicalGraphics.getHeight());
        start = System.nanoTime();
        System.out.println("GAME_CREATE_OK offline; PortMaster keyboard input; saves=" + System.getProperty("gunslugs2.saves","saves"));
    }

    @Override public void initControllers() {
        // The original noController argument is not checked by initControllers().
        // Override its virtual entry point rather than starting Jamepad/SDL twice.
        controllersFound = 0; controller1.isKeyboard();
    }
    @Override public void init() { super.init(); profileReady = true; }
    @Override public void setDisplayMode(int width,int height,boolean fullscreen) {
        // The launcher owns the hardware mode, including later settings changes.
        if (physicalGraphics != null) isFullScreen = physicalGraphics.isFullscreen();
    }
    @Override public void resize(int width,int height) {
        if (!ready || width < 160 || height < 160) return;
        layout.resize(width,height);
        super.resize(layout.gameWidth,layout.gameHeight);
        System.out.println("GAME_RESIZE_OK " + width + "x" + height + " view=" + layout.gameWidth + "x" + layout.gameHeight);
    }
    @Override public void render() {
        // Match this Windows build's original 60 FPS cap.
        long now = System.nanoTime();
        while (lastFrame != 0 && now - lastFrame < 16666667L) {
            java.util.concurrent.locks.LockSupport.parkNanos(16666667L - (now - lastFrame));
            if (Thread.currentThread().isInterrupted()) break;
            now = System.nanoTime();
        }
        lastFrame = now; // no catch-up updates after a stall/resume
        physicalGl.glDisable(GL20.GL_SCISSOR_TEST);
        physicalGl.glClearColor(0,0,0,1); physicalGl.glClear(GL20.GL_COLOR_BUFFER_BIT);
        super.render();
        frames++;
        int smoke = Integer.getInteger("gunslugs2.smokeFrames",0);
        if (smoke > 0 && frames >= smoke) {
            String capture = System.getProperty("gunslugs2.capture");
            if (capture != null) capture(capture);
            System.out.println("SMOKE_OK frames=" + frames + " state=" + GameState + " seconds=" + (System.nanoTime()-start)/1e9);
            Gdx.app.exit();
        }
    }
    public void capture(String path) {
        Pixmap pixmap = Pixmap.createFromFrameBuffer(0,0,physicalGraphics.getBackBufferWidth(),physicalGraphics.getBackBufferHeight());
        try { PixmapIO.writePNG(Gdx.files.absolute(path),pixmap,-1,true); }
        finally { pixmap.dispose(); }
    }
    @Override public void pause() { if (profileReady) myCanvas.saveSettings(); super.pause(); }
    @Override public void resume() { lastFrame = 0; super.resume(); }
    @Override public void dispose() {
        if (profileReady) myCanvas.saveSettings();
        try { if (ready) super.dispose(); }
        finally { if (physicalGraphics != null) { Gdx.graphics = physicalGraphics; Gdx.gl = physicalGl; Gdx.gl20 = physicalGl; } }
    }

    private static Object delegate(Object target,Method method,Object[] args) throws Throwable {
        try { return method.invoke(target,args); }
        catch (InvocationTargetException e) { throw e.getCause(); }
    }
    private void installDisplayBridge() {
        final int[] framebuffer = {0};
        GL20 gl = (GL20)Proxy.newProxyInstance(Main.class.getClassLoader(),new Class<?>[]{GL20.class},(self,method,args)-> {
            String name = method.getName();
            if (name.equals("glBindFramebuffer")) framebuffer[0] = (Integer)args[1];
            if (framebuffer[0] == 0 && (name.equals("glViewport") || name.equals("glScissor"))) {
                args = new Object[]{layout.viewportX((Integer)args[0]),layout.viewportY((Integer)args[1]),
                    layout.viewportWidth((Integer)args[2]),layout.viewportHeight((Integer)args[3])};
            }
            return delegate(physicalGl,method,args);
        });
        Gdx.gl = gl; Gdx.gl20 = gl;
        Gdx.graphics = (Graphics)Proxy.newProxyInstance(Main.class.getClassLoader(),new Class<?>[]{Graphics.class},(self,method,args)-> {
            switch (method.getName()) {
                case "getWidth": case "getBackBufferWidth": return layout.gameWidth;
                case "getHeight": case "getBackBufferHeight": return layout.gameHeight;
                case "getGL20": return gl;
                case "setWindowedMode": case "setFullscreenMode": case "supportsDisplayModeChange": return false;
                case "setVSync": return null;
                default: return delegate(physicalGraphics,method,args);
            }
        });
    }
}
