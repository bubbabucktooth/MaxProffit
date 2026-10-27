"""Check actual word layout for every quote across desktop and mobile widths."""
import json
from pathlib import Path
import time


def run(cdp, evaluate, check_layout, root):
    quotes = json.loads((Path(__file__).resolve().parents[1] / 'quotes.json').read_text(encoding='utf-8'))
    source = {quote['id']: quote['text'] for quote in quotes}
    seen = set()
    failures = []
    deadline = time.monotonic() + 10
    while evaluate("reviewDoc.querySelector('.throw-button').disabled"):
        if time.monotonic() > deadline:
            raise AssertionError('Game did not become ready')
        time.sleep(.025)
    for hit in range(1, 41):
        evaluate("reviewDoc.querySelector('.throw-button').click();reviewDoc.querySelectorAll('.flying-bill').forEach(b=>b.getAnimations().forEach(a=>a.finish()))")
        deadline = time.monotonic() + 5
        while evaluate("Number(reviewDoc.querySelector('#money-count').value)") != hit:
            if time.monotonic() > deadline:
                raise AssertionError(f'No impact for throw {hit}')
            time.sleep(.025)
        quote_id = evaluate("reviewDoc.querySelector('.speech-bubble').dataset.quoteId")
        rendered = evaluate("reviewDoc.querySelector('.quote-text').textContent")
        assert rendered.replace('\u2011','-') == source[quote_id]
        seen.add(quote_id)
        for width, height in [(1440,1000),(1024,768),(800,900),(701,800),(390,844),(320,740)]:
            cdp('Emulation.setDeviceMetricsOverride', {'width':width,'height':height,'deviceScaleFactor':1,'mobile':width<700})
            results = evaluate(r"""(() => {
              const stage=reviewDoc.querySelector('.stage'), bubble=reviewDoc.querySelector('.speech-bubble');
              const text=bubble.querySelector('.quote-text');
              stage.classList.add('motion-paused');
              bubble.hidden=false;
              const failures=[];
              if(bubble.scrollWidth> bubble.clientWidth+1) failures.push({reason:'horizontal overflow'});
              for(const match of text.textContent.matchAll(/\S+/g)) {
                const range=reviewDoc.createRange();range.setStart(text.firstChild,match.index);range.setEnd(text.firstChild,match.index+match[0].length);
                if(range.getClientRects().length>1) failures.push({word:match[0],reason:'word split across lines'});
              }
              return failures;
            })()""")
            failures.extend([{'width':width,'id':quote_id,**item} for item in results])
            if quote_id == 'hustler-07' and width in (1440,701,390):
                check_layout(f'quotes-{width}')
    assert len(seen) == 40
    assert not failures, failures
    print('PASS: all 40 quotes at 6 viewport widths (240 layouts), no split words or horizontal bubble overflow')
