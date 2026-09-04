# Vendored frontend assets

- three.min.js: three.js r128, UMD build, from
  https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js
  Vendored (not fetched at runtime) so the play surface has no network
  dependency. Exposes the global `THREE`. r128 is the last UMD `three.min.js`
  build cdnjs serves as a single global-exposing file; newer three.js
  releases ship as ES modules and no longer publish a single-file UMD
  `three.min.js` on cdnjs. OrbitControls is not vendored - app.js implements
  drag-to-rotate manually instead of using a second file.
