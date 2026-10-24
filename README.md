# Voxwright with neural voices

1. Install Python 3.9 or newer.
2. In this folder run:
   pip install -r requirements.txt
   python server.py
3. Open http://localhost:8000 in any browser.

Choose Voice engine = Neural, then pick an accent and a male or female voice.
Without settings the server runs in open mode (no payment check), which is good for testing.

To sell with Gumroad, read GUMROAD_SETUP.md.

## Notes (fixed version)
- Subscribe button: it opens your Gumroad link. Set it in one of two ways:
  1. Start the server with GUMROAD_URL=https://yourname.gumroad.com/l/voxwright (see GUMROAD_SETUP.md), or
  2. Open index.html, find `var GUMROAD_URL="";` and paste your link between the quotes.
- With no GUMROAD_PRODUCT_ID the server runs in test mode: no paywall, unlimited listens.
- Neural voices need server.py running. If you only upload index.html to a static host, the page falls back to browser voices.
