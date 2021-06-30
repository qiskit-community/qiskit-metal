# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""LOM analysis based on https://arxiv.org/pdf/2103.10344.pdf
"""
# pylint: disable=invalid-name

from abc import abstractmethod, ABC
from collections import defaultdict, namedtuple
from typing import Any, List, Dict, Tuple, DefaultDict, Sequence, Mapping

import numpy as np
import pandas as pd
import scqubits as scq
from sympy import Matrix

from pyEPR.calcs.convert import Convert
from pyEPR.calcs.constants import e_el as ele

BasisTransform = namedtuple(
    'BasisTransform',
    ['orig_node_basis', 'node_jj_basis', 'num_negative_nodes'])

Operator = namedtuple('Operator', ['op', 'add_hc'])


def _product_no_duplicate(*args) -> List[List]:
    """
    product_no_duplicate('ABCDx', 'xy') --> Ax Ay Bx By Cx Cy Dx Dy xy
    ** Note that xx is not included **

    Similar to itertools.product except for results with duplicates are
    excluded

    """

    pools = [tuple(pool) for pool in args]
    result = [[]]

    for pool in pools:
        result = [x + [y] for x in result for y in pool if y not in x]

    return result


def _make_cmat_df(cmat, nodes):
    """
    generate a pandas dataframe from a capacitance matrix and list of node names
    """
    df = pd.DataFrame(cmat)
    df.columns = nodes
    df.index = nodes
    return df


def _df_cmat_to_adj_list(df_cmat: pd.DataFrame) -> DefaultDict(list):
    """
    generate an adjacency list from a capacitance matrix in a dataframe
    """
    nodes = df_cmat.columns.values
    vals = df_cmat.values
    graph = defaultdict(list)
    for ii, node in enumerate(nodes):
        for jj in range(ii, len(nodes)):
            graph[node].append((nodes[jj], vals[ii, jj]))
    return graph


def _remove_row_col_at_idx(mat, idx):
    """
    remove row and column in a matrix corresponding an index
    """
    mat_ = np.delete(mat, idx, 0)
    mat_ = np.delete(mat_, idx, 1)
    return mat_


def _extract_matrix_from_transform(transform: BasisTransform,
                                   junctions: Mapping[Tuple[str, str], str],
                                   index: pd.Index) -> np.ndarray:
    """
    calculate the S_n^{-1} matrix that corresponds to a given transform
    https://arxiv.org/pdf/2103.10344.pdf
    """
    junctions = dict(zip(junctions.values(), junctions.keys()))

    dim = len(transform.orig_node_basis)
    m = np.zeros((dim, dim))
    for ii, (n_old, n_new) in enumerate(
            zip(transform.orig_node_basis, transform.node_jj_basis)):
        if n_old == n_new:
            m[ii, ii] = 1
        else:
            n1, n2 = junctions[n_new]
            c1, c2 = index.get_indexer([n1, n2])
            m[ii, c1] = 1
            m[ii, c2] = -1
    return m


def _transform_to_junction_flux_basis(orig_nodes,
                                      junctions: Mapping[Tuple[str, str], str],
                                      choose_least_num_neg: bool = True):
    """
    junctions = {('n1', 'n2'):'j1', ('n3', 'n4'):'j2'}
    junction flux is defined such that Phi_{j1} = Phi_{1} - Phi_{2}, for {'j1': ('n1', 'n2')}, where we refer to n1 as
    the "positive" node and n2 as the "negative" node

    Param:
        choose_least_num_neg: if set true, choose the transform with least number of -1s in the transform matrix.
            this means choosing a basis which has the LARGEST number of "positive" junction nodes, i.e.,
            the LEAST number of "negative" junction nodes; if set false, return all possible transforms
    """
    junctions = dict(zip(junctions.values(), junctions.keys()))

    j_list = list(junctions.keys())

    # each junction flux can potentially replace one of two orignal nodes in the new flux basis.
    # for N junctions, an array of N nodes can represent such mapping where the ith node in the array
    # is the original node that is replaced by the ith junction; And an array of these arrays can
    # represent all possible mappings

    all_combos = _product_no_duplicate(*tuple(junctions.values()))
    all_maps = [dict(zip(x, j_list)) for x in all_combos]

    _transforms = []
    for _map in all_maps:
        new_basis = []
        num_negative_nodes = 0
        for n in orig_nodes:
            if n not in _map:
                new_basis.append(n)
            else:
                new_basis.append(_map[n])
                if junctions[_map[n]][1] == n:  # "negative" node
                    num_negative_nodes += 1

        _transforms.append(
            BasisTransform(orig_nodes, new_basis, num_negative_nodes))

    if choose_least_num_neg:
        _transforms.sort(key=lambda t: t.num_negative_nodes)
        return _transforms[0]

    return _transforms


#----------------------------------------------------------------------------------------------------


def _maybe_remove_grd_node_then_cache(f):

    def wrapper(self):
        _attr = f'_{f.__name__}'
        if getattr(self, _attr) is None:
            m = f(self)
            if self.ignore_grd_node:
                m = _remove_row_col_at_idx(m, self.grd_idx)
            setattr(self, _attr, m)
        else:
            m = getattr(self, _attr)
        return m

    return wrapper


class CircuitGraph:
    """
    class representing the lumped circuit
    """

    units = {'capacitance': 'fF', 'inductance': 'nH'}
    _IGNORE_GRD_NODE = True

    def __init__(self, nodes: Sequence, grd_node: str,
                 cmats: List[pd.DataFrame], ind_lists: List[Dict[Tuple, float]],
                 junctions: Mapping[Tuple[str, str], str]):

        self.nodes = list(nodes)
        self.idx = pd.Index(self.nodes)
        self._grd_node = grd_node
        self.ignore_grd_node = CircuitGraph._IGNORE_GRD_NODE
        self.grd_idx = self.idx.get_indexer([grd_node])[0]

        self._c_graphs = [_df_cmat_to_adj_list(m) for m in cmats]
        self._ind_lists = ind_lists
        self._junctions = junctions

        self._C_n = None
        self._L_n_inv = None

        self._S_n = None
        self._new_basis = None

    def __str__(self):
        #TODO
        pass

    def _adj_list_to_mat(self, adj_list):
        idx = self.idx
        dim = len(idx)
        mat = np.zeros((dim, dim))
        for n1 in adj_list:
            for n2, w in adj_list[n1]:
                r = idx.get_indexer([n1])[0]
                c = idx.get_indexer([n2])[0]
                mat[r, c] = w
                mat[c, r] = w
        return mat

    def _inductance_list_to_Linv_mat(self, ind_dict):
        idx = self.idx
        dim = len(idx)
        mat = np.zeros((dim, dim))
        for (n1, n2), l in ind_dict.items():
            if n1 == n2:
                raise ValueError(
                    'inductance needs to be specified between two different nodes'
                )
            idx1, idx2 = idx.get_indexer([n1, n2])
            mat[idx1, idx2] = mat[idx2, idx1] = -1 / l
        for ii in range(len(mat)):
            mat[ii, ii] = -mat[ii].sum()
        return mat

    @property
    @_maybe_remove_grd_node_then_cache
    def C_n(self):
        dim = len(self.idx)
        C_n = np.zeros((dim, dim))
        for c_g in self._c_graphs:
            C_n += self._adj_list_to_mat(c_g)
        return C_n

    @property
    @_maybe_remove_grd_node_then_cache
    def L_n_inv(self):
        dim = len(self.idx)
        L_n_inv = np.zeros((dim, dim))
        for l_dict in self._ind_lists:
            L_n_inv += self._inductance_list_to_Linv_mat(l_dict)
        return L_n_inv

    @property
    @_maybe_remove_grd_node_then_cache
    def S_n(self):
        t = _transform_to_junction_flux_basis(self.nodes,
                                              self._junctions,
                                              choose_least_num_neg=True)
        S_n_inv = _extract_matrix_from_transform(t, self._junctions, self.idx)
        S_n = np.linalg.inv(S_n_inv)
        self._new_basis = t.new_basis
        return S_n

    @property
    def C(self):
        return self.S_n.T.dot(self.C_n).dot(self.S_n)

    @property
    def L_inv(self):
        return self.S_n.T.dot(self.L_n_inv).dot(self.S_n)

    @property
    def orig_node_basis(self):
        _orig_basis = self.nodes
        if self.ignore_grd_node:
            _orig_basis = [
                _node for _node in _orig_basis if _node != self._grd_node
            ]
        return _orig_basis

    @property
    def node_jj_basis(self):
        if self._new_basis is None:
            _ = self.S_n
        _new_basis = self._new_basis
        if self.ignore_grd_node:
            _new_basis = [
                _node for _node in _new_basis if _node != self._grd_node
            ]
        return _new_basis

    @property
    def S_remove(self):
        # FIXME: take user input into account
        L_inv = self.L_inv
        _s_r = []
        null_space = Matrix(L_inv).nullspace()
        for _v in null_space:
            v = _v / _v.norm()
            v = np.array(v).astype(np.float64)
            _s_r.append(v)
            if np.count_nonzero(v) != 1:
                raise ValueError(
                    f'Nullspace column vector {v} has more than one non-zero element. \
                                 Only indivudal nodes in the current flux [see self.new_basis] basis can be removed'
                )
        return np.concatenate(_s_r, axis=1)

    @property
    def S_keep(self):
        # FIXME: currently assuming that S_keep can be solely constructed from
        # S_remove (which itself is constructed from the identity matrix) and the identity matrix
        S_remove = self.S_remove
        dim = S_remove.shape[0]
        eye = np.eye(dim)
        return eye[:, np.where(S_remove.T.sum(axis=0) == 0)[0]]

    def get_nodes_keep(self):
        s_keep = self.S_keep
        dim = s_keep.shape[0]
        keep_idx = s_keep.T.dot(np.arange(dim)[:, np.newaxis])[:, 0].astype(int)
        return np.array(self.node_jj_basis)[keep_idx].tolist()

    def get_nodes_remove(self):
        s_remove = self.S_remove
        dim = s_remove.shape[0]
        remove_idx = s_remove.T.dot(np.arange(dim)[:,
                                                   np.newaxis])[:,
                                                                0].astype(int)
        return np.array(self.node_jj_basis)[remove_idx].tolist()

    @property
    def L_inv_k(self):
        """
        https://arxiv.org/pdf/2103.10344.pdf
        equation (7a)
        """
        s_keep = self.S_keep
        l_inv = self.L_inv
        return s_keep.T.dot(l_inv).dot(s_keep)

    @property
    def C_k(self):
        """
        https://arxiv.org/pdf/2103.10344.pdf
        equation (7b)
        """
        s_k = self.S_keep
        s_r = self.S_remove
        c = self.C
        _inner = c.dot(s_r).dot(np.linalg.inv(s_r.T.dot(c.dot(s_r)))).dot(
            s_r.T.dot(c))
        return s_k.T.dot(c - _inner).dot(s_k)

    @property
    def C_inv_k(self):
        c_k = self.C_k
        if np.linalg.matrix_rank(c_k) < c_k.shape[0]:
            raise ValueError('C_k is rank deficient hence can\'t be inverted')
        return np.linalg.inv(self.C_k)


#----------------------------------------------------------------------------------------------------


def _rename_nodes_in_df(node_rename: Dict, df: pd.DataFrame) -> pd.DataFrame:
    orig_nodes = df.columns.values.tolist()
    new_nodes = [
        n if n not in node_rename else node_rename[n] for n in orig_nodes
    ]
    return _make_cmat_df(df.values, new_nodes)


def _rename_nodes_in_dict(node_rename: Dict, dict_input: Dict[Tuple[str],
                                                              Any]) -> Dict:
    renamed = {}
    for nodes, val in dict_input.items():
        _renamed_key = tuple(
            [n if n not in node_rename else node_rename[n] for n in nodes])
        renamed[_renamed_key] = val
    return renamed


def _find_subsystem_mat_index(cg: CircuitGraph, subsystem, single_node=True):
    nodes_keep = cg.get_nodes_keep()
    reduced_mat_idx = pd.Index(nodes_keep)

    ss_nodes = subsystem.nodes
    idx = reduced_mat_idx
    node_idx = idx.get_indexer(ss_nodes)
    subsystem_idx = node_idx[node_idx > 0]
    if subsystem_idx.size != 1 and single_node:
        raise ValueError(
            f'One and ONLY one node in the reduced node-junction basis should map to the {subsystem.sys_type} subsystem.'
        )
    elif subsystem_idx.size == 0:
        raise ValueError('Subsystem not found in the circuit\'s nodes.')
    return subsystem_idx


def _process_input_gs(gs):
    # TODO: to be implemented
    return gs


class QuantumSystemType:
    TRANSMON = "TRANSMON"
    RESONATOR = "RESONATOR"


class Subsystem:
    """Class representing a subsystem that can typically be mapped to a quantum system with known
    solution, such as a transmon, a fluxonium or a quantum harmonic osccilator
    """

    def __init__(self, name: str, sys_type: str, nodes: List[str],
                 q_opts: dict):
        self.name = name
        self.sys_type = sys_type
        self.nodes = nodes
        self.q_opts = q_opts
        self._quantum_system = None
        self._h_params = {}
        self.system_params = {}

    @property
    def h_params(self):
        if self._h_params == {}:
            raise ValueError(
                f'Subsystem {self.name}\'s Hamiltonian parameters have not been calcuated.'
            )
        return self._h_params

    @property
    def quantum_system(self):
        if self._quantum_system is None:
            raise ValueError(
                f'Subsystem {self.name}\'s quantum system has not been created.'
            )
        return self._quantum_system

    def quantumfy(self, quantum_builder) -> None:
        quantum_builder.make_quantum(self)


class QuantumBuilder(ABC):

    def __init__(self, cg: CircuitGraph):
        self.cg = cg
        self.nodes_keep = self.cg.get_nodes_keep()
        self.reduced_mat_idx = pd.Index(self.nodes_keep)

    @abstractmethod
    def make_quantum(self, subsystem: Subsystem):
        raise NotImplementedError


class TransmonBuilder(QuantumBuilder):

    # pylint: disable=protected-access
    def make_quantum(self, subsystem: Subsystem):
        cg = self.cg
        l_inv_k = cg.L_inv_k
        c_inv_k = cg.C_inv_k

        subsystem_idx = _find_subsystem_mat_index(cg,
                                                  subsystem,
                                                  single_node=True)
        ss_idx = subsystem_idx[0]
        subsystem.system_params['subsystem_idx'] = ss_idx

        EJ = Convert.Ej_from_Lj(1 / l_inv_k[ss_idx, ss_idx])
        EC = Convert.Ec_from_Cs(1 / c_inv_k[ss_idx, ss_idx])
        Qzpf = 2 * ele
        qubit_opts = dict(EJ=EJ, EC=EC, ng=0.001, ncut=22, truncated_dim=10)
        transmon = scq.Transmon({**qubit_opts, **subsystem.q_opts})

        subsystem._quantum_system = transmon
        subsystem._h_params = dict(EJ=EJ, EC=EC, Qzpf=Qzpf)
        subsystem._h_params['default_charge_op'] = Operator(
            transmon.n_operator(), False)


class ResonatorBuilder(QuantumBuilder):

    # pylint: disable=protected-access
    def make_quantum(self, subsystem: Subsystem):
        #TODO: Qzpf
        cg = self.cg

        subsystem_idx = _find_subsystem_mat_index(cg,
                                                  subsystem,
                                                  single_node=True)
        ss_idx = subsystem_idx[0]
        subsystem.system_params['subsystem_idx'] = ss_idx

        f_res = subsystem.qops.get('f_res')
        if f_res is None:
            raise ValueError('f_res is not defined.')
        res_opts = dict(E_osc=f_res, truncated_dim=4)
        resonator = scq.Oscillator({**res_opts, **subsystem.q_opts})

        subsystem._quantum_system = resonator
        subsystem._h_params['default_charge_op'] = Operator(
            1j *
            (resonator.creation_operator() - resonator.annihilation_operator()),
            False)


class CapCouplingBuilder(QuantumBuilder):
    pass


class Cell:
    """A physical subdivision of the device, a sub-network of capaciators, inductoros and other
    linear or non-linear circuit elements, whose values can be independently simulated/defined with
    respect to other cells.
    """

    def __init__(self, options: Dict):
        self._node_rename = options['node_rename']
        self.cap_mat = _rename_nodes_in_df(self._node_rename,
                                           options['cap_mat'])
        self.ind_dict = None
        self.jj_dict = None
        if 'ind_dict' in options:
            self.ind_dict = _rename_nodes_in_dict(self._node_rename,
                                                  options['ind_dict'])
        if 'ind_mat' in options:
            raise NotImplementedError
        if 'jj_dict' in options:
            self.jj_dict = _rename_nodes_in_dict(self._node_rename,
                                                 options['jj_dict'])

        self.nodes = self.cap_mat.columns.values.tolist()


class CompositeSystem:
    """Class representing the composite system which may consist of multiple subsystems and cells
    """

    def __init__(self, subsystems: List[Subsystem], cells: List[Cell],
                 grd_node: str):
        self._subsystems = subsystems
        self.num_subsystems = len(subsystems)
        self._cells = cells
        self.num_cells = len(cells)
        self.grd_node = grd_node

        self._nodes = list({ss.nodes for ss in self._subsystems})
        self._c_list = [ss.cap_mat for ss in self._subsystems]
        self._l_list = [ss.ind_dict for ss in self._subsystems]
        self._jj = {
            k: j for ss in self._subsystems for k, j in ss.jj_dict.items()
        }

        self._cg = None

    def circuitGraph(self) -> CircuitGraph:
        """create a CircuitGraph object with circuit parameters of the composite system

        Returns:
            CircuitGraph: [description]
        """
        if self._cg is None:
            nodes = self._nodes
            grd_node = self.grd_node
            c_list = self._c_list
            l_list = self._l_list
            jjs = self._jj
            self._cg = CircuitGraph(nodes, grd_node, c_list, l_list, jjs)

        return self._cg

    def create_hilbertspace(self) -> scq.HilbertSpace:
        """ create the composite hilbertspace including all the subsystems. Interaction NOT included

        Raises:
            NotImplementedError: [description]

        Returns:
            scq.HilbertSpace: [description]
        """
        cg = self.circuitGraph()

        quantum_systems = []
        for sub in self._subsystems:
            if sub.sys_type == QuantumSystemType.TRANSMON:
                q_builder = TransmonBuilder(cg)
            elif sub.sys_type == QuantumSystemType.RESONATOR:
                q_builder = ResonatorBuilder(cg)
            else:
                raise NotImplementedError

            sub.quantumfy(q_builder)
            quantum_systems.append(sub.quantum_system)

        return scq.HilbertSpace(quantum_systems)

    def compute_gs(self):
        raise NotImplementedError

    def add_interaction(self,
                        gs: Any = None,
                        gscale: float = 1.) -> scq.HilbertSpace:
        """ add interaction terms to the composite hilbertspace

        Args:
            gs (Any, optional): [description]. Defaults to None.

        Returns:
            scq.HilbertSpace: [description]
        """
        cg = self.circuitGraph()
        h = self.create_hilbertspace()

        if gs is None:
            gs = self.compute_gs()
        else:
            gs = _process_input_gs(gs)

        c_inv_k = cg.C_inv_k
        l_inv_k = cg.L_inv_k

        if c_inv_k.shape != gs.shape:
            raise ValueError(
                'The dimension of g matrix doesn\'t match that of the reduced capacitance matrix.'
            )

        for ii in range(self.num_subsystems):
            sub1 = self._subsystems[ii]
            idx1 = sub1.system_params['subsystem_idx']
            for jj in range(ii + 1, self.num_subsystems):
                sub2 = self._subsystems[jj]
                idx2 = sub2.system_params['subsystem_idx']
                g = gs[idx1, idx2]
                if g == 0:
                    continue
                q1 = sub1.quantum_system
                q2 = sub2.quantum_system

                if l_inv_k[idx1, idx2] != 0:
                    raise NotImplementedError(
                        'Interaction term for inductive coupling not yet implemented.'
                    )
                if c_inv_k[idx1, idx2] != 0:
                    q1_op, add_hc1 = sub1.h_params['default_charge_op']
                    q2_op, add_hc2 = sub2.h_params['default_charge_op']

                    h.add_interaction(g=g * gscale,
                                      op1=(q1_op, q1),
                                      op2=(q2_op, q2),
                                      add_hc=add_hc1 or add_hc2)
        return h
