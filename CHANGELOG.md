# Changelog

## [0.5.0](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/compare/v0.4.0...v0.5.0) (2026-09-04)


### ⚠ BREAKING CHANGES

* list_examples/load_example serve the tracked cookbook alongside bundled examples

### Features

* add mm_mcp.cookbook lookup for the tracked cookbook/ tree ([ee60045](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/ee60045784d9ce17caf720928797efaafe8c94f4))
* **config:** add cookbook_dir (MM_COOKBOOK_DIR, defaults to the checkout's cookbook/) ([5a0b42b](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/5a0b42bb7cbb237aa9feb66076225010e0dfb249))
* **cookbook:** +4 natural terrain materials (t05-t08) via topology-not-donor ([6ed5773](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/6ed57732ab46cb226ce4de0bce79eb2940265a6c))
* **cookbook:** +5 masonry materials, fix render.py pipe-EOF hang ([4c14f8f](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/4c14f8f266d51f1cadf8d7222c8ed18c741d1363))
* **cookbook:** +5 painted-metal materials (pm01-pm05) ([4d72c8b](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/4d72c8b3534169b66fea98d750c8037a6427e4c2))
* **cookbook:** +f07 herringbone tweed; close wool-knit as unreachable ([8ca2c2b](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/8ca2c2b4d955031b52e2a9a3107ea88016562681))
* **cookbook:** promote the 43 authored graphs into a tracked cookbook/ tree ([6c3083c](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/6c3083cb0dab10a9e8b0e1f8117e50aa1a613915))
* **debug-swatches:** +2 blend port/opacity diagnostic swatches ([80256d0](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/80256d09a3a02c70acbf4250cc68e4f5aa407c31))
* **doctor:** report the cookbook directory and material count ([56f1e23](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/56f1e23936669dcc8b7526c0e5d1399a170c6983))
* list_examples/load_example serve the tracked cookbook alongside bundled examples ([68a7d67](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/68a7d6767ba5c3692236ed3a39fe6a1cd06139db))


### Bug Fixes

* **cookbook:** address final review findings on cookbook-as-data ([f31d753](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/f31d7538380a76b147f91b66746805e5a61225c0))
* **cookbook:** resolve sf03 circuit-board trace-bleed-through ([6667b4b](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/6667b4b1eee797103760be8a6167cfe805f438ed))
* **doctor:** guard the cookbook check so an unreadable dir is reported, never raised ([251fb4a](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/251fb4aae88e50b4d656bac89d9f453ebde6c539))
* **gitignore:** restore the quality/cookbook/ ignore rule dropped in the promote commit ([55132eb](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/55132eb4074dca0af21755cdd57be1e8a85ed5ce))


### Documentation

* add cookbook-as-data design spec + phased plan ([a91f129](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/a91f1299a4f08eaed87c6e733ea79f9b497c5abf))
* **cookbook:** README/AUTHORING describe the tracked cookbook; contact sheet at 43 ([9384266](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/9384266288cfd954ca66071f06093b4e9f6fd100))
* **noise:** noise-vocabulary gallery + close list_node_types/render_preview backlog ([20e485d](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/20e485d1677e41f9f4be5d6ad50cbb19a6b1e7ba))
* wrap up blend-opacity debug-swatch session (HANDOFF/STATUS baton) ([198e2ad](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/198e2ad17fced7f801c6284b6510cbc83e8f2a18))
* wrap up masonry + sf03 session (HANDOFF/STATUS baton) ([a849784](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/a849784d8c65606154858a1c82aee716b3e2dd21))
* wrap up noise-vocab + backlog batch session (HANDOFF/STATUS baton) ([e7bb420](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/e7bb4209806b60f3e8afb732b3ce79e88ec42a10))
* wrap up painted-metal cookbook session (HANDOFF/STATUS baton) ([c0b96d7](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/c0b96d7369715332e7b573c40e4629bc5fec44fa))
* wrap up teardown [#2](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/issues/2) + cookbook-as-data session (HANDOFF/STATUS baton, STATUS header capped) ([66661f5](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/66661f53c3c6a4c5101ed83bb87b07ead7e48a4f))
* wrap up v0.4.0 release session (HANDOFF/STATUS + archive trim) ([d946942](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/d9469426fd8430ad744330bc0623aba6c577202c))
* wrap up wool-knit-closed + herringbone + terrain session (HANDOFF/STATUS baton) ([4136c9e](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/4136c9edee25fc84c73480c6f4a4ac770947d197))

## [0.4.0](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/compare/v0.3.0...v0.4.0) (2026-08-30)


### Features

* add inspect_project batch tool ([9a54953](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/9a549534c5c428bea2f2e95f6ff4d95955ea7a31))
* add inspect_ptex pure metrics helper ([2453208](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/2453208abfd8e5fbf528b41f92755e51574a4046))
* add MM_ALLOWED_ROOTS config field (allowed_roots) ([f71cbde](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/f71cbde0cdc69851742da25c6260c66b19695e5c))
* add path guards (ensure_within_roots, reject_path_fragment) ([6e6bb65](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/6e6bb65aa57671f9a51aafdf826fccaace6bc462))
* bound client-facing tool paths (save_graph dict return, traversal guards) ([945d6d6](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/945d6d6d12df4d321074d55ff173b814c9617a9c))
* **config:** add live_overlay_dir ([846f310](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/846f310c7e0ff798c609a7ee2e17cf6f79117635))
* **cookbook:** add l06 topstitched leather (real raised stitch dashes) ([f55359a](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/f55359a7e52a5bda20096869e8188b0ac506cbcd))
* **cookbook:** add leather category (4 materials) + AUTHORING recipes ([5f1a27b](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/5f1a27b28652ea4e848939c7597f1a82c21b9e11))
* **cookbook:** fix l04 reptile albedo polarity + add l05 quilted leather ([6915fc8](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/6915fc862ce7095a64df2239e566a79c152b9402))
* extend authoring cookbook with 4 fabric materials ([a714faf](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/a714faf8db80b49f8f0408c99a7da785bc14760d))
* extend authoring cookbook with 4 organic materials ([bec23b5](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/bec23b5f83e28ebe6b51a8dc3d86253b42b935b3))
* extend authoring cookbook with 4 sci-fi panel materials ([61c83bd](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/61c83bd3107deb76f4698f6d8a04d310c553da2a))
* extend authoring cookbook with 4 terrain materials ([afb3290](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/afb3290994f65c92f47e57ba18c550dab743377b))
* **live:** add async add_node command to the live-control addon ([3711fea](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/3711fea5860fa426469aee946859b1649038e377))
* **live:** add connect_nodes and set_param commands to the live-control addon ([1c8bd92](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/1c8bd92ff8c99313e3d404f3db45efff584e552e))
* **live:** add connect_or_launch (attach-or-launch, poll for ready) ([b1242b5](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/b1242b5e803c1ca44b7320ba1fa2acae7a19e9f2))
* **live:** add low-level ping/get_graph protocol client ([9ff21ec](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/9ff21ec58b91f225a25b8dc595f66d1e5061c080))
* **live:** add render command to the live-control addon ([ce6961a](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/ce6961a71bcf47d4e8cd6395050e08f9fd24a79a))
* **live:** add render to the live.py client, reusing render.py's freshness check ([efd6334](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/efd6334bd699160763d51ca6ee6c1b3cea01c125))
* **live:** add reposition_node op; rule out live rename as unsupported (backlog item I) ([352317a](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/352317a9c4ff5212559fae66d3650c7643e8c64e))
* **live:** add socket server addon skeleton (ping/get_graph) ([33dad4e](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/33dad4e1677bd01c18f19ba091405df39fbef34e))
* **live:** add validated add_node/connect_nodes/set_param to the live.py client ([b0032da](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/b0032da451c4f3fd4a47f473980493edbd6a9341))
* **live:** report whether a graph tab exists from ping ([ba9f620](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/ba9f62073766d835458d770f379bf39794c04463))
* **live:** verify Phase 5 hands-on, add live_clear reset tool ([b414763](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/b41476394ffd2a553d5f38ed1067336032ca718e))
* **overlay:** add idempotent autoload-line injection ([82644fa](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/82644fa7b36332281a1bbc161e9b793b8e5c94f0))
* **overlay:** add stable directory content hash ([ecabb38](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/ecabb389a4973a23a6c54c915e2c80b29308a56a))
* **overlay:** add staleness marker read/write/compare ([a7a3b15](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/a7a3b1566a34d5e8727ccf4512b5ebafaf4acd89))
* **overlay:** ensure_overlay first-build path ([93858ba](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/93858ba3e1ee5fa849417d6e6ec41751fc43b658))
* **preview:** add render_preview MCP tool for lit sphere/cube material preview ([41bd60b](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/41bd60bab978c2ad2102aecdc6656fd1f1917dde))
* **preview:** overhaul preview scene composition, wire tile knob through ([aefd7af](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/aefd7af0ffb1ea47729c5ed87e0bb799c409a7f1))
* **quality:** add phase-1 debug diagnostic swatch gallery ([a0d7674](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/a0d76748d1149a2de0d033aa6e023c08926ffcb3))
* **quality:** add phase-2 automated regression checks for debug swatches ([ba3d968](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/ba3d96814b6e05d13f29b1c70a2477f6e73e4f1c))
* **quality:** expand relief swatch into a shapes+text relief family ([ab688e6](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/ab688e6f207074362b223dce1a6ee77b97604fba))
* render_node_output + live_render_node_output (backlog item H) ([f891fbb](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/f891fbb6451dd67226c4ba48e094e68837de7181))
* report MM_ALLOWED_ROOTS in --check and document it ([a44c649](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/a44c649288240135fdbdb67430c83bec49b8848e))
* **server:** add live_apply MCP tool ([0862265](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/0862265d1cbe883fcb37880fea4c4ab3eb0a56c6))
* **server:** add live_get_graph MCP tool ([a82e764](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/a82e7649a618c6324b1e37578f9c7f1f287f9692))
* **server:** add live_render MCP tool ([8ed1c9b](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/8ed1c9ba2e6aca6d9a926f694e4d1e518fd9b459))
* **server:** add live_start MCP tool ([235b6b8](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/235b6b81b347d85619df6584fe611114a8601174))


### Bug Fixes

* final-review fix wave for Phase 5 step 4 ([502eb4d](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/502eb4d96a062a22bf30754cbdbd73248087257f))
* **live:** check restore success in live_render_node_output, catch AttributeError in live_apply ([12a4be3](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/12a4be30c065ff8b13a75dde5627f7d116845278))
* **live:** fail fast when an attached instance never reports has_graph ([4f4240a](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/4f4240ae3930c33448d9f354d5b01d8a7d2ffd07))
* **live:** harden connect_or_launch against a squatted/dying port ([6a0ee8b](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/6a0ee8b6b42a904f59b66d95cb004f6ca0e59d30))
* **live:** render via material_node.export_material directly, not the un-awaited main_window wrapper ([17a98d3](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/17a98d3c19449a83c04ec810ef7dde86df5ea88e))
* **live:** require a graph tab before connect_or_launch reports ready ([0df1992](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/0df1992260874b7bdaa9afa75f0a0c33f8f5fc59))
* **live:** set_param rejects unknown parameter names before sending ([7037f46](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/7037f4629564f10b3727cc5fbfb19dccc7646e1e))
* **live:** terminate launched process on unexpected exception in connect_or_launch ([5614ea0](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/5614ea04fd241b99781b79cf209bc8d47dabf47c))
* **live:** terminate the GUI child process, not just the launcher ([f97a2ac](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/f97a2accddf5a64ec68b2e494869b00ada88335d))
* **live:** use := for from_name/to_name so GDScript can infer from_node_name's type ([0bc5f92](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/0bc5f92c012e783939052c645fb3bec598248958))
* **overlay:** clear read-only attrs before rmtree on rebuild ([09455c8](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/09455c8a645fc2b97a28ade4272ab33502bebc3a))
* **overlay:** correct autoload insertion to respect section boundaries ([040c5bd](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/040c5bdf37167769867fc1aa1c423cebbed9868a))
* **overlay:** guard against non-dict JSON in marker file ([7e88a10](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/7e88a10fb65c98c9e17144ce8f5bc3dd1725a368))
* **overlay:** guard destructive fs ops, polish for final review ([67a028a](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/67a028a80edb8aebd6fe72559ff44fbcedead9f7))
* **phase5-review:** ignore live overlay dir, detect dead launch process, harden integration gate ([25675d3](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/25675d3f96d4d922f115490f3b75948380af64e3))
* **preview:** remove horizon seam by extending the ground plane ([9e52340](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/9e52340b3651807c8aa36382e883cd605b2ea69b))
* **render:** kill the whole Godot process tree on render timeout ([cd1fcb9](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/cd1fcb9a8469d9fe5fe6737a2a7c9be775efe3e6))
* **render:** use --target instead of -t for Material Maker's export CLI ([82a57f0](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/82a57f0fe3632e3f2c6809256f30ea56430f11eb))
* resolve 6 of the 8 remaining code-review findings; document 2 as deliberate non-changes ([c65cc83](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/c65cc83d6cf5311b1954cc142e949cb5d76a26d1))


### Documentation

* add 3D-preview hero + gallery and cookbook contact sheet to README ([d7f2659](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/d7f2659ea39f89c100a4f5f49241913a4f0ecf4d))
* add connect_or_launch readiness-race plan ([1d3908f](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/1d3908ffd022843a740cd50ebd808135f6cecf5b))
* add Live mode section, fix stale tool count ([52d5a6e](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/52d5a6ee6f3a45eb7515d447c69d180eae4a800a))
* add North Star doc for the round-trip learning mission ([8fc8e33](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/8fc8e33b7fa2329f89f300887d7362bae9523a90))
* add Phase 4 hardening implementation plan + correct spec CI section ([e149709](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/e149709ae8b92b8456a9d48e54034173d3765888))
* add Phase 5 addon-skeleton implementation plan ([d8cda95](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/d8cda95f93fef09165657eb32371799cf434b481))
* add Phase 5 mutating-commands implementation plan ([af25848](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/af258485f318ff00e337e1c6af8836f0d69f2398))
* add Phase 5 overlay-builder implementation plan ([53527bf](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/53527bf9ba615e5a2b5d8f8626ba6a7c5f435463))
* add Phase 5 step 4 (MCP tool surface) plan ([e48b40d](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/e48b40df56b9077a323df4d57880de8bc013f773))
* adopt a HANDOFF.md trim/archive convention (backlog item L) ([cb47010](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/cb47010ec109d945d03f0a517f846c5ee8e57c53))
* amend the live-control spec's readiness constraint ([84948ae](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/84948ae6adfff772d86dd8ac2023e9d7127e0f7a))
* correct package docstring tool count and use release extra in CI ([bfd23df](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/bfd23df37739b939afeada3c7cba6e1c3c10f85b))
* correct render-handler citation in the mutating-commands plan ([356665a](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/356665a43fb26cc6f71f7df4b240278b0e957633))
* enlarge README gallery (2-col, drop title captions) ([8f7f515](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/8f7f515f7e90c6fc3bf04f27f08cdcd16e49fba7))
* fix social-preview title crop + swap in hand-finished brick tile ([738e10b](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/738e10bb449866044902b06be607b6b2f2920b5c))
* fix stale/false claims found in today's teardown ([1fb0d45](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/1fb0d45fdde558ecca7e78052538ed7113400ba2))
* mark session commits pushed in HANDOFF (baton accuracy) ([969d420](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/969d420740efa8f1fa005140b9c67269955fc778))
* record Phase 4 hardening in STATUS ledger ([ae6ab37](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/ae6ab370cbca939d9f5c71012e6e321111039cfa))
* record Phase 5 build step 3 as wired/verified in STATUS.md ([071dbb6](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/071dbb6895bff73f09f6674798b0982cad721384))
* record the GUI-child-process-leak fix and a newly-found readiness race ([f2a0570](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/f2a057017272ce66bba8ad1a75c8c8fd2cf20e57))
* retire Phase 5 feasibility risks via spike ([128fa31](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/128fa31c6900bcf2573c1e56a48f91b03892ba5a))
* spec Phase 4 hardening (path bounding, inspect_project, CI + release-please) ([8b2ba78](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/8b2ba786f228701e10729a8f20714f98d68a3028))
* spec Phase 5 live-control addon design ([311e502](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/311e502afca1230ed811abf8e83303474e3f34d3))
* wrap up bugfix/trim/reposition session ([1368115](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/136811501a0c950dddb47a84e0a7bff784e67c53))
* wrap up cleanup session (code-review findings resolved + teardown dedup) ([c5b0cfb](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/c5b0cfbc4d046e20695f02acdc065182fe4afede))
* wrap up debug-swatch-gallery session (HANDOFF + archive trim) ([e6eb4c0](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/e6eb4c037c654da4ae63d4943fb25175582cfa48))
* wrap up leather cookbook session (HANDOFF + archive trim) ([c9934a7](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/c9934a76dd5c1e4fd204d3f107d166af3c46c225))
* wrap up MCP-wiring blocker session, gitignore .mcp.json ([acd38c5](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/acd38c5d6193100c1f0bc8fe0ab8408d5e190cac))
* wrap up Phase 4 hardening session (HANDOFF + archive trim) ([6b2a070](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/6b2a0704f5e20e173a9bffb0641778db2662231d))
* wrap up Phase 5 hands-on verification + live_clear session ([e97e78e](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/e97e78e105c5156e22879e7cae146d9ac56fd4a0))
* wrap up pre-release audit + teardown + doc-accuracy fixes session ([d0df55b](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/d0df55ba483e67e29508b6a02ab259e49dd05de5))
* wrap up README front-page-images session (HANDOFF + archive trim) ([98cdd5a](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/98cdd5a2ecc7674144f53a26efdf558487d03b24))
* wrap up render_node_output + live_render_node_output session ([25bd25c](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/25bd25c6e0fa3fc60a55a91faa8b7aabbc9e2cfa))
* wrap up Unity export proof + render.py --target fix session ([c07cabf](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/c07cabf1f641d50145d5dae696f0898c6a1c0d40))
* wrap-up handoff + status for v0.2.0 packaging and v0.3.0 doctor ([9c382bd](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/9c382bdce8cf4ec256dddb63f0b208e15071b30e))
* wrap-up handoff for cookbook growth session ([26d069c](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/26d069cee277f1db9c9316c350f570130e195aa9))
* wrap-up handoff for horizon seam fix ([278eea2](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/278eea2ef4f026b601539d2fd1252e1b2ae21e78))
* wrap-up handoff for Phase 5 build step 1 (overlay.py) ([2de70b0](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/2de70b0d4bab2d10e117221e37e12731d010512e))
* wrap-up handoff for Phase 5 build step 2 (addon skeleton) ([855fdcc](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/855fdccb88b8889796f4c0778052a3be1cbb7740))
* wrap-up handoff for Phase 5 build step 3 (mutating commands) ([49b4845](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/49b4845ad9d0370f70f13bf5508c17e71db851cc))
* wrap-up handoff for Phase 5 build step 4 (MCP tool surface) ([89e2d18](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/89e2d18d4841490dc0543163b8945b801e3d2b78))
* wrap-up handoff for Phase 5 design + MVP verification session ([524b9a2](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/524b9a2917b1295ae7bda4ed6f936739dbcb2af2))
* wrap-up handoff for render_preview + North Star session ([0675ca1](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/0675ca1c0ca90c0db309acf796ff69bb7e87c130))
* wrap-up handoff for the connect_or_launch readiness-race fix ([0c105c2](https://github.com/graysonchalmers/Tool-MaterialMaker-MCP/commit/0c105c2427a141eb288595822264c73c7733dd07))
