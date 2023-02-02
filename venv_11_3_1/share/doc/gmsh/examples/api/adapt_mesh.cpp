#include <gmsh.h>
#include <cmath>
#include <map>
#include <set>
#include <complex>

class myVertex {
private:
  int _tag;
  double _x, _y, _z;

public:
  myVertex(int tag, double x, double y, double z)
    : _tag(tag), _x(x), _y(y), _z(z)
  {
  }
  int tag() const { return _tag; }
  double x() const { return _x; }
  double y() const { return _y; }
  double z() const { return _z; }
  double distance(const myVertex &other) const
  {
    return sqrt(std::pow(x() - other.x(), 2) + std::pow(y() - other.y(), 2) +
                std::pow(z() - other.z(), 2));
  }
};

class myElement {
private:
  int _tag;
  std::vector<myVertex *> _nodes;
  std::vector<double> _qu, _qv, _qw, _qweight, _qx, _qy, _qz, _qdet, _qjac;

public:
  myElement(int tag, const std::vector<myVertex *> &nodes,
            const std::vector<double> &qu, const std::vector<double> &qv,
            const std::vector<double> &qw, const std::vector<double> &qweight,
            const std::vector<double> &qx, const std::vector<double> &qy,
            const std::vector<double> &qz, const std::vector<double> &qdet,
            const std::vector<double> &qjac)
    : _tag(tag), _nodes(nodes), _qu(qu), _qv(qv), _qw(qw), _qweight(qweight),
      _qx(qx), _qy(qy), _qz(qz), _qdet(qdet), _qjac(qjac)
  {
  }
  int tag() const { return _tag; }
  const std::vector<myVertex *> &nodes() const { return _nodes; }
  const std::vector<double> &qu() const { return _qu; }
  const std::vector<double> &qv() const { return _qv; }
  const std::vector<double> &qw() const { return _qw; }
  const std::vector<double> &qweight() const { return _qweight; }
  const std::vector<double> &qx() const { return _qx; }
  const std::vector<double> &qy() const { return _qy; }
  const std::vector<double> &qz() const { return _qz; }
  const std::vector<double> &qdet() const { return _qdet; }
  const std::vector<double> &qjac() const { return _qjac; }
  double maxEdge() const
  {
    if(_nodes.size() == 3) {
      double a = _nodes[0]->distance(*_nodes[1]);
      double b = _nodes[0]->distance(*_nodes[2]);
      double c = _nodes[1]->distance(*_nodes[2]);
      return std::max(a, std::max(b, c));
    }
    else {
      std::printf("maxEdge only implemented for 3-node triangles");
      exit(1);
    }
  }
};

class myMesh {
private:
  std::map<std::size_t, myVertex *> _nodes;
  std::map<std::size_t, myElement *> _elements;

public:
  myMesh()
  {
    std::vector<std::size_t> vtags;
    std::vector<double> vxyz, vuvw;
    gmsh::model::mesh::getNodes(vtags, vxyz, vuvw);
    std::vector<int> etypes;
    std::vector<std::vector<std::size_t> > etags, evtags;
    gmsh::model::mesh::getElements(etypes, etags, evtags);
    for(unsigned int i = 0; i < vtags.size(); i++) {
      _nodes[vtags[i]] =
        new myVertex(vtags[i], vxyz[3 * i], vxyz[3 * i + 1], vxyz[3 * i + 2]);
    }
    for(unsigned int i = 0; i < etypes.size(); i++) {
      std::vector<double> quvw, qweight;
      gmsh::model::mesh::getIntegrationPoints(etypes[i], "Gauss2", quvw,
                                              qweight);
      std::vector<double> qdeter, qjacob, qpoints;
      gmsh::model::mesh::getJacobians(etypes[i], quvw, qjacob, qdeter, qpoints);
      int nev = evtags[i].size() / etags[i].size();
      int nq = quvw.size() / 3;
      std::vector<double> qu, qv, qw;
      for(unsigned int j = 0; j < quvw.size(); j += 3) {
        qu.push_back(quvw[j]);
        qv.push_back(quvw[j + 1]);
        qw.push_back(quvw[j + 2]);
      }
      for(unsigned int j = 0; j < etags[i].size(); j++) {
        std::vector<myVertex *> ev;
        for(unsigned int k = nev * j; k < nev * (j + 1); k++)
          ev.push_back(_nodes[evtags[i][k]]);
        std::vector<double> qx, qy, qz, qdet, qjac;
        for(unsigned int k = 3 * nq * j; k < 3 * nq * (j + 1); k += 3) {
          qx.push_back(qpoints[k]);
          qy.push_back(qpoints[k + 1]);
          qz.push_back(qpoints[k + 2]);
        }
        for(unsigned int k = 1 * nq * j; k < 1 * nq * (j + 1); k += 1) {
          qdet.push_back(qdeter[k]);
        }
        for(unsigned int k = 9 * nq * j; k < 9 * nq * (j + 1); k += 9) {
          for(int m = 0; m < 9; m++) qjac.push_back(qjacob[k + m]);
        }
        _elements[etags[i][j]] = new myElement(etags[i][j], ev, qu, qv, qw,
                                               qweight, qx, qy, qz, qdet, qjac);
      }
    }
  }
  const std::map<std::size_t, myVertex *> &nodes() const { return _nodes; }
  const std::map<std::size_t, myElement *> &elements() const
  {
    return _elements;
  }
};

