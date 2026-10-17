package com.eclipsia.eclipse;

import com.eclipsia.Eclipsia;
import com.eclipsia.eclipse.EclipseSchedule.Kind;
import com.eclipsia.eclipse.EclipseSchedule.Phase;
import com.eclipsia.registry.ModContent;
import java.util.EnumMap;
import java.util.Map;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetSubtitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitleTextPacket;
import net.minecraft.network.protocol.game.ClientboundSetTitlesAnimationPacket;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/** Server-side eclipse gameplay: announcements, sun glare and eclipse-empowered monsters. */
public final class EclipseEvents {
    private static final String SOLAR_TAG = "eclipsia.eclipsed_solar";
    private static final String LUNAR_TAG = "eclipsia.eclipsed_lunar";
    private static final int CHECK_INTERVAL = 10;
    /** Looking further up than this (negative pitch is up) counts as looking at the sun. */
    private static final float LOOKING_UP_PITCH = -60.0F;

    private static final Map<Kind, Phase> LAST_PHASE = new EnumMap<>(Kind.class);

    private EclipseEvents() {
    }

    public static void register() {
        ServerTickEvents.END_LEVEL_TICK.register(EclipseEvents::tick);
        ServerEntityEvents.ENTITY_LOAD.register((entity, level) -> {
            if (entity instanceof Mob mob && entity instanceof Enemy) {
                empower(mob, level);
            }
        });
        ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> dropShards(entity));
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> LAST_PHASE.clear());
    }

    private static void tick(ServerLevel level) {
        if (level.dimension() != Level.OVERWORLD || level.getGameTime() % CHECK_INTERVAL != 0) {
            return;
        }
        long clock = level.getOverworldClockTime();
        for (Kind kind : Kind.values()) {
            Phase phase = EclipseSchedule.phase(kind, clock);
            Phase previous = LAST_PHASE.getOrDefault(kind, Phase.NONE);
            if (phase != previous) {
                announce(level, kind, previous, phase);
                LAST_PHASE.put(kind, phase);
            }
            if (phase == Phase.TOTAL) {
                for (ServerPlayer player : level.players()) {
                    if (underOpenSky(level, player)) {
                        award(player, kind == Kind.SOLAR ? "totality" : "blood_moon");
                    }
                }
            }
        }
        if (EclipseSchedule.phase(Kind.SOLAR, clock) != Phase.NONE) {
            for (ServerPlayer player : level.players()) {
                checkSunGlare(level, player);
            }
        }
    }

    private static void announce(ServerLevel level, Kind kind, Phase from, Phase to) {
        String key = kind == Kind.SOLAR ? "eclipsia.solar" : "eclipsia.lunar";
        ChatFormatting color = kind == Kind.SOLAR ? ChatFormatting.GOLD : ChatFormatting.DARK_RED;
        for (ServerPlayer player : level.players()) {
            if (from == Phase.NONE) {
                player.connection.send(new ClientboundSetTitlesAnimationPacket(20, 80, 30));
                player.connection.send(new ClientboundSetSubtitleTextPacket(
                        Component.translatable(key + ".subtitle").withStyle(ChatFormatting.GRAY)));
                player.connection.send(new ClientboundSetTitleTextPacket(
                        Component.translatable(key + ".title").withStyle(color)));
            } else if (to == Phase.TOTAL) {
                player.sendSystemMessage(Component.translatable(key + ".totality").withStyle(color), true);
            } else if (to == Phase.NONE) {
                player.sendSystemMessage(Component.translatable(key + ".end").withStyle(ChatFormatting.GRAY), true);
            }
        }
    }

    private static void checkSunGlare(ServerLevel level, ServerPlayer player) {
        if (player.isSpectator() || player.getXRot() > LOOKING_UP_PITCH || !underOpenSky(level, player)) {
            return;
        }
        if (player.getItemBySlot(EquipmentSlot.HEAD).is(ModContent.ECLIPSE_GLASSES)) {
            award(player, "safe_viewing");
            return;
        }
        if (!player.hasEffect(MobEffects.BLINDNESS)) {
            player.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 80, 0));
            player.sendSystemMessage(Component.translatable("eclipsia.sun_glare").withStyle(ChatFormatting.YELLOW), true);
            award(player, "sun_glare");
        }
    }

    private static boolean underOpenSky(ServerLevel level, ServerPlayer player) {
        return level.canSeeSky(BlockPos.containing(player.getEyePosition()));
    }

    /** Monsters that appear during an eclipse are empowered for the rest of it. */
    private static void empower(Mob mob, ServerLevel level) {
        if (level.dimension() != Level.OVERWORLD) {
            return;
        }
        long clock = level.getOverworldClockTime();
        for (Kind kind : Kind.values()) {
            if (EclipseSchedule.phase(kind, clock) == Phase.NONE) {
                continue;
            }
            String tag = kind == Kind.SOLAR ? SOLAR_TAG : LUNAR_TAG;
            if (!mob.addTag(tag)) {
                return;
            }
            int duration = (int) EclipseSchedule.ticksUntilEnd(kind, clock) + 200;
            mob.addEffect(new MobEffectInstance(MobEffects.SPEED, duration, 0));
            if (kind == Kind.LUNAR) {
                mob.addEffect(new MobEffectInstance(MobEffects.STRENGTH, duration, 0));
            }
            return;
        }
    }

    private static void dropShards(LivingEntity entity) {
        if (!(entity.level() instanceof ServerLevel level)) {
            return;
        }
        Item shard = null;
        if (entity.removeTag(SOLAR_TAG)) {
            shard = ModContent.UMBRAL_SHARD;
        } else if (entity.removeTag(LUNAR_TAG)) {
            shard = ModContent.SANGUINE_SHARD;
        }
        if (shard != null && entity.getRandom().nextFloat() < 0.6F) {
            entity.spawnAtLocation(level, new ItemStack(shard, 1 + entity.getRandom().nextInt(2)));
        }
    }

    private static void award(ServerPlayer player, String name) {
        AdvancementHolder advancement = player.level().getServer().getAdvancements().get(Eclipsia.id(name));
        if (advancement != null) {
            player.getAdvancements().award(advancement, "witnessed");
        }
    }
}
