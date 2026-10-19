/*
 * syndrome.h — síndromes exactos de Pauli para el código de Steane.
 */
#ifndef SYNDROME_H
#define SYNDROME_H

typedef void (*h7_out_fn)(const char *s);

int h7_q_syndrome(int argc, char **argv, h7_out_fn out);

#endif