class myFunction {
public:
  double operator()(double x, double y, double z) const
  {
    std::complex<double> a =
      6 * (std::sqrt(std::pow(x - .5, 2) + std::pow(y - .5, 2)) - .2);
    return atanh(a).real();
    // return (x*y)*(x*y);
  }
};

void computeInterpolationError(const myMesh &mesh, const myFunction &f,
                               std::map<std::size_t, double> &f_nod,
                               std::map<std::size_t, double> &err_ele)
{
  // evaluate f at the nodes
  for(std::map<std::size_t, myVertex *>::const_iterator it =
        mesh.nodes().begin();
      it != mesh.nodes().end(); it++) {
    myVertex *v = it->second;
    f_nod[it->first] = f(v->x(), v->y(), v->z());
  }
  // compute the interpolation error on the elements
  for(std::map<std::size_t, myElement *>::const_iterator it =
        mesh.elements().begin();
      it != mesh.elements().end(); it++) {
    myElement *e = it->second;
    if(e->nodes().size() == 3) {
      double err = 0.;
      int t0 = e->nodes()[0]->tag();
      int t1 = e->nodes()[1]->tag();
      int t2 = e->nodes()[2]->tag();
      for(unsigned int i = 0; i < e->qweight().size(); i++) {
        double u = e->qu()[i], v = e->qv()[i], w = e->qw()[i];
        double weight = e->qweight()[i];
        double x = e->qx()[i], y = e->qy()[i], z = e->qz()[i];
        double det = std::abs(e->qdet()[i]);
        double f_fem = f_nod[t0] * (1 - u - v) + f_nod[t1] * u + f_nod[t2] * v;
        err += std::pow(f(x, y, z) - f_fem, 2) * det * weight;
      }
      err_ele[it->first] = std::sqrt(err);
    }
  }
}

void computeSizeField(const myMesh &mesh,
                      const std::map<std::size_t, double> &err_ele, int N,
                      std::map<std::size_t, double> &sf_ele)
{
  double a = 2.;
  double d = 2.;
  double fact = 0.;
  for(std::map<std::size_t, double>::const_iterator it = err_ele.begin();
      it != err_ele.end(); it++) {
    double e = it->second;
    fact += std::pow(e, 2. / (1. + a));
  }
  fact *= (std::pow(a, (2. + a) / (1. + a)) + std::pow(a, 1. / (1. + a)));
  for(std::map<std::size_t, double>::const_iterator it = err_ele.begin();
      it != err_ele.end(); it++) {
    double e = it->second;
    double ri = std::pow(e, 2. / (2. * (1 + a))) *
                std::pow(a, 1. / (d * (1. + a))) *
                std::pow((1. + a) * N / fact, 1. / d);
    std::map<std::size_t, myElement *>::const_iterator ite =
      mesh.elements().find(it->first);
    sf_ele[it->first] = ite->second->maxEdge() / ri;
  }
}

