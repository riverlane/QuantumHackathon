## This file needs to contain data generation and evaluation functions.

# cont. problems are defined by N qubits and the HW efficent params that generate the |phi>s
# discrete problems are the circuit (by hand)
import projectq.ops as ops
from projectq import MainEngine, cengines
from projectq.backends import Simulator

import numpy as np
import itertools
import random
import time

import argparse
parser = argparse.ArgumentParser(description='Generate test sets.')
parser.add_argument('--problems', metavar='P', type=int, nargs='+', default=[0, 1, 2, 3, 4, 5],
                    help='problems to regenerate data for.')

args = parser.parse_args()

def int_to_basis_element(i, NQ):
    wfn = np.zeros((2**NQ,))
    wfn[i] = 1.0
    return wfn

def generate_pm_space_vectors(NQ, N, circuit):

    basis_states = [i for i in range(0, 2**NQ)]
    evens = [s for s in basis_states if bin(s).count("1") % 2 == 0]
    odds = [s for s in basis_states if bin(s).count("1") % 2 == 1]

    train_set = []
    engine = MainEngine(backend=Simulator(), engine_list=[])

    t0 = time.time()
    for n in range(N):

        if time.time()-t0 > 10:
            print(n, N)
            t0 = time.time()
        # generate a coefficent vector in complex space.
        weights_r = np.random.uniform(low=0.0, high=1.0, size=(2**(NQ-1),) )
        weights_theta = np.random.uniform(low=0.0, high=2*np.pi, size=(2**(NQ-1),) )
        weights = weights_r * np.exp(1j*weights_theta)
        weights /= np.linalg.norm(weights) # normalize

        label = random.choices([-1, 1])[0]
        if label == -1: # 1 == odds
            ket_theta = sum( [coeff * int_to_basis_element(i, NQ=NQ) for coeff, i in zip(weights, odds)] )
        else:
            ket_theta = sum( [coeff * int_to_basis_element(i, NQ=NQ) for coeff, i in zip(weights, evens)] )

        qreg = engine.allocate_qureg(NQ) # make a new simulator
        engine.backend.set_wavefunction(ket_theta, qreg) # we've been given this state.
        engine.flush()
        # print(f"label {label} exp ZZ { engine.backend.get_expectation_value(ops.QubitOperator('Z0 Z1'), qreg) }")

        for gate, idx in circuit:
            if gate == ops.CNOT:
                gate | (qreg[idx][0], qreg[idx][1])
            else:
                gate | qreg[idx] # apply the test gates

        engine.flush()
        _, ket_phi = engine.backend.cheat()
        ops.All(ops.Measure) | qreg # clean up.
        del qreg

        train_set.append( (ket_phi, label) )
    return list(zip(*train_set)) # vectors, labels

def generate_basis_vectors(NQ, circuit):
    basis_states = [i for i in range(0, 2**NQ)]
    evens = [s for s in basis_states if bin(s).count("1") % 2 == 0]
    odds = [s for s in basis_states if bin(s).count("1") % 2 == 1]
    engine = MainEngine(backend=Simulator(), engine_list=[])

    p1_test_v, p1_test_l = [], []
    for state in basis_states:
        label = 1 if bin(state).count("1") % 2 == 0 else -1
        qreg = engine.allocate_qureg(NQ) # make a new simulator
        engine.backend.set_wavefunction(int_to_basis_element(state, NQ), qreg) # we've been given this state.

        for gate, idx in circuit:
            if gate == ops.CNOT:
                gate | (qreg[idx][0], qreg[idx][1])
            else:
                gate | qreg[idx] # apply the test gates

        engine.flush()
        _, ket_phi = engine.backend.cheat(); ops.All(ops.Measure) | qreg; engine.flush(); del qreg
        p1_test_v.append(ket_phi)
        p1_test_l.append(label)
    return p1_test_v, p1_test_l


