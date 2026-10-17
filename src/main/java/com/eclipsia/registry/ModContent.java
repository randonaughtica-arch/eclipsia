package com.eclipsia.registry;

import com.eclipsia.Eclipsia;
import com.eclipsia.item.EclipseAlmanacItem;
import com.eclipsia.item.TooltipItem;
import java.util.function.Function;
import net.fabricmc.fabric.api.creativetab.v1.FabricCreativeModeTab;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.MapColor;

/** Registers Eclipsia's blocks, items and creative tab. */
public final class ModContent {
    public static final Item UMBRAL_SHARD = registerItem("umbral_shard", Item::new, new Item.Properties());
    public static final Item SANGUINE_SHARD = registerItem("sanguine_shard", Item::new, new Item.Properties());
    public static final Item ECLIPSE_GLASSES = registerItem("eclipse_glasses",
            p -> new TooltipItem(p, "item.eclipsia.eclipse_glasses.tooltip"),
            new Item.Properties().stacksTo(1).equippable(EquipmentSlot.HEAD));
    public static final Item ECLIPSE_ALMANAC = registerItem("eclipse_almanac", EclipseAlmanacItem::new,
            new Item.Properties().stacksTo(1));

    public static final Block UMBRAL_BLOCK = registerBlock("umbral_block", BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_BLACK)
            .strength(3.0F)
            .sound(SoundType.AMETHYST)
            .requiresCorrectToolForDrops());
    public static final Block SANGUINE_BLOCK = registerBlock("sanguine_block", BlockBehaviour.Properties.of()
            .mapColor(MapColor.COLOR_RED)
            .strength(3.0F)
            .sound(SoundType.AMETHYST)
            .requiresCorrectToolForDrops());
    public static final Block CORONA_LAMP = registerBlock("corona_lamp", BlockBehaviour.Properties.of()
            .mapColor(MapColor.GOLD)
            .strength(0.3F)
            .sound(SoundType.GLASS)
            .lightLevel(state -> 15));

    private ModContent() {
    }

    public static void register() {
        CreativeModeTab tab = FabricCreativeModeTab.builder()
                .icon(() -> new ItemStack(ECLIPSE_ALMANAC))
                .title(Component.translatable("itemGroup." + Eclipsia.MOD_ID))
                .displayItems((parameters, output) -> {
                    output.accept(ECLIPSE_GLASSES);
                    output.accept(ECLIPSE_ALMANAC);
                    output.accept(UMBRAL_SHARD);
                    output.accept(SANGUINE_SHARD);
                    output.accept(UMBRAL_BLOCK);
                    output.accept(SANGUINE_BLOCK);
                    output.accept(CORONA_LAMP);
                })
                .build();
        Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, Eclipsia.id("eclipsia"), tab);
    }

    private static Item registerItem(String path, Function<Item.Properties, Item> factory, Item.Properties properties) {
        ResourceKey<Item> key = ResourceKey.create(Registries.ITEM, Eclipsia.id(path));
        return Registry.register(BuiltInRegistries.ITEM, key, factory.apply(properties.setId(key)));
    }

    private static Block registerBlock(String path, BlockBehaviour.Properties properties) {
        ResourceKey<Block> blockKey = ResourceKey.create(Registries.BLOCK, Eclipsia.id(path));
        Block block = Registry.register(BuiltInRegistries.BLOCK, blockKey, new Block(properties.setId(blockKey)));

        ResourceKey<Item> itemKey = ResourceKey.create(Registries.ITEM, Eclipsia.id(path));
        BlockItem item = new BlockItem(block, new Item.Properties().setId(itemKey).useBlockDescriptionPrefix());
        item.registerBlocks(Item.BY_BLOCK, item);
        Registry.register(BuiltInRegistries.ITEM, itemKey, item);
        return block;
    }
}
