## Pygame Android Window
### Fullscreen + orientation lock + fast rendering for Pygame on Android

This is a small helper file for Pygame games on Android.

It works with Buildozer and python-for-android. It handles the hard parts
of Android screen setup for you.

## What this file does

It does 3 things:

1. Makes your game fullscreen on Android. (Hides the top bar and bottom bar.)
2. Locks the screen to landscape or portrait. You choose which one.
3. Creates a smaller surface to draw on. This makes your game run faster on
   weak phones.

---

## The 2 surfaces — read this first

This file gives you **two surfaces**. They are not the same thing.

Mixing them up is the most common mistake. Please read this part carefully.

| Name | What it is | Draw on it? |
|---|---|---|
| `Window.window` | A small surface. Your game lives here. | ✅ Yes |
| `Window._real_screen` | The real phone screen. | ❌ No |

Think of `Window.window` like a small piece of paper.

You draw your whole game on this small paper.

Then, one time every frame, the code stretches that paper to fill the real
screen. This stretching is done by one line:

```python
pygame.transform.scale(...)
```

### The main rule

> Always draw on `Window.window`.
> Never draw on `Window._real_screen`.

If you draw on `_real_screen` by mistake, it gets erased. This happens the
next time the scale line runs. That line copies over the whole screen every
single frame.

---

## Orientation (landscape or portrait)

Open `Window.py`. Find this line near the top:

```python
ORIENTATION = "landscape"
```

You can set it to:

```python
ORIENTATION = "landscape"
```

or:

```python
ORIENTATION = "portrait"
```

### When to use landscape

Good for:

- Platformers
- Racing games
- Side-scrollers
- Most action games

### When to use portrait

Good for:

- Flappy Bird style games
- Endless runners
- Vertical shooters
- Simple casual games

You only need to change this one line. Nothing else needs to change in
`Window.py`.

---

## Buildozer setup

Open your `buildozer.spec` file. Add or check these lines:

```ini
requirements = python3==3.10.12,hostpython3==3.10.12,pygame,jnius,android

orientation = landscape
fullscreen = 1
```

If you set `ORIENTATION = "portrait"` in `Window.py`, you must also change
`buildozer.spec` to match:

```ini
orientation = portrait
```

Both files must say the same thing. If they don't match, the orientation
may not lock correctly.

---

## Basic example

Here is the simplest possible game loop. You can copy this pattern.

```python
import pygame
import Window

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        Window.handle_window_event(event)

        if event.type == pygame.QUIT:
            running = False

    # Step 1: draw onto Window.window (the small surface)
    Window.window.fill((30, 30, 30))
    pygame.draw.circle(Window.window, (255, 0, 0), (100, 100), 20)

    # Step 2: stretch Window.window onto the real screen
    pygame.transform.scale(
        Window.window,
        (Window.screen_width, Window.screen_height),
        Window._real_screen
    )

    # Step 3: show it on the phone
    pygame.display.flip()

    clock.tick(60)
```

### Remember this order, every frame

1. Draw everything onto `Window.window`
2. Scale `Window.window` into `Window._real_screen`
3. Call `pygame.display.flip()`

---

## Example with a background image

Maybe you want a picture as your background, not just a color. Here is how.

```python
import pygame
import Window

clock = pygame.time.Clock()
running = True

# Load the image ONE TIME, before the loop starts.
# Loading it every frame would be slow.
background_raw = pygame.image.load("background.png")

# Resize it once, so it fits Window.window perfectly.
background_image = pygame.transform.scale(
    background_raw,
    Window.window.get_size()
)

while running:
    for event in pygame.event.get():
        Window.handle_window_event(event)

        if event.type == pygame.QUIT:
            running = False

        # If the screen size changes, resize the background to match.
        if event.type == pygame.VIDEORESIZE:
            background_image = pygame.transform.scale(
                background_raw,
                Window.window.get_size()
            )

    # Step 1: draw the image instead of a color
    Window.window.blit(background_image, (0, 0))

    # ... draw the rest of your game here, on top of the background ...

    # Step 2: stretch Window.window onto the real screen
    pygame.transform.scale(
        Window.window,
        (Window.screen_width, Window.screen_height),
        Window._real_screen
    )

    # Step 3: show it on the phone
    pygame.display.flip()

    clock.tick(60)
```