def add_samples(problem):
    problem["TrainSamples"], problem["TrainLabels"] = generate_pm_space_vectors(NQ=problem["NumQubits"],
                                                                                N=problem["NSamples"],
                                                                                circuit=problem["U"])
    problem["TestVectors"], problem["TestLabels"] = generate_basis_vectors(NQ=problem["NumQubits"],
                                                                           circuit=problem["U"])
    problem["QuantumMeasurement"] = ops.QubitOperator(" ".join([f"Z{i}" for i in range(problem["NumQubits"])])),
    return problem


D_problem_0 = {
    "Name":"problem0",
    "NumQubits":1,

    # The (hidden!) permutation gate, and possibly it's inverse? Leave Udag as none if not known
    "U":[(ops.H, 0)], "Udag":[(ops.H, 0)],

    # For the one qubit problem we can only really give the basis elements. Lbels autogenerated
    "NSamples":2, "TrainSamples":[np.array([1, 0]), np.array([0, 1])],
    "TrainLabels":[1, -1],

    # For us: what measurement should be taken. The classical one is a map from a bitstr basis state to the observable
    "QuantumMeasurement":ops.QubitOperator("Z0"),

    # This stuff should be displyed where the participants can see it.
    "Hint":"""This is the single qubit problem we walked through at the start of the hackathon.
The U circuit we created puts the qubit into a superposition of 0 and 1.
We showed that by applying a Hadamard gate we go back to just one of the states.
"""
}


D_problem_1 = {
    "Name":"problem1",
    "NumQubits":2,
    "U":[(ops.H, 0), (ops.X, 1)], "Udag":[(ops.H, 0), (ops.X, 1)],
    "NSamples":50,
    "TimeEst":5,
    "Hint":"""This your first problem to solve in your groups.
The circuit consists of only 2 gates! One on each qubit. We promise the gates are only
from [X, Y, Z, H] - it's your job to work out what ones.
"""
}

if 1 in args.problems:
    D_problem_1 = add_samples(D_problem_1)
    print("done 1")

D_problem_2 = {
    "Name":"problem2",
    "NumQubits":2,
    "U":[(ops.H, 0), (ops.X, 1), (ops.CNOT, slice(0, 2, 1)), (ops.Y, 1)], "Udag":None,
    "NSamples":500,
    "TimeEst":5,
    "Hint":"""Problem 2: multiple qubit gates. You will need to try interacting
the qubits with one another.
"""
}

if 2 in args.problems:
    D_problem_2 = add_samples(D_problem_2)
    print("done 2")

D_problem_3 = {
    "Name":"problem3",
    "NumQubits":5,
    "U":[(ops.H, i) for i in range(5)] +
        [(ops.CNOT, slice(i, i+2, 1)) for i in range(4)],
    "Udag":None,
    "NSamples":5000,
    "TimeEst":5,
    "Hint":"""Torture test for SVM. Large layers of gates.
"""
}

if 3 in args.problems:
    t0 = time.time()
    D_problem_3 = add_samples(D_problem_3)
    print(f"done 3 in {time.time()-t0}")

C_problem_4 = {
    "Name":"problem4",
    "NumQubits":8,
    "Udag":None,
    "NSamples":500,
    "TimeEst":5,
    "Hint":"""Torture test for SVM - large HW ansatz with random params.
"""
}

if 4 in args.problems:
    depth = 5
    num_qubits = C_problem_4["NumQubits"]
    num_params = num_qubits * (3*depth + 2)
    param_values = np.random.uniform(low=0.0, high=2.0*np.pi, size=(num_params,))
    circuit = []
    p_idx_subset = list(range(num_params))
    for d in range(depth+1):
        if d == 0:
            # strip the params we need for this depth
            p_idx_subset, localps = p_idx_subset[2*num_qubits:], p_idx_subset[:2*num_qubits]
            # logger.debug(f"local parmaters: {len(localps)}")
            for i in range(num_qubits):
                circuit.append( (ops.Rx(param_values[localps[i*2]]), i) )
                circuit.append( (ops.Rz(param_values[localps[i*2+1]]), i) )
        else:
            p_idx_subset, localps = p_idx_subset[3*num_qubits:], p_idx_subset[:3*num_qubits]

            for i in range(num_qubits):
                circuit.append( (ops.Rz(param_values[localps[i*3]]), i) )
                circuit.append( (ops.Rx(param_values[localps[i*3+1]]), i) )
                circuit.append( (ops.Rz(param_values[localps[i*3+2]]), i) )

        for qi in range(num_qubits-1):
            circuit.append( (ops.CNOT, slice(qi, qi+2, 1)))

    C_problem_4["U"] = circuit
    C_problem_4 = add_samples(C_problem_4)
    print("done 4")


