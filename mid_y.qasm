OPENQASM 2.0;
include "qelib1.inc";
// H7-OS - eco de Hahn sobre GHZ de 3 qubits (exp/eco_prerregistro.md)
// modelo F (entorno cuantico fijo) sin eco, lectura XXX, realizacion 0
qreg q[3];
qreg e[3];
creg c[3];
h q[0];
cx q[0],q[1];
cx q[0],q[2];
h e;
// paso 1
cu1(pi/8) q[0],e[0];
cu1(pi/8) q[1],e[1];
cu1(pi/8) q[2],e[2];
// paso 2
cu1(pi/8) q[0],e[0];
cu1(pi/8) q[1],e[1];
cu1(pi/8) q[2],e[2];
// paso 3
cu1(pi/8) q[0],e[0];
cu1(pi/8) q[1],e[1];
cu1(pi/8) q[2],e[2];
// paso 4
cu1(pi/8) q[0],e[0];
cu1(pi/8) q[1],e[1];
cu1(pi/8) q[2],e[2];
sdg q[0];
h q;
measure q -> c;
