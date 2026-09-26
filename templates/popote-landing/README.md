# Popote Ulipo landing page

Open index.html to preview. Keep styles.css, script.js and the assets folder alongside it. No build tools, CDN scripts or API keys are required for the front end.

## Connect image generation

Serve these files from your backend. The form sends a multipart POST to `/generate` with one field named `image`. Change `data-endpoint` in index.html to change this URL. Keep Gemini credentials and moderation on the server.

Success JSON:
```json
{"success": true, "original_url": "/uploads/original.jpg", "generated_url": "/outputs/poster.png"}
```
The original preview uses the locally selected photo; original_url is optional. Both absolute HTTP(S) and relative generated_url values are supported. Use a same-origin result URL for reliable browser downloads; external URLs may open instead of downloading unless the server supplies Content-Disposition: attachment.

Failure JSON (with an appropriate 4xx/5xx status):
```json
{"success": false, "error": "Please choose another photo."}
```

This package is front-end only. Opening it locally or using a static server does not generate images. The original Python image-generation scripts are not a web endpoint and are not included in this package. Enforce content moderation, upload limits and image validation on the backend too. The request times out after three minutes.

## Design and assets

- Green-led cinematic layout, responsive styling, keyboard focus, reduced-motion support, local preview, file validation, consent checkbox, error/loading/results states.
- `assets/campaign.jpg`: supplied campaign artwork, preserved unchanged, including Safaricom logo.
- `assets/portrait.jpg`: illustrative stock portrait from https://images.unsplash.com/photo-1531123897727-8f129e1688ce (downloaded at width 1800). It is not a campaign participant or an example generated result. This is not a 4K source image.
- Green #43b02a is a working design token, not a certified brand specification. An official brand manual and standalone logo were not provided; confirm typography, colour and logo usage against approved assets before publication.
- The header's “25 / POPOTE ULIPO” is live text, not a recreation of the official Safaricom logo. The supplied official artwork appears in the upload section.
- Replace the concept footer and add approved campaign privacy and retention information before a public launch.
