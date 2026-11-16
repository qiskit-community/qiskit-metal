/* Home page hero: tilt the cards a few degrees as the page scrolls.
   Sets --qm-p on .qm-stage: 0 when the stage enters the window at the bottom,
   1 when it leaves at the top. CSS turns that into a tilt and a small parallax,
   on phones too. Nothing runs for reduced motion, and the work is skipped while
   the stage is off screen. */
(function () {
  var stage = document.querySelector(".qm-stage");
  if (!stage || !window.matchMedia) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  function update() {
    var r = stage.getBoundingClientRect();
    var h = window.innerHeight;
    if (r.bottom < 0 || r.top > h) return;
    var p = 1 - (r.top + r.height) / (h + r.height);
    stage.style.setProperty("--qm-p", Math.max(0, Math.min(1, p)).toFixed(3));
  }

  // A scroll event fires about once per frame, and one measurement plus one
  // custom property per event is cheap, so there is no extra throttling.
  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update, { passive: true });
  update();
})();
