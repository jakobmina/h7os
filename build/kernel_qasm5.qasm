OPENQASM 2.0;
include "qelib1.inc";
// H7-OS - n mod 14 en la base GHZ: (|r> + (-1)^n |7-r>)/sqrt2
// n = 15, r = 1, paridad impar (-)
qreg q[3];
creg c[3];
// q[2] = paridad, q[1] q[0] = bits bajos del miembro del par con q[2] = 0
x q[2];
x q[0];
// codificar
h q[2];
cx q[2],q[1];
cx q[2],q[0];
// leer en la base GHZ (el inverso)
cx q[2],q[0];
cx q[2],q[1];
h q[2];
measure q -> c;
