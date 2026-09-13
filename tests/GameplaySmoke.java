package org.portmaster.gunslugs2;

import com.badlogic.gdx.*;
import com.badlogic.gdx.backends.lwjgl3.Lwjgl3Application;
import com.orangepixel.gunslugs2.myCanvas;
import java.lang.reflect.Field;
import java.util.*;

/** Test-only keyboard driver, excluded from the shipped host. */
public final class GameplaySmoke extends Main {
    private int frame, previousState = -1;
    private boolean gameplay;
    private final Set<Integer> held = new HashSet<>();
    public static void main(String[] args) throws Exception {
        new Lwjgl3Application(new GameplaySmoke(),configuration());
    }
    private void key(int code,boolean down) {
        if (down) { if (held.add(code)) Gdx.input.getInputProcessor().keyDown(code); }
        else if (held.remove(code)) Gdx.input.getInputProcessor().keyUp(code);
    }
    private Object value(Object object,String name) throws Exception {
        Field field = object.getClass().getDeclaredField(name); field.setAccessible(true);
        return field.get(object);
    }
    @Override public void render() {
        frame++;
        if (physicalGraphics.getWidth() != Integer.getInteger("gunslugs2.width",640)
            || physicalGraphics.getHeight() != Integer.getInteger("gunslugs2.height",480))
            throw new AssertionError("Game changed physical resolution");
        if (frame >= 200) key(Input.Keys.X, frame % 120 < 60);
        if (frame == 1180 && GameState == 64) key(Input.Keys.ESCAPE,true);
        if (frame == 1182) key(Input.Keys.ESCAPE,false);
        if (frame >= 1250 && frame <= 1700) key(Input.Keys.RIGHT,true);
        if (frame == 1701) key(Input.Keys.RIGHT,false);
        if (frame >= 450) key(Input.Keys.Z,frame % 180 < 20);
        super.render();
        if (GameState != previousState) {
            System.out.println("STATE frame=" + frame + " state=" + GameState);
            previousState = GameState;
        }
        gameplay |= GameState == 43;
        if (frame == 180 || frame == 900 || frame == 1200 || frame == 1400 || frame == 1600 || frame == 1800) {
            capture(System.getProperty("gunslugs2.output") + "/frame-" + frame + ".png");
            try {
                Field field = myCanvas.class.getDeclaredField("myPlayer"); field.setAccessible(true);
                Object player = field.get(null);
                System.out.println("PLAYER frame="+frame+" x="+value(player,"x")+" y="+value(player,"y"));
            } catch (Exception e) { throw new IllegalStateException(e); }
        }
        if (frame == 1800) {
            if (!gameplay) throw new AssertionError("Did not reach gameplay");
            for (int code : new HashSet<>(held)) key(code,false);
            System.out.println("GAMEPLAY_OK 1800 frames; gameplay reached; keyboard events delivered; inspect screenshots");
            Gdx.app.exit();
        }
    }
}
