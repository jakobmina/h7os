#!/usr/bin/env python3
"""q syndrome verificado sin el código C.

Simula el código de Steane [[7,1,3]] como vector de estado en numpy (128
amplitudes, sin tablero ni máscaras de Pauli para decidir): prepara |0_L> y
|+_L>, aplica el error, MIDE los 6 estabilizadores como valores esperados (±1),
corrige con el síndrome (la posición j es j en binario, como en steane.c) y lee
el lógico: Z^7 para |0_L>, X^7 para |+_L>. Con eso reproduce, línea por línea,
lo que imprime el kernel.

  python3 test/syndrome_ref.py               salida esperada de COMMANDS
  python3 test/syndrome_ref.py cmds          COMMANDS unidos con ';' (para run=)
  python3 test/syndrome_ref.py check LOG     compara contra la salida del kernel
  python3 test/syndrome_ref.py x 1 x 2       un caso suelto

check busca en LOG (la captura de COM1) cada bloque esperado como líneas
consecutivas, con los espacios normalizados; la línea «error ...» es eco de la
entrada y no se exige. Sale con 0 si todos los bloques coinciden, 1 si no.
"""
import itertools
import sys

import numpy as np

COMMANDS = [
    "q syndrome",
    "q syndrome x 1 x 2",
    "q syndrome x 1 z 2",
    "q syndrome y 7",
    "q syndrome x 3 z 3",
    "q syndrome x 1 x 2 x 4",
    "q syndrome x 5 x 7",
    "q syndrome z 2 z 4 z 6",
]

N = 7
DIM = 1 << N
IDX = np.arange(DIM)
ROWS = [[j for j in range(1, 8) if j >> k & 1] for k in range(3)]
POPC = np.array([bin(i).count("1") for i in range(DIM)])


def mask(pos):
    return sum(1 << (j - 1) for j in pos)


def apply_x(psi, m):
    return psi[IDX ^ m]


def apply_z(psi, m):
    return psi * (1 - 2 * (POPC[IDX & m] & 1))


def ev(psi, phi):
    return float(np.real(np.vdot(psi, phi)))


def logical_states():
    words = set()
    for c in itertools.product([0, 1], repeat=3):
        m = 0
        for k in range(3):
            if c[k]:
                m ^= mask(ROWS[k])
        words.add(m)
    zero = np.zeros(DIM, complex)
    zero[list(words)] = 1
    zero /= np.linalg.norm(zero)
    plus = (zero + apply_x(zero, DIM - 1)) / np.sqrt(2)
    return zero, plus


ZERO_L, PLUS_L = logical_states()


def run(psi0, ex, ez):
    """Error (Y = i·X·Z), medición de estabilizadores y corrección."""
    psi = apply_x(apply_z(psi0, ez), ex)
    sz = sx = 0
    for k in range(3):
        m = mask(ROWS[k])
        if ev(psi, apply_z(psi, m)) < 0:
            sz |= 1 << k
        if ev(psi, apply_x(psi, m)) < 0:
            sx |= 1 << k
    if sz:
        psi = apply_x(psi, 1 << (sz - 1))
    if sx:
        psi = apply_z(psi, 1 << (sx - 1))
    return psi, sz, sx


def case(ex, ez):
    p0, sz, sx = run(ZERO_L, ex, ez)
    pp, _, _ = run(PLUS_L, ex, ez)
    f0 = ev(p0, apply_z(p0, DIM - 1)) < 0
    fp = ev(pp, apply_x(pp, DIM - 1)) < 0
    same = abs(abs(np.vdot(ZERO_L, p0)) - 1) < 1e-9 and abs(abs(np.vdot(PLUS_L, pp)) - 1) < 1e-9
    return sz, sx, f0, fp, same


def pauli(ex, ez):
    out = []
    for j in range(1, 8):
        b = 1 << (j - 1)
        t = ("Y" if ez & b else "X") if ex & b else ("Z" if ez & b else "")
        if t:
            out.append(f"{t}{j}")
    return " ".join(out) or "ninguno"


