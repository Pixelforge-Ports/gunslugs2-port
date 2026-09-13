package org.portmaster.gunslugs2;

import java.io.InputStream;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.jar.JarFile;

/** Validation only: the owner's game jar is never modified or converted. */
public final class VerifyGame {
    public static final String SHA256 = "8f92f9ea2f84b055be744f98b911dbcdc6f8199bd1ec75b54338bff3ffffa913";
    public static void check(Path path) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream in = Files.newInputStream(path)) {
            byte[] buffer = new byte[65536]; int count;
            while ((count = in.read(buffer)) != -1) digest.update(buffer, 0, count);
        }
        StringBuilder result = new StringBuilder();
        for (byte value : digest.digest()) result.append(String.format("%02x", value & 255));
        if (!SHA256.equals(result.toString())) throw new IllegalArgumentException("Unsupported Gunslugs2.jar fingerprint. Use the supported Windows/GOG build documented in README.");
        try (JarFile jar = new JarFile(path.toFile())) {
            for (String name : new String[]{"com/orangepixel/gunslugs2/myCanvas.class", "libgdxarm64.so", "linux/arm64/org/lwjgl/liblwjgl.so", "spl2.png"})
                if (jar.getEntry(name) == null) throw new IllegalArgumentException("Missing game component: " + name);
        }
        System.out.println("GAME_DATA_OK original jar verified; no conversion needed");
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Usage: VerifyGame Gunslugs2.jar");
        check(Paths.get(args[0]));
    }
}
