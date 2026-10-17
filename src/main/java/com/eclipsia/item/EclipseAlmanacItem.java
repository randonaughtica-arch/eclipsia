package com.eclipsia.item;

import com.eclipsia.eclipse.EclipseSchedule;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;

/** Tells the player how far away the next solar and lunar eclipses are. */
public class EclipseAlmanacItem extends TooltipItem {
    public EclipseAlmanacItem(Properties properties) {
        super(properties, "item.eclipsia.eclipse_almanac.tooltip");
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (!level.isClientSide()) {
            for (Component line : EclipseSchedule.describe(level.getOverworldClockTime())) {
                player.sendSystemMessage(line);
            }
        }
        return InteractionResult.SUCCESS;
    }
}
