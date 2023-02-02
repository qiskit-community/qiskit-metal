General.Trackball = 0; // use Euler angles
General.RotationX = 30;
General.RotationY = 10;
General.RotationZ = -15;

// One can use View.XXX instead of View[YYY].XXX to define general
// View options!

View.ShowElement = 1;
View.ColorTable = {Red,Green,Blue};

// Load the views one by one to save memory

For i In {1:4}

  Merge Sprintf("../../tutorials/view%g.pos",i);
  Draw;
  //Print Sprintf("out%g.png",i);
  Delete View[0];

EndFor