The only real change is this line:

```python
Window.window.blit(background_image, (0, 0))
```

This replaces `Window.window.fill(...)`. Everything else stays the same.

---

## Performance (making it faster or sharper)

By default, this file uses:

```python
RENDER_SCALE = 0.55
```

This means your game draws at 55% size. Then it gets stretched up to fill
the real screen.

### Example

If the real phone screen is:

```
1920 x 1080
```

then the small render surface becomes:

```
1056 x 594
```

Your game only has to draw about 30% as many pixels each frame. This can
make a noticeable speed difference on slow phones.

### Choosing a value

Lower number, like `0.40`:
- Faster
- Looks a bit more blurry

Higher number, like `0.80`:
- Sharper picture
- More work for the phone

Highest number, `1.0`:
- Full sharpness (native resolution)
- Slowest option

Try a few values and pick what feels right for your game.

---

## If your game uses classes (more advanced)

Some games store the display surface inside a class, like
`self.display`. If you do this, update it after a resize. This matters
because `Window.window` might become a brand new object after a resize.

```python
if event.type == pygame.VIDEORESIZE:
    self.display = Window.window

    if self.current_scene and hasattr(self.current_scene, "display"):
        self.current_scene.display = Window.window
```

---

## Quick reference table

| Name | What it does |
|---|---|
| `ORIENTATION` | Set to `"landscape"` or `"portrait"`. |
| `set_android_fullscreen()` | Forces fullscreen and locks orientation. |
| `handle_window_event(event)` | Call this for every event. Keeps fullscreen and surfaces in sync. |
| `window` | The small surface you draw your game on. |
| `_real_screen` | The real phone screen. Don't draw here directly. |
| `screen_width` | Width of the real screen, in pixels. |
| `screen_height` | Height of the real screen, in pixels. |
| `RENDER_W` | Width of `window`, in pixels. |
| `RENDER_H` | Height of `window`, in pixels. |
| `RENDER_SCALE` | How much smaller `window` is, compared to the real screen. |

---

## What you need installed

- `pygame`
- `pyjnius` (only needed on a real Android phone — ignored everywhere else,
  like when testing on your computer)

---

## Good things to know

- This file is made for Buildozer / python-for-android, using the `sdl2`
  bootstrap.
- Many Android phones never send a `VIDEORESIZE` event while in fullscreen
  mode. The resize handling in this file mainly helps with desktop testing,
  foldable phones, and future devices. So don't worry if you never see this
  event fire on a normal phone — that is expected.
- Please avoid writing this in your other files:

  ```python
  from Window import window
  ```

  The reason: `window` can be replaced with a brand new surface later (for
  example, after a screen resize). Writing `from Window import window` only
  grabs one copy, at the moment you import it. It will not update later.

  Instead, please write:

  ```python
  import Window
  ```

  and then use `Window.window` every time you need it. This way, you
  always get the newest version.


## About this implementation

Built by Wonder Kofi Junior (AlmightyPrime), a solo developer from Ghana. Two years of learning, failing, and finishing. 

## Support The Project

If this repository helped you integrate fullscreen display into your Pygame Android game, or if you'd like to try a fully integrated production example on Google Play, please consider:

Starring this repository

Sharing it with other developers
Downloading and rating Skiptrace on Google Play
Play Store: https://play.google.com/store/apps/details?id=com.almightyprime.skiptrace

Developer story: https://www.fixgamingchannel.com/from-a-jackie-chan-movie-to-google-play-the-story-of-skiptrace/

Your support helps me continue creating tutorials and open-source resources for the Pygame Android community.