def report(ex, ez):
    sz, sx, f0, fp, same = case(ex, ez)
    rx = ex ^ (1 << (sz - 1) if sz else 0)
    rz = ez ^ (1 << (sx - 1) if sx else 0)
    if f0 or fp:
        verdict = "Y lógico" if f0 and fp else ("X lógico" if f0 else "Z lógico")
    elif not (rx or rz):
        verdict = "corregido"
    else:
        assert same
        verdict = "estabilizador: actúa como identidad"
    return [
        f"error     {pauli(ex, ez)}",
        f"sz = {sz:03b}  ->  " + (f"corrige X{sz}" if sz else "nada"),
        f"sx = {sx:03b}  ->  " + (f"corrige Z{sx}" if sx else "nada"),
        f"residuo   {pauli(rx, rz)} · {verdict}",
        "lectura   |0_L> " + ("se invierte" if f0 else "intacto")
        + " · |+_L> " + ("se invierte" if fp else "intacto"),
    ]


def summary():
    rows = []
    for w in range(4):
        tot = ok = bad = n0 = np_ = 0
        for pos in itertools.combinations(range(1, 8), w):
            for types in itertools.product("XYZ", repeat=w):
                ex = sum(1 << (p - 1) for p, t in zip(pos, types) if t in "XY")
                ez = sum(1 << (p - 1) for p, t in zip(pos, types) if t in "ZY")
                _, _, f0, fp, _ = case(ex, ez)
                tot += 1
                bad += f0 or fp
                ok += not (f0 or fp)
                n0 += f0
                np_ += fp
        rows.append(f"{w:4d}  {tot:5d}  {ok:11d}  {bad:7d}  {n0:5d}  {np_:5d}")
    return (["peso  casos  inofensivos  lógicos  |0_L>  |+_L>"] + rows + [
        "|0_L> y |+_L>: casos en que esa lectura se invierte",
        "2 errores: solo se absorben X en un qubit y Z en otro (decodificador CSS)",
    ])


def parse(args):
    ex = ez = 0
    if len(args) % 2:
        raise ValueError("pares tipo posición")
    for t, p in zip(args[::2], args[1::2]):
        if p not in list("1234567") or t.lower() not in ("x", "y", "z"):
            raise ValueError(f"{t} {p}")
        b = 1 << (int(p) - 1)
        if t.lower() in "xy":
            ex ^= b
        if t.lower() in "zy":
            ez ^= b
    return ex, ez


def expected(cmd):
    args = cmd.split()[2:]
    return summary() if not args else report(*parse(args))


def norm(line):
    return " ".join(line.replace("\r", "").split())


def check(log_path):
    with open(log_path, "rb") as f:
        log = [norm(l) for l in f.read().decode("utf-8", "replace").split("\n")]
    log = [l for l in log if l]
    good = 0
    for cmd in COMMANDS:
        want = [norm(l) for l in expected(cmd) if not l.startswith("error ")]
        n = len(want)
        hit = any(log[i:i + n] == want for i in range(len(log) - n + 1))
        good += hit
        if not hit:
            print(f"syndrome_ref: NO coincide «{cmd}»; se esperaba:")
            for l in want:
                print("    " + l)
    print(f"syndrome_ref: {good}/{len(COMMANDS)} bloques iguales al vector de estado")
    return 0 if good == len(COMMANDS) else 1


def main(argv):
    if argv[:1] == ["cmds"]:
        print(";".join(COMMANDS))
        return 0
    if argv[:1] == ["check"] and len(argv) == 2:
        return check(argv[1])
    if argv:
        try:
            print("\n".join(report(*parse(argv))))
        except ValueError:
            print("uso: syndrome_ref.py [x|y|z pos]...  (pos 1..7) · cmds · check LOG")
            return 2
        return 0
    for cmd in COMMANDS:
        print("h7> " + cmd)
        print("\n".join(expected(cmd)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