void getKeysValues(const std::map<std::size_t, double> &f,
                   std::vector<std::size_t> &keys,
                   std::vector<std::vector<double> > &values)
{
  keys.clear();
  values.clear();
  for(std::map<std::size_t, double>::const_iterator it = f.begin();
      it != f.end(); it++) {
    keys.push_back(it->first);
    values.push_back(std::vector<double>(1, it->second));
  }
}

int main(int argc, char **argv)
{
  std::printf("Usage: %s [intial lc] [target #elements] [dump files]\n",
              argv[0]);
  double lc = 0.02;
  int N = 10000;
  bool dumpfiles = false;

  std::set<std::string> args(argv, argv + argc);
  if(args.count("-nopopup")) argc--;

  if(argc > 1) lc = atof(argv[1]);
  if(argc > 2) N = atoi(argv[2]);
  if(argc > 3) dumpfiles = atoi(argv[3]);

  gmsh::initialize();

  // create a geometrical model
  gmsh::model::add("square");
  int square = gmsh::model::occ::addRectangle(0, 0, 0, 1, 1);
  gmsh::model::occ::synchronize();

  // create initial uniform mesh
  std::vector<std::pair<int, int> > pnts;
  gmsh::model::getBoundary({{2, square}}, pnts, true, true, true);
  gmsh::model::mesh::setSize(pnts, lc);
  gmsh::model::mesh::generate(2);
  if(dumpfiles) gmsh::write("mesh.msh");
  myMesh mesh;

  // compute and visualize the interpolation error
  myFunction f;
  std::map<std::size_t, double> f_nod, err_ele;
  computeInterpolationError(mesh, f, f_nod, err_ele);
  std::vector<std::size_t> keys;
  std::vector<std::vector<double> > values;
  int f_view = gmsh::view::add("nodal function");
  getKeysValues(f_nod, keys, values);
  gmsh::view::addModelData(f_view, 0, "square", "NodeData", keys, values);
  if(dumpfiles) gmsh::view::write(f_view, "f.pos");
  int err_view = gmsh::view::add("element-wise error");
  getKeysValues(err_ele, keys, values);
  gmsh::view::addModelData(err_view, 0, "square", "ElementData", keys, values);
  if(dumpfiles) gmsh::view::write(err_view, "err.pos");

  // compute and visualize the remeshing size field
  std::map<std::size_t, double> sf_ele;
  computeSizeField(mesh, err_ele, N, sf_ele);
  int sf_view = gmsh::view::add("mesh size field");
  getKeysValues(sf_ele, keys, values);
  gmsh::view::addModelData(sf_view, 0, "square", "ElementData", keys, values);
  if(dumpfiles) gmsh::view::write(sf_view, "sf.pos");

  // create a new model and mesh it using the size field (to remesh the original
  // model in-place, the size field should be created as a list-based view!)
  gmsh::model::add("square2");
  gmsh::model::occ::addRectangle(0, 0, 0, 1, 1);
  gmsh::model::occ::synchronize();

  // mesh the new model using the size field
  int bg_field = gmsh::model::mesh::field::add("PostView");
  gmsh::model::mesh::field::setNumber(bg_field, "ViewTag", sf_view);
  gmsh::model::mesh::field::setAsBackgroundMesh(bg_field);
  gmsh::model::mesh::generate(2);
  if(dumpfiles) gmsh::write("mesh2.msh");
  myMesh mesh2;

  // compute and visualize the interpolation error on the adapted mesh
  std::map<std::size_t, double> f2_nod, err2_ele;
  computeInterpolationError(mesh2, f, f2_nod, err2_ele);
  int f2_view = gmsh::view::add("nodal function on adapted mesh");
  getKeysValues(f2_nod, keys, values);
  gmsh::view::addModelData(f2_view, 0, "square2", "NodeData", keys, values);
  if(dumpfiles) gmsh::view::write(f2_view, "f2.pos");
  int err2_view = gmsh::view::add("element-wise error on adapted mesh");
  getKeysValues(err2_ele, keys, values);
  gmsh::view::addModelData(err2_view, 0, "square2", "ElementData", keys,
                           values);
  if(dumpfiles) gmsh::view::write(err2_view, "err2.pos");

  // show everything in the gui
  if(!args.count("-nopopup")) gmsh::fltk::run();

  gmsh::finalize();
  return 0;
}
