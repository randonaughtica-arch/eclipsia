package com.eclipsia.client;

import com.eclipsia.eclipse.EclipseSchedule;
import com.eclipsia.eclipse.EclipseSchedule.Kind;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.world.level.Level;

/** How visible the sun and moon are on the client, given the current eclipse. */
public final class EclipseSky {
    private EclipseSky() {
    }

    public static float sunVisibility() {
        return 1.0F - 0.92F * coverage(Kind.SOLAR);
    }

    public static float moonVisibility() {
        return 1.0F - 0.65F * coverage(Kind.LUNAR);
    }

    private static float coverage(Kind kind) {
        ClientLevel level = Minecraft.getInstance().level;
        if (level == null || level.dimension() != Level.OVERWORLD) {
            return 0.0F;
        }
        return EclipseSchedule.coverage(kind, level.getOverworldClockTime());
    }
}
