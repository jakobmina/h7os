OPENQASM 2.0;
include "qelib1.inc";
// H7-OS - prueba de unitalidad (exp/unital_prerregistro.md)
// modelo E (entorno frio), lectura Z, realizacion 0
qreg q[1];
qreg r[1];
qreg e[8];
creg c[2];
// q empieza en I/2: par de Bell con la referencia r
h q[0];
cx q[0],r[0];
// paso 1
cx q[0],e[0];
h q[0];
rz(pi/8) q[0];
cx e[0],q[0];
rz(-pi/8) q[0];
cx e[0],q[0];
h q[0];
cx q[0],e[0];
// paso 2
cx q[0],e[1];
h q[0];
rz(pi/8) q[0];
cx e[1],q[0];
rz(-pi/8) q[0];
cx e[1],q[0];
h q[0];
cx q[0],e[1];
// paso 3
cx q[0],e[2];
h q[0];
rz(pi/8) q[0];
cx e[2],q[0];
rz(-pi/8) q[0];
cx e[2],q[0];
h q[0];
cx q[0],e[2];
// paso 4
cx q[0],e[3];
h q[0];
rz(pi/8) q[0];
cx e[3],q[0];
rz(-pi/8) q[0];
cx e[3],q[0];
h q[0];
cx q[0],e[3];
// paso 5
cx q[0],e[4];
h q[0];
rz(pi/8) q[0];
cx e[4],q[0];
rz(-pi/8) q[0];
cx e[4],q[0];
h q[0];
cx q[0],e[4];
// paso 6
cx q[0],e[5];
h q[0];
rz(pi/8) q[0];
cx e[5],q[0];
rz(-pi/8) q[0];
cx e[5],q[0];
h q[0];
cx q[0],e[5];
// paso 7
cx q[0],e[6];
h q[0];
rz(pi/8) q[0];
cx e[6],q[0];
rz(-pi/8) q[0];
cx e[6],q[0];
h q[0];
cx q[0],e[6];
// paso 8
cx q[0],e[7];
h q[0];
rz(pi/8) q[0];
cx e[7],q[0];
rz(-pi/8) q[0];
cx e[7],q[0];
h q[0];
cx q[0],e[7];
// lectura Z
measure q[0] -> c[0];
measure r[0] -> c[1];
