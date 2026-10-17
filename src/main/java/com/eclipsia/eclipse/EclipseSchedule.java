package com.eclipsia.eclipse;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;

/**
 * Works out where the overworld is in its eclipse cycle from the overworld clock.
 * The sky effects themselves come from the timelines in data/eclipsia/timeline,
 * which use the same numbers (see {@link EclipseTimings}).
 */
public final class EclipseSchedule {
    public enum Kind {
        SOLAR(EclipseTimings.SOLAR_PEAK, EclipseTimings.SOLAR_PARTIAL, EclipseTimings.SOLAR_TOTAL),
        LUNAR(EclipseTimings.LUNAR_PEAK, EclipseTimings.LUNAR_PARTIAL, EclipseTimings.LUNAR_TOTAL);

        private final long peak;
        private final long partial;
        private final long total;

        Kind(long peak, long partial, long total) {
            this.peak = peak;
            this.partial = partial;
            this.total = total;
        }
    }

    public enum Phase {
        NONE,
        PARTIAL,
        TOTAL
    }

    private EclipseSchedule() {
    }

    /** Signed distance in ticks from the eclipse peak within the current cycle. */
    private static long offsetFromPeak(Kind kind, long clockTicks) {
        return Math.floorMod(clockTicks, EclipseTimings.PERIOD) - kind.peak;
    }

    /** How much of the sun (or moon) is covered, from 0 to 1. */
    public static float coverage(Kind kind, long clockTicks) {
        long distance = Math.abs(offsetFromPeak(kind, clockTicks));
        if (distance >= kind.partial) {
            return 0.0F;
        }
        if (distance <= kind.total) {
            return 1.0F;
        }
        return 1.0F - (float) (distance - kind.total) / (kind.partial - kind.total);
    }

    public static Phase phase(Kind kind, long clockTicks) {
        long distance = Math.abs(offsetFromPeak(kind, clockTicks));
        if (distance >= kind.partial) {
            return Phase.NONE;
        }
        return distance <= kind.total ? Phase.TOTAL : Phase.PARTIAL;
    }

    /** Ticks until the next eclipse of this kind begins (0 while one is under way). */
    public static long ticksUntilStart(Kind kind, long clockTicks) {
        if (phase(kind, clockTicks) != Phase.NONE) {
            return 0L;
        }
        long start = kind.peak - kind.partial;
        return Math.floorMod(start - Math.floorMod(clockTicks, EclipseTimings.PERIOD), EclipseTimings.PERIOD);
    }

    /** Ticks until the current eclipse of this kind ends (0 if none is under way). */
    public static long ticksUntilEnd(Kind kind, long clockTicks) {
        if (phase(kind, clockTicks) == Phase.NONE) {
            return 0L;
        }
        return kind.partial - offsetFromPeak(kind, clockTicks);
    }

    public static String nameKey(Kind kind) {
        return kind == Kind.SOLAR ? "eclipsia.solar" : "eclipsia.lunar";
    }

    /** One line per eclipse kind: either how far it has progressed or how long until it starts. */
    public static List<Component> describe(long clockTicks) {
        List<Component> lines = new ArrayList<>();
        lines.add(Component.translatable("eclipsia.almanac.header").withStyle(ChatFormatting.GOLD));
        for (Kind kind : Kind.values()) {
            Component name = Component.translatable(nameKey(kind));
            if (phase(kind, clockTicks) != Phase.NONE) {
                int percent = Math.round(coverage(kind, clockTicks) * 100.0F);
                lines.add(Component.translatable("eclipsia.almanac.now", name, percent));
            } else {
                long ticks = ticksUntilStart(kind, clockTicks);
                lines.add(Component.translatable("eclipsia.almanac.next", name, ticks / 24000L, (ticks % 24000L) / 1000L));
            }
        }
        return lines;
    }
}
