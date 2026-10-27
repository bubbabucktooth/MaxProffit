"""Verify complete cinematic rounds without accessing the user's browser profile."""
import time


def run(cdp, evaluate, check_layout, root):
    js = evaluate
    def wait_for(expression, timeout=12):
        deadline = time.monotonic() + timeout
        while not js(expression):
            if time.monotonic() > deadline:
                raise AssertionError(expression)
            time.sleep(.025)

    def count():
        return int(js("reviewDoc.querySelector('#money-count').value"))

    def settle():
        wait_for("!reviewDoc.querySelector('.flying-bill') && !reviewDoc.querySelector('#pending-count').textContent && ['idle','finale','game_over'].includes(reviewDoc.querySelector('.stage').dataset.phase)")

    def scene(name):
        wait_for(f"reviewDoc.querySelector('.finale-layer').dataset.scene === '{name}'")

    def reset():
        assert js("reviewDoc.querySelector('.stage').dataset.phase") == 'game_over'
        js("reviewDoc.querySelector('.restart-button').click()")
        assert count() == 0
        assert js("reviewDoc.querySelector('.stage').dataset.expression") == 'believer'
        assert js("reviewDoc.querySelector('.stage').dataset.phase") == 'idle'
        assert js("reviewDoc.querySelector('.speech-bubble').hidden")
        assert js("reviewDoc.querySelector('.finale-layer').hidden")
        assert js("!reviewDoc.querySelector('.throw-button').disabled")
        assert js("!reviewDoc.querySelector('.flight-layer').children.length")
        assert js("!reviewDoc.querySelector('.explosion').children.length")

    def observe_quotes():
        js("""(() => {const w=reviewDoc.defaultView;w.quoteLog=[];
        w.quoteObserver=new w.MutationObserver(records=>{for(const r of records)if(r.oldValue)w.quoteLog.push(r.oldValue)});
        w.quoteObserver.observe(reviewDoc.querySelector('.speech-bubble'),{attributes:true,attributeFilter:['data-quote-id'],attributeOldValue:true});})()""")

    wait_for("!reviewDoc.querySelector('.throw-button').disabled")
    assert count() == 0
    assert js("!reviewDoc.querySelector('.motivation-meter') && !reviewDoc.querySelector('.level-track')")
    assert js("reviewDoc.querySelector('.receipt').classList.contains('sr-only')")
    check_layout('finale-game-desktop')
    ids = []
    durations = []
    for hit in range(1, 41):
        js("reviewDoc.querySelector('.throw-button').click()")
        if hit == 1:
            assert count() == 0
        else:
            js("reviewDoc.querySelectorAll('.flying-bill').forEach(b=>b.getAnimations().forEach(a=>a.finish()))")
        wait_for(f"reviewDoc.querySelector('#money-count').value === '{hit}'")
        expected_level = (hit - 1) // 10 + 1
        assert js("Number(reviewDoc.querySelector('.stage').dataset.level)") == expected_level
        quote_id = js("reviewDoc.querySelector('.speech-bubble').dataset.quoteId")
        assert quote_id not in ids
        ids.append(quote_id)
        durations.append(float(js("getComputedStyle(reviewDoc.querySelector('#character .head-idle')).animationDuration").rstrip('s')))
    assert all(a > b for a,b in zip(durations,durations[1:]))
    assert len(set(ids)) == 40
    settle()
    assert js("reviewDoc.querySelector('.stage').dataset.phase") == 'finale'
    scene('freeze')
    check_layout('finale-freeze')
    # Ignore invalid extra throws/restarts during the finale, even when dispatched.
    js("reviewDoc.querySelector('.throw-button').disabled=false; for(let i=0;i<100;i++)reviewDoc.querySelector('.throw-button').click();reviewDoc.querySelector('.restart-button').click()")
    assert count() == 40
    assert js("reviewDoc.querySelector('.stage').dataset.phase") == 'finale'
    scene('charge')
    time.sleep(1.05)
    check_layout('finale-charge')
    scale = js("new DOMMatrixReadOnly(getComputedStyle(reviewDoc.querySelector('.finale-coach')).transform).a")
    assert scale > 2, scale
    scene('orbit')
    time.sleep(1.2)
    check_layout('finale-orbit')
    assert js("!reviewDoc.querySelector('.space-scene').hidden")
    scene('cracks')
    time.sleep(.7)
    check_layout('finale-cracks')
    scene('explosion')
    time.sleep(.25)
    check_layout('finale-explosion')
    assert js("reviewDoc.querySelectorAll('.planet-fragment,.fire-fragment').length") == 32
    scene('game_over')
    assert js("reviewDoc.querySelector('.stage').dataset.phase") == 'game_over'
    assert js("reviewDoc.querySelector('.game-over h2').textContent") == 'He motivated Earth to blow itself up.'
    assert js("reviewDoc.querySelector('.restart-button').textContent") == 'Try again.'
    assert js("reviewDoc.activeElement.classList.contains('restart-button')")
    check_layout('finale-game-over')
    reset()

    # A second whole round, fired as 100 clicks, starts only one cinematic.
    observe_quotes()
    js("""(() => {const w=reviewDoc.defaultView;w.scenes=[];
    w.sceneObserver=new w.MutationObserver(records=>{for(const r of records)if(r.oldValue)w.scenes.push(r.oldValue)});
    w.sceneObserver.observe(reviewDoc.querySelector('.finale-layer'),{attributes:true,attributeFilter:['data-scene'],attributeOldValue:true});})()""")
    js("for(let i=0;i<100;i++)reviewDoc.querySelector('.throw-button').click()")
    assert js("reviewDoc.querySelectorAll('.flying-bill').length") <= 12
    assert js("reviewDoc.querySelector('.throw-button').disabled")
    js("document.querySelector('iframe').contentWindow.postMessage({type:'streamlit:render',args:{}},location.origin)")
    settle()
    assert count() == 40
    burst_ids = js("reviewDoc.defaultView.quoteLog.concat(reviewDoc.querySelector('.speech-bubble').dataset.quoteId)")
    assert len(burst_ids) == 40 and set(burst_ids) == set(ids)
    js("reviewDoc.defaultView.quoteObserver.disconnect()")
    scene('game_over')
    scenes = js("reviewDoc.defaultView.scenes.concat(reviewDoc.querySelector('.finale-layer').dataset.scene)")
    assert scenes == ['freeze','charge','orbit','cracks','explosion','darkness','game_over'], scenes
    js("reviewDoc.defaultView.sceneObserver.disconnect()")
    reset()

    # Third round: mobile with reduced motion still tells the entire story.
    cdp('Emulation.setDeviceMetricsOverride', {'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
    cdp('Emulation.setEmulatedMedia', {'features':[{'name':'prefers-reduced-motion','value':'reduce'}]})
    wait_for("reviewDoc.querySelector('.stage').classList.contains('motion-paused')")
    js("for(let i=0;i<100;i++)reviewDoc.querySelector('.throw-button').click()")
    settle()
    scene('charge')
    assert js("reviewDoc.querySelector('.finale-layer').classList.contains('reduced-finale')")
    assert js("reviewDoc.querySelector('.finale-coach').getAnimations().length") == 0
    check_layout('finale-mobile-charge')
    scene('orbit')
    check_layout('finale-mobile-earth')
    scene('game_over')
    check_layout('finale-mobile-over')
    reset()
    assert js("document.querySelector('iframe').contentDocument.reviewToken") == 123
    # Check for stale timeline callbacks after restarting.
    time.sleep(.4)
    assert js("reviewDoc.querySelector('.finale-layer').hidden")
    assert js("reviewDoc.querySelector('.stage').dataset.phase") == 'idle'
    print('PASS: 3 complete cinematic rounds; 40 unique quotes; 40-cast cap under 100 clicks; exact scene sequence once per round; desktop charge/zoom/Earth/explosion; mobile reduced motion; full restart and stable component; counters removed')
