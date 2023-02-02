
View "Test" {
  ST(0,0,0, 1,0,0, 0,1,0){1,2,3};
};

PostProcessing.HorizontalScales = 0; // Display value scales horizontally
View[0].AutoPosition = 0; // Position the scale or 2D plot automatically (0: manual)
View[0].Height = 200; // Height (in pixels) of the scale or 2D plot
View[0].Width = 20; // Width (in pixels) of the scale or 2D plot
View[0].PositionX = -100; // X position (in pixels) of the scale or 2D plot (< 0: measure from right edge; >= 1e5: centered)
View[0].PositionY = 1e6; // Y position (in pixels) of the scale or 2D plot (< 0: measure from bottom edge; >= 1e5: centered)
View[0].ShowScale = 1; // Show value scale?
