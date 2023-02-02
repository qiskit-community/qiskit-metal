// create 500 views, in 5 groups
For i In {1:5}
  For j In {1:100}
    View Sprintf("View %g in group %g", j, i) {
      SQ(i/10,j/100,0,            i/10+1/10,j/100,0,
         i/10+1/10,j/100+1/100,0, i/10,j/100+1/100,0){1,1,1,1};
    };
    View[PostProcessing.NbViews-1].Group = Sprintf("Group %g", i);
    View[PostProcessing.NbViews-1].Closed = 1; // close the group
    View[PostProcessing.NbViews-1].DoubleClickedCommand =
      "Printf('Double-clicked View[%g]', PostProcessing.DoubleClickedView);";
    View[PostProcessing.NbViews-1].ShowScale = 0;
    View[PostProcessing.NbViews-1].ShowElement = 1;
    View[PostProcessing.NbViews-1].ColorTable = {{j/100*255,i/5*255,128}};
  EndFor
EndFor
