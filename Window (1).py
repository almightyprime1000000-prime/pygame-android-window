import threading
import pygame
pygame.init()


# ===============================
# ORIENTATION SETTING
# Set this to "landscape" or "portrait" depending on your game.
# Landscape  -> racing games, platformers, side-scrollers, etc.
# Portrait   -> Flappy Bird-style games, vertical scrollers, etc.
# Everything below reads this single setting — change it here only.
# ===============================

ORIENTATION = "landscape"  # "landscape" or "portrait"


# ===============================
# ANDROID FULLSCREEN / ORIENTATION
# Forces the orientation chosen above and hides the system status/nav bars.
# Uses pyjnius to call native Android APIs directly — no-ops safely on
# non-Android platforms (the try/except swallows the ImportError).
# ===============================

def set_android_fullscreen():
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        View = autoclass('android.view.View')
        activity = PythonActivity.mActivity

        # --- Force orientation based on ORIENTATION setting above ---
        ActivityInfo = autoclass('android.content.pm.ActivityInfo')
        if ORIENTATION == "portrait":
            requested_orientation = ActivityInfo.SCREEN_ORIENTATION_SENSOR_PORTRAIT
        else:
            requested_orientation = ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE
        activity.setRequestedOrientation(requested_orientation)

        # --- Hide status bar / nav bar, allow drawing under notch cutouts ---
        win = activity.getWindow()
        decorView = win.getDecorView()
        attrs = win.getAttributes()
        LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
        attrs.layoutInDisplayCutoutMode = (
            LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
        )
        win.setAttributes(attrs)
        flags = (
            View.SYSTEM_UI_FLAG_FULLSCREEN |
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
            View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN |
            View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_LAYOUT_STABLE
        )
        decorView.setSystemUiVisibility(flags)
    except Exception:
        # Not running on Android (e.g. desktop testing) — ignore
        pass


# ===============================
# INITIAL SETUP
# Apply fullscreen immediately, then give Android a moment to settle
# before measuring the real screen size.
# ===============================

set_android_fullscreen()
pygame.time.delay(500)


# ===============================
# REAL SCREEN SURFACE
# The actual physical display pygame draws to, at full device resolution.
# ===============================

_real_screen  = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.NOFRAME)
screen_width  = _real_screen.get_width()
screen_height = _real_screen.get_height()

# Android sometimes resets system UI flags shortly after launch (e.g. once
# the splash screen drops) — reapply fullscreen one second later as a safety net.
threading.Timer(1.0, set_android_fullscreen).start()


# ===============================
# RENDER SURFACE
# A smaller off-screen surface that the game actually draws to.
# Rendering at a reduced resolution (55%) and then scaling up to the real
# screen is cheaper than rendering at native resolution, which matters on
# lower-end Android devices.
# ===============================

RENDER_SCALE = 0.55
RENDER_W = int(screen_width  * RENDER_SCALE)
RENDER_H = int(screen_height * RENDER_SCALE)

# 'window' is the surface the rest of the game draws to.
# main.py's render loop is responsible for scaling this surface up and
# blitting it onto _real_screen each frame.
window = pygame.Surface((RENDER_W, RENDER_H))


# ===============================
# EVENT HANDLING — KEEP FULLSCREEN / RENDER SURFACE IN SYNC
# Call handle_window_event(event) from your main event loop for every
# pygame event. It re-applies fullscreen on focus/touch/resume, and keeps
# the render surface correctly sized if Android changes the screen
# dimensions out from under you (e.g. rotating the device, or a
# multi-window/foldable resize).
#
# Usage in your main loop:
#
#     for event in pygame.event.get():
#         Window.handle_window_event(event)
#         ... your other event handling ...
#
# After a VIDEORESIZE event, re-read Window.window, Window.screen_width,
# and Window.screen_height (they may have changed), and push the new
# 'window' surface into your current scene if it caches a reference to it.
# ===============================

def handle_window_event(event):
    global _real_screen, screen_width, screen_height, window, RENDER_W, RENDER_H

    # Re-apply fullscreen when the app regains focus
    if event.type == pygame.ACTIVEEVENT:
        if event.state == 2 and event.gain == 1:
            set_android_fullscreen()

    # Re-apply fullscreen on first touch (helps recover from system UI
    # popping back up after a notification swipe, etc.)
    if event.type == pygame.FINGERDOWN:
        set_android_fullscreen()

    # Custom delayed-fullscreen trigger (fire pygame.USEREVENT + 1 from
    # wherever you scheduled it, then disable the timer so it only fires once)
    if event.type == pygame.USEREVENT + 1:
        set_android_fullscreen()
        pygame.time.set_timer(pygame.USEREVENT + 1, 0)

    # Keep the 55% render surface in sync if the real screen size changes
    # (device rotation, foldable resize, etc.) instead of letting pygame's
    # default resize behavior break the scaling architecture.
    if event.type == pygame.VIDEORESIZE:
        if screen_width != event.w or screen_height != event.h:
            # Re-setup the true hardware display surface
            _real_screen = pygame.display.set_mode(
                (event.w, event.h), pygame.FULLSCREEN | pygame.NOFRAME
            )
            screen_width, screen_height = event.w, event.h

            # Re-calculate and resize the render surface at the same scale
            RENDER_W = int(screen_width  * RENDER_SCALE)
            RENDER_H = int(screen_height * RENDER_SCALE)
            window = pygame.Surface((RENDER_W, RENDER_H))
