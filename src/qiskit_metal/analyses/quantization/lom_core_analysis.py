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

# monkey patch to temporarily mock h5py dependency required by scqubits, which conflicts with
# geopandas
import sys

from scipy.fftpack import hilbert


# pylint: disable=wrong-import-position
# pylint: disable=too-few-public-methods
class DummyH5py:

    @property
    def Group(self):
        pass


sys.modules['h5py'] = DummyH5py

from collections import defaultdict, namedtuple
from typing import Any, List, Dict, Tuple, DefaultDict, Sequence, Mapping, Union, Callable
import argparse

import numpy as np
import pandas as pd
import scqubits as scq
from sympy import Matrix
from scipy import optimize, integrate

from pyEPR.calcs.convert import Convert
from pyEPR.calcs.constants import e_el as ele, hbar

from qiskit_metal.toolbox_python.utility_functions import get_all_args
from qiskit_metal.analyses.em.cpw_calculations import guided_wavelength
from qiskit_metal.analyses.hamiltonian.states_energies import extract_energies
from qiskit_metal.analyses.quantization.constants import (MHzRad, GHzRad, NANO, FEMTO, ONE_OVER_FEMTO)

from qiskit_metal import logger

BasisTransform = namedtuple(
    'BasisTransform',
    ['orig_node_basis', 'node_jj_basis', 'num_negative_nodes'])

Operator = namedtuple('Operator', ['op', 'add_hc'])


class CouplingType:
    CAPACITIVE = 'CAPACITIVE'
    INDUCTIVE = 'INDUCTIVE'


def analyze_loaded_tl(fr, vp, Z0, cap_loading: Dict[str, float], shorted=False):
    """ Calculate charge operator zero point fluctuation, Q_zpf at the point of the loading
    capacitor.
    https://arxiv.org/pdf/2103.10344.pdf
    equation 20

    Args:
        fr (float): TL resonator frequency in MHz
        vp (float): phase velocity in m/s
        Z0 (float): characteristic impedance of the TL in ohm
        cap_loading (dict): a dictionary of the loading capacitors; the keys
            are the names of the nodes; the values the capacitances in fF
        shorted (boolean): default false; true if the other end of the TL is shorted false otherwise

    Returns:
        [type]: [description]
    """
    # An arbitrarily very large positive number in place of positive infinity.
    # Almost exclusively function as an infinity flag instead of actually
    # particupating in algebraic calculations, except for the boundary condition
    # of a shorted end. In that case, in the calculation of the capacitive energy
    # participation, the shorted end term is proportional to ,
    # (C_shorted * cos(pi/2)) ^ 2, where C_shorted is infinity. Here, one cannot
    # use np.infty for C_shorted because np.infty * np.cos(np.pi/2) = np.infty in python
    # instead of zero as one would expect.
    #
    # Ultimately, the energy particpation of the shorted end doesn't matter as
    # long as it's close to zero and not infinity since it's energy participation
    # of the other (loaded with finite capacitance) end that matters.
    _POS_INFTY = 1e30
    # Convert to SI
    wr = fr * MHzRad
    if cap_loading == {}:
        raise ValueError('At least one loading capacitor needs to be defined. ')
    elif len(cap_loading) == 1:
        cap_loading['_cl'] = 0 if not shorted else _POS_INFTY

    w_loading = {}
    for node, val in cap_loading.items():
        cap_loading[node] = val * FEMTO
        if val == _POS_INFTY:
            w_loading[node] = 0
        else:
            w_loading[node] = 1 / (Z0 *
                                   cap_loading[node]) if val else _POS_INFTY

    # assign z = 0 to one of the nodes and z = L to the other; switching
    # the assignment would not change the result
    z = {}
    nodes = set(cap_loading.keys())
    for node, val in cap_loading.items():
        z['0'] = node
        if val != 0 and val < _POS_INFTY:
            break
    z['L'] = list(nodes - {z['0']})[0]

    c = 1 / (Z0 * vp)  # cap/unit length

    phi = np.arctan(wr / w_loading[z['0']])
    k = wr / vp
    utl = lambda z: np.cos(k * z + phi)
    utl2 = lambda z: utl(z)**2
    m = 1  # mode number

    w_loading_vals = list(w_loading.values())

    def _arctan_arg(w_L, w_R):
        """Need separate handling for limiting cases
        from different boundary conditions
        """
        # left boundary of the TL is open, i.e., left loading capacitor is 0
        if w_L == _POS_INFTY:
            return -wr / w_R
        # right boundary of the TL is open, i.e., right loading capacitor is 0
        elif w_R == _POS_INFTY:
            return -wr / w_L
        else:
            return wr * (w_L + w_R) / (wr**2 - w_L * w_R)

    root_eq = lambda L: np.arctan(
        _arctan_arg(w_loading_vals[0], w_loading_vals[1])
    ) + m * np.pi - k * L  # = 0
    sol = optimize.root(root_eq, [0.007], jac=False,
                        method='hybr')  # in meters SI
    Ltl = sol.x[0]

    E_cap = (0.5 * c * integrate.quad(utl2, 0, Ltl)[0] +
             0.5 * cap_loading[z['0']] * utl(0)**2 +
             0.5 * cap_loading[z['L']] * utl(Ltl)**2)

    pCL = {}
    Q_zpf = {}
    Phi_zpf = {}

    for node, val in cap_loading.items():
        if node == z['0']:
            pCL[node] = 0.5 * val * utl(0)**2 / E_cap
        else:
            pCL[node] = 0.5 * val * utl(Ltl)**2 / E_cap
        Q_zpf[node] = np.sqrt(hbar * wr / 2 * pCL[node] * val)

        # using the uncertainty relationship that Q_zpf * Phi_zpf = hbar / 2
        Phi_zpf[node] = 0.5 * hbar / Q_zpf[node]

    return Q_zpf, Phi_zpf, phi, Ltl


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


