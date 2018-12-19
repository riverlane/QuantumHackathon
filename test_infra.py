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

    for _ in range(N):

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
    return p1_test_v, p1_test_l


D_problem_0 = {
    "Name":"problem0",
    "NumQubits":1,

    # The (hidden!) permutation gate, and possibly it's inverse? Leave Udag as none if not known
    "U":[(ops.H, 0)], "Udag":[(ops.H, 0)],

    # For the one qubit problem we can only really give the basis elements. Lbels autogenerated
    "NSamples":2, "TrainSamples":[np.array([1, 0]), np.array([0, 1])],
    "TrainLabels":[1, -1],

    # For us: what measurement should be taken. The classical one is a map from a bitstr basis state to the observable
    "QuantumMeasurement":ops.QubitOperator("Z0"), "ClassicalMeasurement": lambda wfn: np.abs(np.conj(wfn[0]*2-1) * (wfn[0]*2-1)), # amount in the 1 state

    # This stuff should be displyed where the participants can see it.
    "Hint":"""This is the single qubit problem we walked through at the start of the hackathon.
The U circuit we created puts the qubit into a superposition of 0 and 1.
We showed that by applying a Hadamard gate we go back to just one of the states.
"""
}

def add_samples(problem):
    problem["TrainSamples"], problem["TrainLabels"] = generate_pm_space_vectors(NQ=problem["NumQubits"],
                                                                                N=problem["NSamples"],
                                                                                circuit=problem["U"])
    problem["TestVectors"], problem["TestLabels"] = generate_basis_vectors(NQ=problem["NumQubits"],
                                                                           circuit=problem["U"])
    problem["QuantumMeasurement"] = ops.QubitOperator(" ".join([f"Z{i}" for i in range(problem["NumQubits"])])),
    return problem


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
D_problem_1 = add_samples(D_problem_1)
print("done 1")

D_problem_2 = {
    "Name":"problem2 - multiple qubits",
    "NumQubits":2,
    "U":[(ops.H, 0), (ops.X, 1), (ops.CNOT, slice(0, 2, 1)), (ops.Y, 1)], "Udag":None,
    "NSamples":50,
    "TimeEst":5,
    "Hint":"""Problem 2: multiple qubit gates. You will need to try interacting
the qubits with one another.
"""
}

D_problem_2 = add_samples(D_problem_2)
print("done 2")

D_problem_3 = {
    "Name":"problem3 - getting larger",
    "NumQubits":7,
    "U":[(ops.H, i) for i in range(7)],# +
        #[(ops.CNOT, slice(i, i+2, 1)) for i in range(6)] +
        #[(ops.H, i) for i in range(7)],
    "Udag":None,
    "NSamples":500,
    "TimeEst":5,
    "Hint":"""Torture test for SVM.
"""
}

t0 = time.time()
D_problem_3 = add_samples(D_problem_3)
print(f"done 3 in {time.time()-t0}")


def save_train_data(problem):
    with open(problem["Name"]) as f:
        writer = csv.writer(f)
        for vector, label in zip(problem["TrainSamples"], problem["SampleLabels"]):
            writer.writerow([vector, label])

def evaluate(problem, trainfn):
    t0 = time.time()
    predictfn = trainfn( zip(problem["TrainSamples"], problem["TrainLabels"]) )
    dt = time.time() - t0

    cost = 0.0
    for testvec, testres in zip(problem["TestVectors"], problem["TestLabels"]):
        p = predict(testvec)
        cost += abs(p-testres)

    print(f"error in your solution was {cost}, taking {dt}s to train.")
    if dt > problem["TimeEst"]:
        print(f"It took more than {problem['TimeEst']} to train your solution - we are sure there is a better method!")

print("doing trial for p3")

from small_circuits import train, train_svm
evaluate(D_problem_3, train_svm)
