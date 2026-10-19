/*
 * syndrome.c — comando "q syndrome" de H7-OS (código de Steane [[7,1,3]])
 *
 * Cálculo exacto en el marco de Pauli: solo máscaras de 7 bits, sin libc.
 */
#include "syndrome.h"

static unsigned syn7(unsigned m)
{
    unsigned s = 0, j;
    for (j = 1; j <= 7; j++)
        if (m & (1u << (j - 1)))
            s ^= j;
    return s;
}

static int par7(unsigned m)
{
    m ^= m >> 4;
    m ^= m >> 2;
    m ^= m >> 1;
    return (int)(m & 1u);
}

static int wt7(unsigned m)
{
    int w = 0;
    while (m) {
        w += (int)(m & 1u);
        m >>= 1;
    }
    return w;
}

static unsigned fix7(unsigned m)
{
    unsigned s = syn7(m);
    return s ? m ^ (1u << (s - 1)) : m;
}

struct line {
    char b[128];
    int n;
};

static void ls(struct line *l, const char *s)
{
    while (*s && l->n < (int)sizeof l->b - 2)
        l->b[l->n++] = *s++;
}

static void lc(struct line *l, char c)
{
    if (l->n < (int)sizeof l->b - 2)
        l->b[l->n++] = c;
}

static void lbin3(struct line *l, unsigned s)
{
    lc(l, (char)('0' + ((s >> 2) & 1u)));
    lc(l, (char)('0' + ((s >> 1) & 1u)));
    lc(l, (char)('0' + (s & 1u)));
}

static void ldec(struct line *l, unsigned v, int width)
{
    char t[12];
    int k = 0;
    do {
        t[k++] = (char)('0' + v % 10u);
        v /= 10u;
    } while (v);
    while (width-- > k)
        lc(l, ' ');
    while (k)
        lc(l, t[--k]);
}

static void lflush(struct line *l, h7_out_fn out)
{
    l->b[l->n++] = '\n';
    l->b[l->n] = '\0';
    out(l->b);
    l->n = 0;
}

static void lpauli(struct line *l, unsigned ex, unsigned ez)
{
    unsigned j;
    int first = 1;
    for (j = 1; j <= 7; j++) {
        unsigned b = 1u << (j - 1);
        char t = (ex & b) ? ((ez & b) ? 'Y' : 'X') : ((ez & b) ? 'Z' : 0);
        if (!t)
            continue;
        if (!first)
            lc(l, ' ');
        lc(l, t);
        lc(l, (char)('0' + j));
        first = 0;
    }
    if (first)
        ls(l, "ninguno");
}

static int streq(const char *a, const char *b)
{
    while (*a && *a == *b) {
        a++;
        b++;
    }
    return *a == *b;
}

static void usage(h7_out_fn out)
{
    out("uso: q syndrome [x|y|z pos]...   pos 1..7 · ej. q syndrome x 1 x 2\n");
    out("     q syndrome                  resumen de todos los errores de peso 0..3\n");
}

static void report(unsigned ex, unsigned ez, h7_out_fn out)
{
    struct line l = { {0}, 0 };
    unsigned sz = syn7(ex), sx = syn7(ez);
    unsigned rx = fix7(ex), rz = fix7(ez);
    int lx = par7(rx), lz = par7(rz);

    ls(&l, "error     ");
    lpauli(&l, ex, ez);
    lflush(&l, out);

    ls(&l, "sz = ");
    lbin3(&l, sz);
    ls(&l, sz ? "  ->  corrige X" : "  ->  nada");
    if (sz)
        lc(&l, (char)('0' + sz));
    lflush(&l, out);

    ls(&l, "sx = ");
    lbin3(&l, sx);
    ls(&l, sx ? "  ->  corrige Z" : "  ->  nada");
    if (sx)
        lc(&l, (char)('0' + sx));
    lflush(&l, out);

    ls(&l, "residuo   ");
    lpauli(&l, rx, rz);
    if (!rx && !rz)
        ls(&l, " · corregido");
    else if (!lx && !lz)
        ls(&l, " · estabilizador: actúa como identidad");
    else
        ls(&l, lx && lz ? " · Y lógico" : (lx ? " · X lógico" : " · Z lógico"));
    lflush(&l, out);

    ls(&l, "lectura   |0_L> ");
    ls(&l, lx ? "se invierte" : "intacto");
    ls(&l, " · |+_L> ");
    ls(&l, lz ? "se invierte" : "intacto");
    lflush(&l, out);
}

static void summary(h7_out_fn out)
{
    unsigned cnt[4][5] = { {0} };
    unsigned code, w, k;
    struct line l = { {0}, 0 };

    for (code = 0; code < (1u << 14); code++) {
        unsigned ex = 0, ez = 0, j;
        int lx, lz;
        for (j = 0; j < 7; j++) {
            if (code >> (2 * j) & 1u)
                ex |= 1u << j;
            if (code >> (2 * j + 1) & 1u)
                ez |= 1u << j;
        }
        w = (unsigned)wt7(ex | ez);
        if (w > 3)
            continue;
        lx = par7(fix7(ex));
        lz = par7(fix7(ez));
        cnt[w][0]++;
        cnt[w][(lx || lz) ? 2 : 1]++;
        cnt[w][3] += (unsigned)lx;
        cnt[w][4] += (unsigned)lz;
    }

    out("peso  casos  inofensivos  lógicos  |0_L>  |+_L>\n");
    for (w = 0; w < 4; w++) {
        static const int width[5] = { 5, 11, 7, 5, 5 };
        ldec(&l, w, 4);
        for (k = 0; k < 5; k++) {
            ls(&l, "  ");
            ldec(&l, cnt[w][k], width[k]);
        }
        lflush(&l, out);
    }
    out("|0_L> y |+_L>: casos en que esa lectura se invierte\n");
    out("2 errores: solo se absorben X en un qubit y Z en otro (decodificador CSS)\n");
}

int h7_q_syndrome(int argc, char **argv, h7_out_fn out)
{
    unsigned ex = 0, ez = 0;
    int i;

    if (argc == 0) {
        summary(out);
        return 0;
    }
    if (argc % 2) {
        usage(out);
        return -1;
    }
    for (i = 0; i < argc; i += 2) {
        const char *t = argv[i], *p = argv[i + 1];
        unsigned b;
        if (p[0] < '1' || p[0] > '7' || p[1] != '\0') {
            usage(out);
            return -1;
        }
        b = 1u << (p[0] - '1');
        if (streq(t, "x") || streq(t, "X"))
            ex ^= b;
        else if (streq(t, "z") || streq(t, "Z"))
            ez ^= b;
        else if (streq(t, "y") || streq(t, "Y")) {
            ex ^= b;
            ez ^= b;
        } else {
            usage(out);
            return -1;
        }
    }
    report(ex, ez, out);
    return 0;
}