def _cj_dict_to_adj_list(cj_dict: Dict[Tuple, float]) -> DefaultDict(list):
    graph = defaultdict(list)
    for (n1, n2), c in cj_dict.items():
        graph[n1].append((n2, -c))
        graph[n1].append((n1, c))
        graph[n2].append((n2, c))
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
    For example:
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

    # each junction flux can potentially replace one of two original nodes in the new flux basis.
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


class LabeledNdarray(np.ndarray):
    """np.ndarray subclass that shows labels when the array is printed.

    The constructor only accepts a square matrix. Sliced LabeledNdarray will still be
    a LabeledNdarray but the labels are not preserved: if the resulting matrix is still
    a square matrix, the labels will just be [0, 1, ...<array_row_number>-1]; and if the
    the resulting matrix is not a square matrix, there will be no labels.

    """

    def __new__(cls, input_array: np.ndarray, labels=None):
        if input_array.shape[0] != input_array.shape[1]:
            raise ValueError(
                'LabeledNdarray constructor only supports square matrices.')
        obj = np.asarray(input_array).view(cls)
        obj.labels = labels if labels is not None else [
            str(x) for x in range(obj.shape[0])
        ]
        return obj

    def to_dataframe(self):
        """ output to pandas dataframe
        """
        if len(self.shape) == 1 or self.shape[0] != self.shape[1]:
            raise ValueError(
                'Only square matrices are labeled and can be exported to dataframe.'
            )
        return _make_cmat_df(self, self.labels)

    def __array_finalize__(self, obj):
        if obj is None:
            return
        if self.shape != obj.shape:
            self.labels = [str(x) for x in range(self.shape[0])]
        else:
            self.labels = getattr(obj, 'labels',
                                  [str(x) for x in range(self.shape[0])])

    def __repr__(self):
        if len(self.shape) == 1 or self.shape[0] != self.shape[1]:
            return f'{self.view(np.ndarray)}'
        return f'{_make_cmat_df(self, self.labels)}'

    def __str__(self):
        if len(self.shape) == 1 or self.shape[0] != self.shape[1]:
            return f'{self.view(np.ndarray)}'
        return f'{_make_cmat_df(self, self.labels)}'


#----------------------------------------------------------------------------------------------------


