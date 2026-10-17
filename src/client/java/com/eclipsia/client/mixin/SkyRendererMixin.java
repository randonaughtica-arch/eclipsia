package com.eclipsia.client.mixin;

import com.eclipsia.client.EclipseSky;
import net.minecraft.client.renderer.SkyRenderer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.ModifyVariable;

/** Fades the sun out as the moon covers it, and dims the moon during a lunar eclipse. */
@Mixin(SkyRenderer.class)
public class SkyRendererMixin {
    @ModifyVariable(method = "renderSun", at = @At("HEAD"), argsOnly = true, ordinal = 0)
    private float eclipsia$dimSun(float brightness) {
        return brightness * EclipseSky.sunVisibility();
    }

    @ModifyVariable(method = "renderMoon", at = @At("HEAD"), argsOnly = true, ordinal = 0)
    private float eclipsia$dimMoon(float brightness) {
        return brightness * EclipseSky.moonVisibility();
    }
}
