package com.eclipsia;

import com.eclipsia.eclipse.EclipseCommand;
import com.eclipsia.eclipse.EclipseEvents;
import com.eclipsia.registry.ModContent;
import net.fabricmc.api.ModInitializer;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Eclipsia implements ModInitializer {
    public static final String MOD_ID = "eclipsia";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MOD_ID, path);
    }

    @Override
    public void onInitialize() {
        ModContent.register();
        EclipseEvents.register();
        EclipseCommand.register();
        LOGGER.info("Eclipsia is watching the sky");
    }
}