def _maybe_remove_grd_node_then_cache(f):
    """function decorator that takes the matrix output
    of a function, i.e., f(), removes the ground node from
    the matrix and caches the result
    """

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
    class implementing the lumped model circuit analysis.
    Notations closely follow that of https://arxiv.org/pdf/2103.10344.pdf

    User shouldn't have to instantiate this class themself as it is
    created automatically by the CompositeSystem class

    The object corresponds to the entire composite system, incorporating inputs
    of all the cells provided
    """

    units = {'capacitance': 'fF', 'inductance': 'nH'}
    _IGNORE_GRD_NODE = True

    def __init__(
        self,
        nodes: Sequence,
        grd_node: str,
        cmats: List[pd.DataFrame],
        ind_lists: List[Dict[Tuple, float]],
        junctions: Mapping[Tuple[str, str], str],
        cj_dicts: List[Dict[Tuple, float]] = None,
        nodes_force_keep: Sequence = None,
        s_remove_provided: Union[np.ndarray, bool] = False,
        s_keep_provided: Union[np.ndarray, bool] = False,
    ):
        """Initialize the class with parameters specifying the circuit

        Args:
            nodes (Sequence): a list of the nodes
            grd_node (str): name of the ground node
            cmats (List[pd.DataFrame]): list of Maxwell capacitance matrices in pandas
                dataframes, one for each cell provided
            ind_lists (List[Dict[Tuple, float]]): list of dicts where each dict specifies
                the inductances in each cell. For the dict, the keys are tuples of specifying
                the two nodes between which the inductors lie.
                For example, [{('n1', 'n2'): 10}, {('n5', 'n7'): 13}] specifies that there
                is an inductor of 10 nH between node 'n1' and 'n2' for one cell and an
                inductor of 13 nH between node 'n5' and 'n7' for another cell
            junctions (Mapping[Tuple[str, str], str]): dict mapping original circuit
                nodes to custom-named junction nodes. This is the parameter informing
                the LOM analysis between which nodes the Josephson junctions are located.
                For example, {('n1', 'n2'): 'j1'} specifies that there is a junction
                between nodes 'n1' and 'n2' and named as 'j1'
            cj_dicts (List[Dict[Tuple, float]], optional): if provided, specifies
                the junction capacitances in each cell. Structure is the same as ind_lists.
                For the dict, the keys are tuples of specifying the two nodes between which
                the junctions lie. For example, [{('n1', 'n2'): 2}, None] specifies that there
                is an junction capacitance of 2 fF between node 'n1' and 'n2' for the first
                provided cell and None for the second provided cell. Defaults to None.
            nodes_force_keep (Sequence, optional): a list of nodes that will not be eliminated
                during L and C matrices reduction. Use this parameter to specify non-dynamic
                nodes (nodes that are connected capacitors only or inductors only) that should
                be preserved. If not specified (i.e., None), all non-dynamic nodes are eliminated
            s_remove_provided (np.ndarray): precalculated s_remove; see documentation on S_Remove. This is
                useful when a circuit's topology doesn't change hence s_remove doesn't change and can be
                reused
            s_keep_provided (np.ndarray): precalculated s_keep; see documentation on S_Keep. This is
                useful when a circuit's topology doesn't change hence s_keep doesn't change and can be
                reused
        """

        self.nodes = list(nodes)
        self.idx = pd.Index(self.nodes)
        self._grd_node = grd_node
        self.ignore_grd_node = CircuitGraph._IGNORE_GRD_NODE
        self.grd_idx = self.idx.get_indexer([grd_node])[0]
        self.nodes_force_keep = nodes_force_keep

        self._c_graphs = [_df_cmat_to_adj_list(m) for m in cmats]
        if cj_dicts is not None:
            for cj_dict in cj_dicts:
                if cj_dict is not None:
                    self._c_graphs.append(_cj_dict_to_adj_list(cj_dict))

        self._ind_lists = ind_lists
        self._junctions = junctions

        self._C_n = None
        self._L_n_inv = None

        # TODO: Handle cached properties dependencies more rigorously, i.e., set them to None, when
        # their dependencies change
        self._C_inv_k = None
        self._C_k = None
        self._L_inv_k = None

        self._S_n = None
        self._node_jj_basis = None

        self._s_remove_provided = s_remove_provided
        self._s_keep_provided = s_keep_provided

    def __str__(self):
        str_out = 'node_jj_basis:\n'
        str_out += '-------------\n'
        str_out += '\n'
        str_out += f'{self.node_jj_basis}\n'
        str_out += '\n'
        str_out += 'nodes_keep:\n'
        str_out += '-------------\n'
        str_out += '\n'
        str_out += f'{self.get_nodes_keep()}\n'
        str_out += '\n'
        str_out += '\n'
        str_out += 'L_inv_k (reduced inverse inductance matrix):\n'
        str_out += '-------------\n'
        str_out += '\n'
        str_out += f'{self.L_inv_k}\n'
        str_out += '\n'
        str_out += 'C_k (reduced capacitance matrix):\n'
        str_out += '-------------\n'
        str_out += '\n'
        str_out += f'{self.C_k}\n'
        str_out += '\n'

        return str_out

    def _adj_list_to_mat(self, adj_list):
        """ convert adjacency list representation of capacitance graph to
        a matrix representation
        """
        idx = self.idx
        dim = len(idx)
        mat = np.zeros((dim, dim))
        for n1 in adj_list:
            for n2, w in adj_list[n1]:
                r = idx.get_indexer([n1])[0]
                c = idx.get_indexer([n2])[0]
                mat[r, c] += w
                if r != c:
                    mat[c, r] += w
        return mat

    def _inductance_list_to_Linv_mat(self, ind_dict):
        """ convert inductance list to inductance inverse matrix
        """
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
        """
        https://arxiv.org/pdf/2103.10344.pdf
        equation (5)
        """
        dim = len(self.idx)
        C_n = np.zeros((dim, dim))
        for c_g in self._c_graphs:
            C_n += self._adj_list_to_mat(c_g)
        return LabeledNdarray(C_n, self.orig_node_basis)

    @property
    @_maybe_remove_grd_node_then_cache
    def L_n_inv(self):
        """
        https://arxiv.org/pdf/2103.10344.pdf
        equation (5)
        """
        dim = len(self.idx)
        L_n_inv = np.zeros((dim, dim))
        for l_dict in self._ind_lists:
            L_n_inv += self._inductance_list_to_Linv_mat(l_dict)
        return LabeledNdarray(L_n_inv, self.orig_node_basis)

    @property
    @_maybe_remove_grd_node_then_cache
    def S_n(self):
        """ Linear transformation from original node basis to
        node-junction basis where all non-linear dipole fluxes are
        explicitly in the basis. The flux of the j-th dipole
        $\Phi_{j} = \Phi_{n2} - \Phi_{n1}$, where $\Phi_{n2}$ and
        $\Phi_{n1}$ are the node-to-datum fluxes of its two nodes
        .
        $\Phi = S_{n}^{-1}\Phi_n$
        """
        t = _transform_to_junction_flux_basis(self.nodes,
                                              self._junctions,
                                              choose_least_num_neg=True)
        S_n_inv = _extract_matrix_from_transform(t, self._junctions, self.idx)
        S_n = np.linalg.inv(S_n_inv)
        self._node_jj_basis = t.node_jj_basis
        return S_n

    @property
    def C(self):
        """Transformed capacitance matrix of the composite system
        """
        return LabeledNdarray(
            self.S_n.T.dot(self.C_n).dot(self.S_n), self.node_jj_basis)

    @property
    def L_inv(self):
        """Transformed inductance inverse matrix of the composite system
        """
        return LabeledNdarray(
            self.S_n.T.dot(self.L_n_inv).dot(self.S_n), self.node_jj_basis)

    @property
    def orig_node_basis(self):
        """ Original node basis consisting of node-to-datum fluxes,
        excluding the ground node
        """
        _orig_basis = self.nodes
        if self.ignore_grd_node:
            _orig_basis = [
                _node for _node in _orig_basis if _node != self._grd_node
            ]
        return _orig_basis

    @property
    def node_jj_basis(self):
        """ Node-junction basis which is linear transformation
        from original node basis to where all non-linear dipole fluxes are
        explicitly in the basis. The flux of the j-th dipole
        $\Phi_{j} = \Phi_{n2} - \Phi_{n1}$, where $\Phi_{n2}$ and
        $\Phi_{n1}$ are the node-to-datum fluxes of its two nodes
        .
        $\Phi = S_{n}^{-1}\Phi_n$
        """
        if self._node_jj_basis is None:
            _ = self.S_n
        _node_jj_basis = self._node_jj_basis
        if self.ignore_grd_node:
            _node_jj_basis = [
                _node for _node in _node_jj_basis if _node != self._grd_node
            ]
        return _node_jj_basis

    @property
    def S_remove(self):
        """ Eliminate coupler constraints due to the singularity of
        the inverse inductance matrix. Here we eliminate fluxes
        in the kernel space of the transformed inverse inductance
        matrix. These are nodes that are only touched by capacitors and are
        considered non-dynamic nodes.
        """
        if self._s_remove_provided is not False:
            return self._s_remove_provided
        nodes_force_keep = self.nodes_force_keep if self.nodes_force_keep else []
        force_keep_idx = pd.Index(
            self.node_jj_basis).get_indexer(nodes_force_keep)
        if np.where(force_keep_idx < 0)[0].size:
            bad_nodes = list(
                np.array(nodes_force_keep)[np.where(force_keep_idx < 0)])
            bad_nodes_str = ', '.join(bad_nodes)
            raise ValueError(
                f'nodes {bad_nodes_str} in input node_force_keep are not in the flux basis [self.node_jj_basis].'
            )

        L_inv = self.L_inv
        _s_r = []
        null_space = Matrix(L_inv).nullspace()
        for _v in null_space:
            v = _v / _v.norm()
            v = np.array(v).astype(np.float64)
            if np.count_nonzero(v) != 1:
                raise ValueError(
                    f'Nullspace column vector {v} has more than one non-zero element. \
                                 Only individual nodes in the current flux [see self.node_jj_basis] basis can be removed'
                )

            # if the node to be removed is in the list of nodes that are forced to be kept, don't remove
            if np.where(force_keep_idx == np.where(v)[0][0])[0].size:
                continue
            _s_r.append(v)

        return np.concatenate(_s_r, axis=1) if _s_r else None

    @property
    def S_keep(self):
        """ Complement of S_remove
        """
        # FIXME: currently assuming that S_keep can be solely constructed from
        # S_remove (which itself is constructed from the identity matrix) and the identity matrix
        if self._s_keep_provided is not False:
            return self._s_keep_provided
        S_remove = self.S_remove
        dim = self.L_inv.shape[0]
        eye = np.eye(dim)
        return eye[:, np.where(S_remove.T.sum(
            axis=0) == 0)[0]] if S_remove is not None else eye

    def get_nodes_keep(self):
        s_keep = self.S_keep
        dim = s_keep.shape[0]
        keep_idx = s_keep.T.dot(np.arange(dim)[:, np.newaxis])[:, 0].astype(int)
        return np.array(self.node_jj_basis)[keep_idx].tolist()

    def get_nodes_remove(self):
        s_remove = self.S_remove
        if s_remove is not None:
            dim = s_remove.shape[0]
            remove_idx = s_remove.T.dot(
                np.arange(dim)[:, np.newaxis])[:, 0].astype(int)
            return np.array(self.node_jj_basis)[remove_idx].tolist()
        else:
            return []

    @property
    def L_inv_k(self):
        """
        https://arxiv.org/pdf/2103.10344.pdf
        equation (7a)
        """
        if self._L_inv_k is not None:
            return self._L_inv_k
        s_keep = self.S_keep
        l_inv = self.L_inv
        self._L_inv_k = LabeledNdarray(
            s_keep.T.dot(l_inv).dot(s_keep), self.get_nodes_keep())
        return self._L_inv_k

    @property
    def C_k(self):
        """
        https://arxiv.org/pdf/2103.10344.pdf
        equation (7b)
        """
        if self._C_k is not None:
            return self._C_k
        s_k = self.S_keep
        s_r = self.S_remove
        c = self.C
        _inner = c.dot(s_r).dot(np.linalg.inv(s_r.T.dot(c.dot(s_r)))).dot(
            s_r.T.dot(c)) if s_r is not None else 0
        self._C_k = LabeledNdarray(
            s_k.T.dot(c - _inner).dot(s_k), self.get_nodes_keep())
        return self._C_k

    @property
    def C_inv_k(self):
        if self._C_inv_k is not None:
            return self._C_inv_k
        c_k = self.C_k
        if np.linalg.matrix_rank(c_k) < c_k.shape[0]:
            raise ValueError('C_k is rank deficient hence can\'t be inverted')
        self._C_inv_k = LabeledNdarray(np.linalg.inv(self.C_k),
                                       self.get_nodes_keep())
        return self._C_inv_k


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
    subsystem_idx = node_idx[node_idx >= 0]
    if subsystem_idx.size != 1 and single_node:
        raise ValueError(
            f'One and ONLY one node in the reduced node-junction basis should map to the {subsystem.sys_type} subsystem.'
        )
    elif subsystem_idx.size != node_idx.size:
        raise ValueError(
            'One or more subsystem nodes not found in the circuit\'s nodes.')
    return subsystem_idx


def _process_input_gs(gs):
    # TODO: to be implemented
    return gs


class QuantumSystemRegistry:
    _system_registry = {}

    @classmethod
    def add_to_registry(cls, name, builder):
        cls._system_registry[name] = builder

    @classmethod
    def registry(cls):
        return cls._system_registry


class Subsystem:
    """Class representing a subsystem that can typically be mapped to a quantum system with known
    solution, such as a transmon, a fluxonium or a quantum harmonic osccilator

    frequencies if entered in q_opts need to be in GHz
    """

    def __init__(self,
                 name: str,
                 sys_type: str,
                 nodes: List[str],
                 q_opts: dict = None):
        """Initialize the Subsystem object

        Args:
            name (str): name of the subsystem
            sys_type (str): type of the subsystem. Type can be one of the types implemented
                by one of the concrete QuantumBuilders (call QuantumSystemRegistry.registry()
                to see all the choices), which can also be custom-made by user
            nodes (List[str]): list of nodes the subsystem corresponds to. For example, for
                a transmon subsystem, this would just be a list of a single node which is the
                user-defined junction node in the Cell object
            q_opts (dict, optional): options relevant to the type of quantum subsystem. The
                Subsystem object builds the quantum subsystem using quantumfy() which calls
                make_quantum() of the corresponding QuantumBuilder. q_opts provides
                parameters needed by make_quantum(). In the case of qubit subsystems, make_quantum()
                takes advantage of the scQbuits package (https://scqubits.readthedocs.io).
                Consequently, the default options correspond to the default options of the qubit
                classes in scQubits. Defaults to None.
        """
        self.name = name
        self.sys_type = sys_type
        self.nodes = nodes
        self.q_opts = q_opts
        self._quantum_system = None
        self._h_params = defaultdict(dict)
        self.system_params = {}

    @property
    def h_params(self):
        """ Hamiltonian parameters of the subsystem
        """
        if self._h_params == {}:
            raise ValueError(
                f'Subsystem {self.name}\'s Hamiltonian parameters have not been calculated.'
            )
        return self._h_params

    @property
    def quantum_system(self):
        """ The quantum subsystem that the subsystem corresponds to. It
        is built by calling an associated builder passed in quantumfy()
        using the Visitor pattern
        """
        if self._quantum_system is None:
            raise ValueError(
                f'Subsystem {self.name}\'s quantum system has not been created.'
            )
        return self._quantum_system

    def quantumfy(self, quantum_builder) -> None:
        """ Building the corresponding quantum system with an
        associated builder
        """
        quantum_builder.make_quantum(self)


class _QuantumBuilderMeta(type):

    def __init__(cls, name, bases, attrs):
        # register the class in the QuantumSystemType registry
        # if it is not the base class, i.e. excluding QuantumBuilder
        if bases:
            sys_type = getattr(cls, 'system_type', None)
            if sys_type is None:
                raise AttributeError(
                    'You need to define a type string for your QuantumBuilder class by assigning a "system_type" class attribute.'
                    +
                    ' For example, the "system_type" for the TransmonBuilder is "TRANSMON", FluxoniumBuilder "FLUXONIUM".'
                )
            QuantumSystemRegistry.add_to_registry(sys_type, cls)

            logger.info(
                '%s with system_type %s registered to QuantumSystemRegistry',
                cls.__name__, sys_type)

        super().__init__(name, bases, attrs)


class QuantumBuilder(metaclass=_QuantumBuilderMeta):

    def __init__(self, cg: CircuitGraph):
        self.cg = cg
        self.nodes_keep = self.cg.get_nodes_keep()
        self.reduced_mat_idx = pd.Index(self.nodes_keep)

    def make_quantum(self, subsystem: Subsystem):
        raise NotImplementedError


class QuantumBuilderOptions(argparse.Namespace):

    def set_from_input(self, input_opts: Dict):
        if input_opts is not None and len(input_opts):
            for k, v in input_opts.items():
                setattr(self, k, v)

    def view_as(self, group: Union[str, type]):
        if isinstance(group, str):
            return getattr(self, group, None)
        elif isinstance(group, type):
            opts = {}
            args = get_all_args(group.__init__)
            for arg in args:
                opts[arg] = getattr(self, arg, None)
            return opts


def set_builder_options(func):

    def wrapper(self, subsystem):
        dflt_opts = getattr(self, 'default_opts', {})
        build_options = QuantumBuilderOptions(**dflt_opts)
        build_options.set_from_input(subsystem.q_opts)
        setattr(self, 'builder_options', build_options)
        func(self, subsystem)

    return wrapper


class TransmonBuilder(QuantumBuilder):
    """
    Concrete builder class for a type of quantum subsystem
    Each subsystem of a composite system calls make_quantum() method of this class
    to map LOM analysis results, the reduced L and C matrix elements to hamiltonian
    parameters, such as Ej, Ec and etc

    To create your own custom quantum builder, follow the patterns of the existing
    ones, such this one, or the other ones implemented in this library

        system_type (str): name of the quantum subsystem
        default_opts (dict): default options relevant to the type of quantum
            subsystem. Provide any default values for the paremeters that
            make_quantum() needs. In the case of qubit subsystems, make_quantum()
            takes advantage of the scQbuits package (https://scqubits.readthedocs.io).
            Consequently, the default options correspond to the default options of
            the qubit classes in scQubits
    """

    system_type = 'TRANSMON'
    default_opts = {'ng': 0.001, 'ncut': 22, 'truncated_dim': 10}

    # pylint: disable=protected-access
    # pylint: disable=no-member
    @set_builder_options
    def make_quantum(self, subsystem: Subsystem):
        """ concrete building function for the builder to build the quantum
        system based on default options and input options set for the
        Subsystem object
        """
        cg = self.cg
        l_inv_k = cg.L_inv_k
        c_inv_k = cg.C_inv_k

        subsystem_idx = _find_subsystem_mat_index(cg,
                                                  subsystem,
                                                  single_node=True)
        ss_idx = subsystem_idx[0]
        subsystem.system_params['subsystem_idx'] = subsystem_idx

        # EJ and EC are in MHz
        EJ = Convert.Ej_from_Lj(1 / l_inv_k[ss_idx, ss_idx])
        EC = Convert.Ec_from_Cs(1 / c_inv_k[ss_idx, ss_idx])
        Q_zpf = 2 * ele
        builder_options = self.builder_options
        builder_options.EJ = EJ
        builder_options.EC = EC
        transmon = scq.Transmon(**builder_options.view_as(scq.Transmon))

        subsystem._quantum_system = transmon
        node = subsystem.nodes[0]
        subsystem._h_params[node] = dict(EJ=EJ, EC=EC, Q_zpf=Q_zpf)
        subsystem._h_params[node]['default_charge_op'] = Operator(
            transmon.n_operator(), False)


class FluxoniumBuilder(QuantumBuilder):
    """
    Concrete builder class for a type of quantum subsystem
    Each subsystem of a composite system calls make_quantum() method of this class
    to map LOM analysis results, the reduced L and C matrix elements to hamiltonian
    parameters, such as Ej, Ec and etc

    To create your own custom quantum builder, follow the patterns of the existing
    ones, such this one, or the other ones implemented in this library

        system_type (str): name of the quantum subsystem
        default_opts (dict): default options relevant to the type of quantum
            subsystem. Provide any default values for the paremeters that
            make_quantum() needs. In the case of qubit subsystems, make_quantum()
            takes advantage of the scQbuits package (https://scqubits.readthedocs.io).
            Consequently, the default options correspond to the default options of
            the qubit classes in scQubits
    """

    system_type = 'FLUXONIUM'
    default_opts = {'cutoff': 110, 'truncated_dim': 10}

    # pylint: disable=protected-access
    # pylint: disable=no-member
    @set_builder_options
    def make_quantum(self, subsystem: Subsystem):
        """ concrete building function for the builder to build the quantum
        system based on default options and input options set for the
        Subsystem object
        """
        cg = self.cg
        c_inv_k = cg.C_inv_k

        subsystem_idx = _find_subsystem_mat_index(cg,
                                                  subsystem,
                                                  single_node=True)
        ss_idx = subsystem_idx[0]
        subsystem.system_params['subsystem_idx'] = subsystem_idx

        # EJ and EC are in MHz
        EC = Convert.Ec_from_Cs(1 / c_inv_k[ss_idx, ss_idx])
        Q_zpf = 2 * ele
        builder_options = self.builder_options
        builder_options.EC = EC
        fluxonium = scq.Fluxonium(**builder_options.view_as(scq.Fluxonium))

        subsystem._quantum_system = fluxonium

        node = subsystem.nodes[0]
        subsystem._h_params[node] = dict(EJ=builder_options.EJ,
                                         EC=builder_options.EC,
                                         EL=builder_options.EL,
                                         flux=builder_options.flux,
                                         Q_zpf=Q_zpf)
        subsystem._h_params[node]['default_charge_op'] = Operator(
            fluxonium.n_operator(), False)


class TLResonatorBuilder(QuantumBuilder):
    """
    Concrete builder class for a type of quantum subsystem
    Each subsystem of a composite system calls make_quantum() method of this class
    to map LOM analysis results, the reduced L and C matrix elements to hamiltonian
    parameters, such as Ej, Ec and etc

    To create your own custom quantum builder, follow the patterns of the existing
    ones, such this one, or the other ones implemented in this library

        system_type (str): name of the quantum subsystem
        default_opts (dict): default options relevant to the type of quantum
            subsystem. Provide any default values for the paremeters that
            make_quantum() needs. In the case of qubit subsystems, make_quantum()
            takes advantage of the scQbuits package (https://scqubits.readthedocs.io).
            Consequently, the default options correspond to the default options of
            the qubit classes in scQubits
    """

    system_type = 'TL_RESONATOR'
    default_opts = {
        'Z0': 50,
        'vp': 'use_design',  # phase velocity
        'design': {
            'line_width': 10 * 1e-6,
            'line_gap': 6 * 1e-6,
            'substrate_thickness': 750 * 1e-6,
            'film_thickness': 200 * 1e-9
        },
        'truncated_dim': 3,
        'other_end_shorted': False
    }

    # pylint: disable=protected-access
    # pylint: disable=no-member
    @set_builder_options
    def make_quantum(self, subsystem: Subsystem):
        """ concrete building function for the builder to build the quantum
        system based on default options and input options set for the
        Subsystem object
        """
        cg = self.cg
        c_inv_k = cg.C_inv_k

        builder_options = self.builder_options
        f_res = builder_options.f_res
        Z0 = builder_options.Z0
        # convert to MHz
        f_res *= 1000
        builder_options.E_osc = f_res

        if builder_options.vp == 'use_design':
            lambdaG, _, _ = guided_wavelength(f_res * 10**6,
                                              **builder_options.design)
            vp = f_res * MHzRad * lambdaG / (2 * np.pi)
        else:
            vp = float(builder_options.vp)

        subsystem_idx = _find_subsystem_mat_index(cg,
                                                  subsystem,
                                                  single_node=False)

        subsystem.system_params['subsystem_idx'] = subsystem_idx

        if len(subsystem_idx) > 2:
            raise ValueError(
                'Transmission line resonator currently supports at most two nodes.'
            )
        elif len(subsystem_idx) == 2 and builder_options.other_end_shorted:
            raise ValueError(
                'Transmission line resonator should have only one node \
                specified if one of its boundaries is shorted to ground.')

        loading_capacitor = {}
        for ii, node in enumerate(subsystem.nodes):
            loading_capacitor[node] = 1 / c_inv_k[subsystem_idx[ii],
                                                  subsystem_idx[ii]]

        resonator = scq.Oscillator(**builder_options.view_as(scq.Oscillator))
        subsystem._quantum_system = resonator

        Q_zpf, *_ = analyze_loaded_tl(f_res,
                                      vp,
                                      Z0,
                                      cap_loading=loading_capacitor,
                                      shorted=builder_options.other_end_shorted)

        for node in subsystem.nodes:
            subsystem._h_params[node]['Q_zpf'] = Q_zpf[node]
            subsystem._h_params[node]['default_charge_op'] = Operator(
                1j * (resonator.creation_operator() -
                      resonator.annihilation_operator()), False)


class LumpedResonatorBuilder(QuantumBuilder):
    """
    Concrete builder class for a type of quantum subsystem
    Each subsystem of a composite system calls make_quantum() method of this class
    to map LOM analysis results, the reduced L and C matrix elements to hamiltonian
    parameters, such as Ej, Ec and etc

    To create your own custom quantum builder, follow the patterns of the existing
    ones, such this one, or the other ones implemented in this library

        system_type (str): name of the quantum subsystem
        default_opts (dict): default options relevant to the type of quantum
            subsystem. Provide any default values for the paremeters that
            make_quantum() needs. In the case of qubit subsystems, make_quantum()
            takes advantage of the scQbuits package (https://scqubits.readthedocs.io).
            Consequently, the default options correspond to the default options of
            the qubit classes in scQubits
    """

    system_type = 'LUMPED_RESONATOR'
    default_opts = {'truncated_dim': 3}

    # pylint: disable=protected-access
    # pylint: disable=no-member
    @set_builder_options
    def make_quantum(self, subsystem: Subsystem):
        """ concrete building function for the builder to build the quantum
        system based on default options and input options set for the
        Subsystem object
        """
        cg = self.cg
        l_inv_k = cg.L_inv_k
        c_inv_k = cg.C_inv_k

        subsystem_idx = _find_subsystem_mat_index(cg,
                                                  subsystem,
                                                  single_node=True)
        ss_idx = subsystem_idx[0]
        subsystem.system_params['subsystem_idx'] = subsystem_idx

        builder_options = self.builder_options

        # TODO: should we be more explicit about units?
        # assume l_inv_k is in 1/nH and c_inv_k is in 1/fF
        l = 1 / l_inv_k[ss_idx, ss_idx] * NANO
        c = 1 / c_inv_k[ss_idx, ss_idx] * FEMTO

        # resonant angular frequency in radians/s
        w_res = 1 / np.sqrt(l * c)
        # convert to MHz
        f_res = w_res / MHzRad
        builder_options.E_osc = f_res

        Z = np.sqrt(l / c)
        Q_zpf = np.sqrt(hbar / (2 * Z))
        resonator = scq.Oscillator(**builder_options.view_as(scq.Oscillator))
        subsystem._quantum_system = resonator

        node = subsystem.nodes[0]
        subsystem._h_params[node]['Q_zpf'] = Q_zpf
        subsystem._h_params[node]['default_charge_op'] = Operator(
            1j *
            (resonator.creation_operator() - resonator.annihilation_operator()),
            False)


class Cell:
    """A physical subdivision of the device (i.e., the composite system), a sub-graph
    of capaciators, inductoros and other linear or non-linear circuit elements. The
    cell can be independently simulated to extract its electromagnetic parameters, which
    the the user provides as inputs to this object
    """

    def __init__(self, options: Dict):
        """Initialize the cell object

        Args:
            options (Dict): options can contain the following keys
                node_rename (dict): a dict mapping from original node names to
                    new node names, {old_name: new_name}
                cap_mat (pd.DataFrame): Maxwell capacitance of the cell in
                    pandas dataframe
                ind_dict (dict): the keys are tuples of specifying the two nodes
                    between which the inductors lie. For example,
                    {('n1', 'n2'): 10} specifies that there is an inductor of 10
                    nH between node 'n1' and 'n2' for one cell and an inductor of
                    13 nH between node 'n5' and 'n7' for another cell
                jj_dict (dict): dict mapping original circuit nodes to custom-named
                    junction nodes. This is the parameter informing the LOM analysis between
                    which nodes the Josephson junctions are located. For example,
                    {('n1', 'n2'): 'j1'} specifies that there is a junction between
                    nodes 'n1' and 'n2' and named as 'j1' cf_dict (dict):
                cj_dict (dict): if provided, specifies the junction capacitances in each
                    cell. Structure is the same as ind_dict. For the dict, the keys are
                    tuples of specifying the two nodes between which the junctions lie.
                    For example, {('n1', 'n2'): 2} specifies that there is an
                    junction capacitance of 2 fF between node 'n1' and 'n2' for the first
                    provided cell and None for the second provided cell.

        """
        self._node_rename = options.get('node_rename', {})
        self.cap_mat = _rename_nodes_in_df(self._node_rename,
                                           options['cap_mat'])
        self.ind_dict = None
        self.jj_dict = None
        self.cj_dict = None

        if 'ind_dict' in options:
            self.ind_dict = _rename_nodes_in_dict(self._node_rename,
                                                  options['ind_dict'])
        if 'ind_mat' in options:
            raise NotImplementedError
        if 'jj_dict' in options:
            self.jj_dict = _rename_nodes_in_dict(self._node_rename,
                                                 options['jj_dict'])

        if 'cj_dict' in options:
            self.cj_dict = _rename_nodes_in_dict(self._node_rename,
                                                 options['cj_dict'])

        self.nodes = self.cap_mat.columns.values.tolist()


class CompositeSystem:
    """Class representing the composite system which may consist of multiple subsystems and cells
    """

    def __init__(
        self,
        subsystems: List[Subsystem],
        cells: List[Cell],
        grd_node: str,
        nodes_force_keep: Sequence = None,
        s_remove_provided: Union[np.ndarray, bool] = False,
        s_keep_provided: Union[np.ndarray, bool] = False,
    ):
        """Initialize the CompositeSystem object

        Args:
            subsystems (List[Subsystem]): list of Subsystem objects
            cells (List[Cell]): list of Cell objects
            grd_node (str): name of the ground node
            nodes_force_keep (Sequence, optional): a list of nodes that will not be eliminated
                during L and C matrices reduction. Use this parameter to specify non-dynamic
                nodes (nodes that are connected capacitors only or inductors only) that should
                be preserved. If not specified (i.e., None), all non-dynamic nodes are eliminated
            s_remove_provided (np.ndarray): precalculated s_remove; see documentation on CircuitGraph.S_Remove
            s_keep_provided (np.ndarray): precalculated s_keep; see documentation on CircuitGraph.S_Keep
        """
        self._subsystems = subsystems
        self.num_subsystems = len(subsystems)
        self.names = [sub.name for sub in self._subsystems]
        self._cells = cells
        self.num_cells = len(cells)
        self.grd_node = grd_node
        self.nodes_force_keep = nodes_force_keep

        self._s_remove_provided = s_remove_provided
        self._s_keep_provided = s_keep_provided

        self._jj = {k: j for c in self._cells for k, j in c.jj_dict.items()}
        _jj_to_node_map = dict(zip(self._jj.values(), self._jj.keys()))

        _cell_nodes = np.unique([n for c in self._cells for n in c.nodes
                                ]).tolist()
        _sys_nodes = []
        for sub in self._subsystems:
            for n in sub.nodes:
                if n not in _jj_to_node_map:
                    _sys_nodes.append(n)
                else:
                    _sys_nodes.extend(
                        list(filter(lambda x: x != grd_node,
                                    _jj_to_node_map[n])))
        if len(set(_sys_nodes)) != len(_sys_nodes):
            raise ValueError('Subsystems should not have overlapping nodes.')
        _non_sys_nodes = [n for n in _cell_nodes if n not in _sys_nodes]
        self._nodes = _sys_nodes + _non_sys_nodes

        self._c_list = [c.cap_mat for c in self._cells]
        self._cj_dicts = [c.cj_dict for c in self._cells]
        self._l_list = [c.ind_dict for c in self._cells]

        self.quantum_subsystems = []

        self._cg = None

    def circuitGraph(self) -> CircuitGraph:
        """create a CircuitGraph object with circuit parameters of the composite system

        Returns:
            CircuitGraph: CircuitGraph object for LOM analysis
        """
        if self._cg is None:
            nodes = self._nodes
            grd_node = self.grd_node
            c_list = self._c_list
            cj_dicts = self._cj_dicts
            l_list = self._l_list
            jjs = self._jj
            self._cg = CircuitGraph(nodes,
                                    grd_node,
                                    c_list,
                                    l_list,
                                    jjs,
                                    cj_dicts,
                                    self.nodes_force_keep,
                                    s_keep_provided=self._s_keep_provided,
                                    s_remove_provided=self._s_remove_provided)

        return self._cg

    @property
    def subsystems(self):
        return self._subsystems

    def node_index(self, node: str):
        """Obtain the index of a given node in the composite system's reduced
        capacitance matrix

        Args:
            node (str): name of the node
        """
        cg = self.circuitGraph()
        nodes_keep = cg.get_nodes_keep()
        reduced_mat_idx = pd.Index(nodes_keep)

        node_idx = reduced_mat_idx.get_indexer([node])
        subsystem_idx = node_idx[node_idx >= 0]

        if subsystem_idx.size == 0:
            raise ValueError('Subsystem not found in the circuit\'s nodes.')
        return subsystem_idx[0]

    def create_hilbertspace(self) -> scq.HilbertSpace:
        """ create the composite hilbertspace including all the subsystems. Interaction
            NOT included

        Returns:
            scq.HilbertSpace: Hilbertspace object for the Hamiltonian
                of the composite system without interations added
        """
        cg = self.circuitGraph()

        quantum_systems = []
        for sub in self._subsystems:
            if sub.sys_type in QuantumSystemRegistry.registry():
                q_builder = QuantumSystemRegistry.registry()[sub.sys_type](cg)
            else:
                raise NotImplementedError

            sub.quantumfy(q_builder)
            quantum_systems.append(sub.quantum_system)

        self.quantum_subsystems = quantum_systems
        return scq.HilbertSpace(quantum_systems)

    def compute_gs(self, coupling_type: str = CouplingType.CAPACITIVE):
        """compute g matrices from reduced C inverse matrix C^{-1}_{k} and reduced L inverse matrix L^{-1}_{k}
        and zero point flucuations (Q_zpf, Phi_zpf)

        Note that the computed g's are in MHz

        Note: the resulting matrix is in the basis of nodes_keep, which may not be in the same order of
        subsystems
        """
        cg = self.circuitGraph()
        nodes = cg.get_nodes_keep()

        if coupling_type == CouplingType.CAPACITIVE:
            c_inv_k = cg.C_inv_k
            g = np.zeros_like(c_inv_k)
            for ii in range(self.num_subsystems):
                sub1 = self._subsystems[ii]
                sub1_nodes = sub1.nodes
                for jj in range(ii, self.num_subsystems):
                    sub2 = self._subsystems[jj]
                    sub2_nodes = sub2.nodes
                    for node1 in sub1_nodes:
                        for node2 in sub2_nodes:
                            if node1 == node2:
                                continue
                            idx1 = self.node_index(node1)
                            idx2 = self.node_index(node2)
                            c_i = c_inv_k[idx1, idx2]
                            if c_i == 0:
                                continue
                            Q_zpf_1 = sub1.h_params[node1]['Q_zpf']
                            Q_zpf_2 = sub2.h_params[node2]['Q_zpf']
                            g[idx1, idx2] = c_i * Q_zpf_1 * Q_zpf_2 * \
                                            ONE_OVER_FEMTO / hbar / MHzRad
                            g[idx2, idx1] = g[idx1, idx2]

            return LabeledNdarray(g, nodes)
        else:
            raise NotImplementedError

    def add_interaction(self,
                        gs: np.ndarray = None,
                        gscale: float = 1.) -> scq.HilbertSpace:
        """ add interaction terms to the composite hilbertspace

        Args:
            gs (np.ndarray): coupling strength matrix. If not provided,
                it will be calculated by compute_gs()
            gscale (float): coupling strength scale

        Returns:
            scq.HilbertSpace: Hilbertspace object for the Hamiltonian
                of the composite system with interations added
        """
        cg = self.circuitGraph()
        h = self.create_hilbertspace()

        if gs is None:
            gs = self.compute_gs(coupling_type=CouplingType.CAPACITIVE)
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
            sub1_nodes = sub1.nodes
            for jj in range(ii, self.num_subsystems):
                sub2 = self._subsystems[jj]
                sub2_nodes = sub2.nodes
                for node1 in sub1_nodes:
                    for node2 in sub2_nodes:
                        if node1 == node2:
                            continue

                        idx1 = self.node_index(node1)
                        idx2 = self.node_index(node2)

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
                            q1_op, add_hc1 = sub1.h_params[node1][
                                'default_charge_op']
                            q2_op, add_hc2 = sub2.h_params[node2][
                                'default_charge_op']

                            h.add_interaction(check_validity=False,
                                              g=g * gscale,
                                              op1=(q1_op, q1),
                                              op2=(q2_op, q2),
                                              add_hc=add_hc1 or add_hc2)
        return h

    def hamiltonian_results(self,
                            hilbertspace: scq.HilbertSpace,
                            evals_count=None,
                            print_info=True) -> pd.DataFrame:
        """Print and return results

        Args:
            hilbertspace (scq.HilbertSpace): Hilbertspace object for the Hamiltonian
                of the composite system
            evals_count (int, optional): Number of eigenenergy levels to keep
                after diagonalizing the Hamiltonian. Defaults to 10.
            print_info (bool, optional): If true, print results as well. Defaults to True.

        Returns:
            pd.DataFrame: dataframe containing the results
        """
        ham_res = {}

        names = self.names

        if evals_count is None:
            evals_count = hilbertspace.dimension

        hamiltonian_mat = hilbertspace.hamiltonian()
        evals, evecs = hamiltonian_mat.eigenstates(eigvals=evals_count)

        # evals, evecs = hilbertspace.eigensys(evals_count=evals_count)
        esys_array = np.empty(shape=(2,), dtype=object)
        esys_array[0] = evals
        esys_array[1] = evecs

        f01s, chi_mat = extract_energies(esys_array,
                                         mode_size=hamiltonian_mat.dims[0])
        f01s = f01s / 1000
        ham_res['fQ_in_Ghz'] = dict(zip(names, f01s))
        ham_res['chi_in_MHz'] = LabeledNdarray(chi_mat, names)

        if print_info:
            print('')
            print('system frequencies in GHz:')
            print('--------------------------')
            print(ham_res['fQ_in_Ghz'])
            print()
            print('Chi matrices in MHz')
            print('--------------------------')
            print(ham_res['chi_in_MHz'])
        return ham_res
