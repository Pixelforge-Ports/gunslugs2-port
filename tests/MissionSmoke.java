package org.portmaster.gunslugs2;

import com.badlogic.gdx.*;
import com.badlogic.gdx.backends.lwjgl3.Lwjgl3Application;
import com.orangepixel.gunslugs2.myCanvas;
import java.lang.reflect.Field;
import java.util.*;

/** Navigate the hub via keyboard events; inspect state without changing game data. */
public final class MissionSmoke extends Main {
    private final Set<Integer> held = new HashSet<>();
    private int frame, combatFrames;
    public static void main(String[] args) throws Exception { new Lwjgl3Application(new MissionSmoke(),configuration()); }
    private Object value(Object object,String name) throws Exception {
        Class<?> type = object instanceof Class ? (Class<?>)object : object.getClass();
        Field field = type.getDeclaredField(name); field.setAccessible(true);
        return field.get(object instanceof Class ? null : object);
    }
    private void key(int code,boolean down) {
        if (down) { if (held.add(code)) Gdx.input.getInputProcessor().keyDown(code); }
        else if (held.remove(code)) Gdx.input.getInputProcessor().keyUp(code);
    }
    @Override public void render() {
        frame++;
        try {
            if (GameState == 42 && frame > 180) key(Input.Keys.X,frame % 30 < 2);
            else if (GameState == 43) {
                Object world = value(myCanvas.class,"myWorld");
                Object player = value(myCanvas.class,"myPlayer");
                if ((Boolean)value(world,"inControlCenter")) {
                    Object[] monsters = (Object[])value(myCanvas.class,"monsterList");
                    for (Object monster : monsters) {
                        if ((Boolean)value(monster,"deleted") || (Integer)value(monster,"myType") != 5
                            || (Integer)value(monster,"subType") != 24) continue;
                        int difference = (Integer)value(monster,"x") - (Integer)value(player,"x");
                        key(Input.Keys.RIGHT,difference > 3); key(Input.Keys.LEFT,difference < -3);
                        key(Input.Keys.X,Math.abs(difference) <= 3 && frame % 30 < 2);
                        key(Input.Keys.Z,Math.abs(difference) > 24 && frame % 90 < 12);
                        if (frame % 120 == 0) System.out.println("DOOR target="+value(monster,"x")+" player="+value(player,"x")+","+value(player,"y")+" delta="+difference);
                        break;
                    }
                } else {
                    combatFrames++;
                    key(Input.Keys.LEFT,false); key(Input.Keys.RIGHT,combatFrames < 300);
                    key(Input.Keys.X,true); key(Input.Keys.Z,combatFrames % 90 < 10);
                    if (combatFrames == 180 || combatFrames == 360) capture(System.getProperty("gunslugs2.output")+"/combat-"+combatFrames+".png");
                    if (combatFrames == 360) {
                        for (int code : new HashSet<>(held)) key(code,false);
                        System.out.println("MISSION_OK: entered combat through hub door; 360 combat frames; keyboard move/fire/jump");
                        Gdx.app.exit();
                    }
                }
            } else { key(Input.Keys.X,false); key(Input.Keys.RIGHT,false); key(Input.Keys.LEFT,false); }
            if (frame % 120 == 0) System.out.println("MISSION_PROGRESS frame="+frame+" state="+GameState+" combat="+combatFrames);
            if (frame == 600) capture(System.getProperty("gunslugs2.output")+"/mission-navigation.png");
            if (frame > 2400) throw new AssertionError("Could not reach combat stage through hub");
        } catch (Exception e) { throw new IllegalStateException(e); }
        super.render();
    }
}
