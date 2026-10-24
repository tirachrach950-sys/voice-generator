# Sell Voxwright on Gumroad

## 1. Create the product (about 10 minutes)
1. Log in at gumroad.com, then Products, then New product.
2. Choose **Membership**.
3. Fill in:
   - **Name:** Voxwright Pro: unlimited audio bot voices
   - **Price:** $3.99 per **month**. Then in the pricing options also turn on **yearly** at **$39.99** (about 16% off). The Yearly button on your site opens that option.
   - **URL slug:** voxwright
   - **Description:** paste the text below.
4. Open the **Content** tab and turn on **Generate a unique license key per sale**.
5. In the "Customize the buyer's experience" receipt message, paste:
   "Thank you! Open https://YOUR-SITE-ADDRESS, press Subscribe, then enter the license key shown on this receipt in the License key box."
6. Publish the product and copy its link (for example https://yourname.gumroad.com/l/voxwright).

### Product description (paste into Gumroad)
Turn any text into a natural spoken audio bot, in minutes.

Voxwright Pro gives you:
- Unlimited listening, MP3 audio downloads and unlimited script length
- Neural voices in English, French, Spanish, Arabic and more
- Male and female voices with accent choice
- Embed code to add your bot to any website
- Cancel anytime

Try two listens or downloads free before you subscribe. Monthly $3.99 or yearly $39.99.

## 2. Find your Product ID
Expand the **License key** section on the product's Content page. The Product ID is shown there.

## 3. Run the server with payments on
Windows (cmd), in this folder:
    set GUMROAD_PRODUCT_ID=PASTE_PRODUCT_ID_HERE
    set GUMROAD_URL=https://yourname.gumroad.com/l/voxwright
    python server.py

Mac/Linux:
    GUMROAD_PRODUCT_ID=... GUMROAD_URL=... python3 server.py

With the Product ID set, each visitor gets two free listens (300 characters each). After that, a valid
Gumroad license key is required. Refunded, charged-back, ended or failed memberships stop working
within an hour.

## 4. Test without paying
Start the server with `set DEV_LICENSE=mytestkey`, then enter `mytestkey` in the License key box.

## Fees to expect
Gumroad takes 10% + $0.50 per sale, plus card processing of about 2.9% + $0.30. On $3.99 that leaves
roughly $2.70 before your voice costs. Check gumroad.com/pricing for current rates.

## Known limits
- The free-listen counter on the server is per IP address and resets when the server restarts.
- The embed code contains the customer's license key, so anyone who views the page source could copy it.
  Signed embed tokens would fix this; ask for them before you sell embeds widely.
- The voices come from an unofficial connection to Microsoft's service. Before charging customers,
  move to the official Azure Speech service.
