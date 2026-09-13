// Compile-only API declaration. Not included in the runtime host.
package com.orangepixel.utils;

public class ArcadeCanvas implements com.badlogic.gdx.ApplicationListener {
    public boolean argument_noController;
    public com.orangepixel.social.Social mySocial;
    public static int GameState;
    public void create() { throw new UnsupportedOperationException(); }
    public void resize(int width, int height) { throw new UnsupportedOperationException(); }
    public void render() { throw new UnsupportedOperationException(); }
    public void pause() { throw new UnsupportedOperationException(); }
    public void resume() { throw new UnsupportedOperationException(); }
    public void dispose() { throw new UnsupportedOperationException(); }
public int controllersFound;
public void initControllers() { throw new UnsupportedOperationException(); }
public com.orangepixel.controller.Gamepad controller1;
public boolean isFullScreen;
public void setDisplayMode(int width, int height, boolean fullscreen) { throw new UnsupportedOperationException(); }
}
