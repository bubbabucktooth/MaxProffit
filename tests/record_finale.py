"""Record the real-time local cinematic as a small review GIF."""
import base64
from io import BytesIO
import time
from PIL import Image


def run(cdp, evaluate, check_layout, root):
    js = evaluate
    def wait_for(expression, timeout=12):
        deadline = time.monotonic() + timeout
        while not js(expression):
            if time.monotonic() > deadline:
                raise AssertionError(expression)
            time.sleep(.025)

    def scene(name):
        wait_for(f"reviewDoc.querySelector('.finale-layer').dataset.scene === '{name}'")

    wait_for("!reviewDoc.querySelector('.throw-button').disabled")
    js("for(let i=0;i<40;i++)reviewDoc.querySelector('.throw-button').click()")
    scene('freeze')
    frames, stamps = [], []
    started = time.monotonic()
    while time.monotonic() - started < 12:
        stamps.append(time.monotonic())
        png = base64.b64decode(cdp('Page.captureScreenshot', {'format':'png'})['data'])
        frames.append(Image.open(BytesIO(png)).convert('RGB').resize((720,500)))
        if js("reviewDoc.querySelector('.stage').dataset.phase") == 'game_over':
            break
        time.sleep(.09)
    assert js("reviewDoc.querySelector('.game-over h2').textContent") == 'He motivated Earth to blow itself up.'
    durations = [max(40,round((b-a)*1000)) for a,b in zip(stamps,stamps[1:])] + [1400]
    frames[0].save(root/'finale.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0)
    js("reviewDoc.querySelector('.restart-button').click()")
    assert js("reviewDoc.querySelector('#money-count').value") == '0'

    cdp('Emulation.setDeviceMetricsOverride', {'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
    js("for(let i=0;i<40;i++)reviewDoc.querySelector('.throw-button').click()")
    scene('charge')
    time.sleep(1.05)
    assert js("new DOMMatrixReadOnly(getComputedStyle(reviewDoc.querySelector('.finale-coach')).transform).a") > 1.2
    check_layout('finale-mobile-charge-full')
    scene('orbit')
    time.sleep(1.2)
    check_layout('finale-mobile-orbit-full')
    scene('game_over')
    check_layout('finale-mobile-over')
    js("reviewDoc.querySelector('.restart-button').click()")
    assert js("reviewDoc.querySelector('.stage').dataset.phase") == 'idle'
    assert js("reviewDoc.querySelector('.finale-layer').hidden")
    print(f'PASS: real-time finale GIF ({len(frames)} frames), full mobile camera zoom/orbit, exact closing text and restart')
