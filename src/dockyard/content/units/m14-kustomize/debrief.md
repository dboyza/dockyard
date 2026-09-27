# Debrief: Compose environment overlays

The overlay changes a reusable base through an explicit rendering step, and the applied application shows whether that rendered configuration is effective.
Editing a patch file is insufficient when the patch selects the wrong resource or the rendered output is never applied.

## Explain your result

Compare the base, the rendered overlay, and the running consumer, identifying where the intended environment value first differs.

## Transfer beyond this lab

Keep environment-specific changes small and review rendered output as part of a release process.
