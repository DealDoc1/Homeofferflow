# PDF fallback font assets

These local, SIL Open Font License 1.1 assets supply glyphs absent from the
existing Helvetica encoding. Ordinary supported text keeps its original font
and metrics. ReportLab embeds used subsets; no runtime font download or paid
font service is required. This does not provide universal script shaping.

## Noto Sans Regular

- Source repository: https://github.com/notofonts/noto-fonts
- Pinned revision: `ffebf8c1ee449e544955a7e813c54f9b73848eac`
- Source path: `hinted/ttf/NotoSans/NotoSans-Regular.ttf`
- Unmodified asset SHA-256:
  `b85c38ecea8a7cfb39c24e395a4007474fa5a4fc864f6ee33309eb4948d232d5`
- Embedded copyright: Copyright 2015-2021 Google LLC. All Rights Reserved.
- License: `OFL-NotoSans.txt`, copied from that revision's `LICENSE`.

## HOF Unicode SC Regular

- Source repository: https://github.com/notofonts/noto-cjk
- Pinned revision: `f8d157532fbfaeda587e826d4cd5b21a49186f7c`
- Source path: `Sans/Variable/TTF/Subset/NotoSansSC-VF.ttf`
- Source SHA-256:
  `d68bafcb48a2707749396aa12bbbd833cb70401f3a9a689fd2902c7e0d295964`
- Embedded copyright: Copyright 2014-2021 Adobe (http://www.adobe.com/),
  with Reserved Font Name 'Source'.
- License: `OFL-NotoSansCJK.txt`, copied from that revision's `Sans/LICENSE`.
- Modification: static weight 400 instance, renamed HOF Unicode SC. Original
  copyright and license metadata retained. The modified font remains OFL 1.1.
- Output SHA-256:
  `0416cb4024b21fcd9059ed6d3bc1a08130b893091c3d979a69d0b1890af6dd5a`

To reproduce, place the pinned original at
`tmp/font-sources/NotoSansSC-VF.ttf`, install `fonttools==4.59.0` in a separate
build environment, and run `python scripts/qa/build_pdf_cjk_font.py` from the
repository root. Fonttools is not a production dependency. The build preserves
the source timestamp rather than introducing the build time.

The PDF function explicitly bundles this directory, including license notices;
other explicitly configured functions exclude it. That configuration is tested
locally and is not evidence of a verified deployed bundle.
