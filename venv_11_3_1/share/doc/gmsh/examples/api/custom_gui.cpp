#include <cmath>
#include <thread>
#include <set>
#include "gmsh.h"

// This example shows how to implement a custom user interface running
// computationally expensive calculations in separate threads. The threads can
// update the user interface in real-time.

// flag that will be set to interrupt a calculation
bool stop_computation = false;

// a computationally expensive routine, that will be run in its own thread
void compute(const std::string &arg)
{
  std::vector<double> iterations, progress;
  gmsh::onelab::getNumber("My App/Iterations", iterations);
  gmsh::onelab::getNumber("My App/Show progress?", progress);
  int n = iterations.size() ? static_cast<int>(iterations[0]) : 1;
  bool show = (progress.size() && progress[0]) ? true : false;
  int p = 0;
  double k = 0., last_refresh = 0.;
  for(int j = 0; j < n; j++) {
    // stop computation if requested by clicking on "Stop it!"
    if(stop_computation) break;
    k = sin(k) + cos(j / 45.);
    // show progress in real time?
    if(show && n > 1 && !(j % (n / 100))) {
      p++;
      gmsh::onelab::setString(arg, {std::to_string(p) + "%"});
      // any code in a thread other than the main thread that modifies the user
      // interface should be locked
      gmsh::fltk::lock();
      gmsh::logger::write(arg + " progress " + std::to_string(p) + "%");
      gmsh::fltk::unlock();
      // ask the main thread to process pending events and to update the user
      // interface, maximum 10 times per second
      if(gmsh::logger::getWallTime() - last_refresh > 0.1) {
        last_refresh = gmsh::logger::getWallTime();
        gmsh::fltk::awake("update");
      }
    }
  }
  gmsh::onelab::setNumber(arg + " result", {k});
  gmsh::onelab::setString("ONELAB/Action", {"done computing"});
  gmsh::fltk::awake("update");
}

bool checkForEvent(const std::string &parameters)
{
  std::vector<std::string> action;
  gmsh::onelab::getString("ONELAB/Action", action);
  if(action.empty()) {
  }
  else if(action[0] == "should compute") {
    gmsh::onelab::setString("ONELAB/Action", {""});
    gmsh::onelab::setString("ONELAB/Button", {"Stop!", "should stop"});
    // force interface update (to show the new button label)
    gmsh::fltk::update();
    // start computationally intensive calculations in their own threads
    std::vector<double> v;
    gmsh::onelab::getNumber("My App/Number of threads", v);
    int n = v.size() ? static_cast<int>(v[0]) : 1;
    for(unsigned int i = 0; i < n; i++) {
      std::thread t(compute, "My App/Thread " + std::to_string(i + 1));
      t.detach();
    }
  }
  else if(action[0] == "should stop") {
    stop_computation = true;
  }
  else if(action[0] == "done computing") {
    // should not detach threads, and join them all here
    gmsh::onelab::setString("ONELAB/Action", {""});
    gmsh::onelab::setString("ONELAB/Button", {"Do it!", "should compute"});
    gmsh::fltk::update();
    stop_computation = false;
  }
  else if(action[0] == "reset") {
    // user clicked on "Reset database"
    gmsh::onelab::setString("ONELAB/Action", {""});
    gmsh::onelab::set(parameters);
    gmsh::fltk::update();
  }
  else if(action[0] == "check") {
    // could perform action here after each change in ONELAB parameters,
    // e.g. rebuild a CAD model, update other parameters, ...
  }
  return true;
}

int main(int argc, char **argv)
{
  gmsh::initialize();

  // hide the standard Gmsh modules
  gmsh::option::setNumber("General.ShowModuleMenu", 0);

  // create some ONELAB parameters to control the number of iterations and
  // threads, the progress display and the custom ONELAB button (when pressed,
  // it will set the "ONELAB/Action" parameter to "should compute")
  std::string parameters = R"( [
    { "type":"number", "name":"My App/Iterations", "values":[1e6], "min":1e4,
      "max":1e9, "step":1e5, "attributes":{"Highlight":"AliceBlue"} },
    { "type":"number", "name":"My App/Number of threads", "values":[2],
      "choices":[1, 2, 3, 4], "attributes":{"Highlight":"AliceBlue"} },
    { "type":"number", "name":"My App/Show progress?", "values":[1],
      "choices":[0, 1] },
    { "type":"string", "name":"ONELAB/Button", "values":["Do it!", "should compute"],
      "visible":false }
  ] )";

  gmsh::onelab::set(parameters);

  // create the graphical user interface
  std::set<std::string> args(argv, argv + argc);
  if(!args.count("-nopopup")) {
    gmsh::fltk::initialize();
    // wait for events until the GUI is closed
    while(gmsh::fltk::isAvailable() && checkForEvent(parameters))
      gmsh::fltk::wait();
  }

  gmsh::finalize();

  return 0;
}
