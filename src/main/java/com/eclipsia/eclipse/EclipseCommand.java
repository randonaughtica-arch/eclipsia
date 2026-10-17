package com.eclipsia.eclipse;

import com.eclipsia.eclipse.EclipseSchedule.Kind;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;

/** {@code /eclipse}: shows the eclipse schedule and the /time add needed to reach each eclipse. */
public final class EclipseCommand {
    private EclipseCommand() {
    }

    public static void register() {
        CommandRegistrationCallback.EVENT.register((dispatcher, buildContext, selection) ->
                dispatcher.register(Commands.literal("eclipse").executes(context -> {
                    long clock = context.getSource().getLevel().getOverworldClockTime();
                    for (Component line : EclipseSchedule.describe(clock)) {
                        context.getSource().sendSuccess(() -> line, false);
                    }
                    for (Kind kind : Kind.values()) {
                        long ticks = EclipseSchedule.ticksUntilStart(kind, clock);
                        if (ticks > 0) {
                            context.getSource().sendSuccess(() -> Component.translatable("commands.eclipsia.next",
                                    Component.translatable(EclipseSchedule.nameKey(kind)), ticks, ticks), false);
                        }
                    }
                    return 1;
                })));
    }
}