C_problem_5 = {
    "Name":"problem5",
    "NumQubits":10,
    "Udag":None,
    "NSamples":20000,
    "TimeEst":1200,
    "Hint":"""Continuous problem with 10 qubits.
"""
}

if 5 in args.problems:
    outer_depth = 2
    inner_depth = 1
    depth = outer_depth*inner_depth

    num_qubits = C_problem_5["NumQubits"]
    num_params = num_qubits*outer_depth*inner_depth
    param_values = np.random.uniform(low=0.0, high=2.0*np.pi, size=num_params)

    rot_arr = [ops.Rx, ops.Ry, ops.Rz]
    rots = np.random.choice(rot_arr, size=num_params)

    rots_str = ['']*num_params
    for iparam in range(num_params):
        if (rots[iparam] == ops.Rx):
            rots_str[iparam] = 'Rx'
        elif (rots[iparam] == ops.Ry):
            rots_str[iparam] = 'Ry'
        elif (rots[iparam] == ops.Rz):
            rots_str[iparam] = 'Rz'


    if (inner_depth == 1):
        hint_str = f"""{inner_depth} rotation gate is applied to each qubit.
"""
    else:
        hint_str = f"""{inner_depth} rotation gates are applied to each qubit.
"""
    if (num_qubits == 2):
        hint_str += f"""This is followed by a CNOT gate. The first qubit is used
to control a NOT gate on the second.
"""
    else:
        hint_str += f"""This is followed by {num_qubits - 1} CNOT gates. Each qubit in turn
(except the last one) is used to control a NOT gate on the next qubit.
"""

    if (outer_depth == 2):
        hint_str += f"""This whole process (rotations and CNOTS) is repeated once more.
"""
    elif (outer_depth > 2):
        hint_str += f"""This whole process (rotations and CNOTS) is repeated {outer_depth-1} times more.
"""

    hint_str += f"""The rotation gates are given below. They are ordered by qubit and then
application order so that the first rotation listed is the first rotation applied
to the first qubit, the second rotation listed is the second rotation applied to
the first qubit, and so on. The gates are:
{', '.join(rots_str)}"""

    C_problem_5["Hint"] += hint_str

    circuit = []

    for iod in range(outer_depth):
        for iid in range(inner_depth):
            idepth = iod*inner_depth + iid

            for iq in range(num_qubits):
                circuit.append( (rots[depth*iq + idepth](param_values[depth*iq + idepth]), iq) )

        for iq in range(num_qubits - 1):
            circuit.append( (ops.CNOT, slice(iq,iq+2,1)))


    C_problem_5["U"] = circuit
    C_problem_5 = add_samples(C_problem_5)
    print("done 5")



import pickle
def save_train_data(problem):
    fname = problem["Name"] + "_spec.pyz"
    with open(fname, "wb") as f:
        pickle.dump(problem, f)
        # writer = csv.writer(f)
        # for vector, label in zip(problem["TrainSamples"], problem["SampleLabels"]):
        #     writer.writerow([vector, label])

problems = [D_problem_0, D_problem_1, D_problem_2, D_problem_3, C_problem_4, C_problem_5]
for pi in args.problems:
    save_train_data(problems[pi])


def evaluate(problem, trainfn):
    t0 = time.time()
    predictfn = trainfn( zip(problem["TrainSamples"], problem["TrainLabels"]) )
    dt = time.time() - t0

    cost = 0.0
    for testvec, testres in zip(problem["TestVectors"], problem["TestLabels"]):
        p = predictfn(testvec)
        cost += abs(p-testres)

    # print("error in your solution was {}, taking {:+02.3f}s to train.".format(cost, float(dt)))
    if dt > problem["TimeEst"]:
        print(f"It took more than {problem['TimeEst']} to train your solution - we are sure there is a better method!")
