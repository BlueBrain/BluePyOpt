TITLE StochKv3.mod

COMMENT
----------------------------------------------------------------
Stochastic inactivating channel using values reported in Mendonca et al. 2016.
(Modified from https://senselab.med.yale.edu/modeldb/showmodel.cshtml?model=125385&file=/Sbpap_code/mod/skaprox.mod)

The model keeps track on the number of channels in each state, and
uses a binomial distribution to update these number.

Jan 1999, Mickey London, Hebrew University, mikilon@lobster.ls.huji.ac.il
        Peter N. Steinmetz, Caltech, peter@klab.caltech.edu
14 Sep 99 PNS. Added deterministic flag.
19 May 2002 Kamran Diba.  Changed gamma and deterministic from GLOBAL to RANGE.
23 Nov 2011 Werner Van Geit @ BBP. Changed the file so that it can use the neuron random number generator. Tuned voltage dependence
16 Mar 2016 James G King @ BBP.  Incorporate modifications suggested by Michael Hines to improve stiching to deterministic mode, thread safety, and using Random123
26 Sep 2016 Christian Roessert @ BBP. Adding inactivation, changing dynamics to values reported in Mendonca et al. 2016
: LJP: OK, whole-cell patch, corrected by 10 mV (Mendonca et al. 2016)

----------------------------------------------------------------
ENDCOMMENT

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
    SUFFIX StochKv3
    THREADSAFE
    USEION k READ ek WRITE ik
    RANGE N, eta, gk, gamma, deterministic, gkbar, ik
    RANGE N0, N1, n0_n1, n1_n0
    RANGE ninf, linf, ltau, ntau, an, bn, al, bl
    RANGE P_an, P_bn, P_al, P_bl
    GLOBAL vmin, vmax
    BBCOREPOINTER rng
    :POINTER rng
}

UNITS {
    (mA) = (milliamp)
    (mV) = (millivolt)
    (pS) = (picosiemens)
    (S) = (siemens)
    (um) = (micron)
}

PARAMETER {
    v           (mV)
    dt      (ms)
    area    (um2)

    gamma  =  50      (pS)
    eta              (1/um2)
    gkbar = .01      (S/cm2)

    deterministic = 0   : if non-zero, will use deterministic version
    vmin = -120 (mV)    : range to construct tables for
    vmax = 100  (mV)
}

ASSIGNED {
    an      (/ms)
    bn      (/ms)
    al      (/ms)
    bl      (/ms)
    ik      (mA/cm2)
    gk      (S/cm2)
    ek      (mV)
    ninf        : steady-state value
    ntau (ms)   : time constant for relaxation
    linf        : steady-state value
    ltau (ms)   : time constant for relaxation

    N
    scale_dens (pS/um2)
    P_an     : probability of one channel making alpha n transition
    P_bn     : probability of one channel making beta n transition
    P_al     : probability of one channel making alpha l transition
    P_bl     : probability of one channel making beta l transition

    rng
    usingR123
}


STATE {
    n l  : state variable of deterministic description
}
ASSIGNED {
    N0L0 N1L0 N0L1 N1L1     : N states populations (These currently will not be saved via the bbsavestate functionality.  Would need to be STATE again)
    n0l0_n1l0 n0l0_n0l1     : number of channels moving from one state to the other
    n1l0_n1l1 n1l0_n0l0
    n0l1_n1l1 n0l1_n0l0
    n1l1_n0l1 n1l1_n1l0
}

COMMENT
The Verbatim block is needed to generate random nos. from a uniform distribution between 0 and 1
for comparison with Pr to decide whether to activate the synapse or not
ENDCOMMENT

VERBATIM
#ifndef NRN_VERSION_GTEQ_8_2_0
#include "nrnran123.h"
extern int cvode_active_;

#include <stdlib.h>
#include <stdio.h>
#include <math.h>

#ifndef CORENEURON_BUILD
double nrn_random_pick(void* r);
void* nrn_random_arg(int argpos);
#endif
#define RANDCAST
#else
#define RANDCAST (Rand*)
#endif

ENDVERBATIM
: ----------------------------------------------------------------
: initialization
INITIAL {
    VERBATIM
    if (cvode_active_ && !deterministic) {
        hoc_execerror("StochKv2 with deterministic=0", "cannot be used with cvode");
    }

    if( usingR123 ) {
        nrnran123_setseq((nrnran123_State*)_p_rng, 0, 0);
    }
    ENDVERBATIM

    eta = (gkbar / gamma) * (10000)
    trates(v)
    n=ninf
    l=linf
    scale_dens = gamma/area
    N = floor(eta*area + 0.5)

    N1L1 = n*l*N
    N1L0 = n*(1-l)*N
    N0L1 = (1-n)*l*N
    if( !deterministic) {
        N1L1 = floor(N1L1 + 0.5)
        N1L0 = floor(N1L0 + 0.5)
        N0L1 = floor(N0L1 + 0.5)
    }
    N0L0 = N - N1L1 - N1L0 - N0L1  : put rest into non-conducting state

    n0l0_n1l0 = 0
    n0l0_n0l1 = 0
    n1l0_n1l1 = 0
    n1l0_n0l0 = 0
    n0l1_n1l1 = 0
    n0l1_n0l0 = 0
    n1l1_n0l1 = 0
    n1l1_n1l0 = 0
}

: ----------------------------------------------------------------
: Breakpoint for each integration step
BREAKPOINT {
  SOLVE states METHOD cnexp

  gk = (strap(N1L1) * scale_dens) * (0.0001)

  ik = gk * (v - ek)
}


: ----------------------------------------------------------------
: states - updates number of channels in each state
DERIVATIVE states {

    trates(v)

    l' = al - (al + bl)*l
    n' = an - (an + bn)*n

    if (deterministic || dt > 1) { : ForwardSkip is also deterministic

      N1L1 = n*l*N
      N1L0 = n*(1-l)*N
      N0L1 = (1-n)*l*N

    }else{

      : ensure that N0 is an integer for when transitioning from deterministic mode to stochastic mode
      N1L1 = floor(N1L1 + 0.5)
      N1L0 = floor(N1L0 + 0.5)
      N0L1 = floor(N0L1 + 0.5)
      N0L0 = N - N1L1 - N1L0 - N0L1

      P_an = strap(an*dt)
      P_bn = strap(bn*dt)
      : check that will represent probabilities when used
      ChkProb(P_an)
      ChkProb(P_bn)

      : n gate transitions
      n0l0_n1l0 = BnlDev(P_an, N0L0)
      n0l1_n1l1 = BnlDev(P_an, N0L1)
      n1l1_n0l1 = BnlDev(P_bn, N1L1)
      n1l0_n0l0 = BnlDev(P_bn, N1L0)

      : move the channels
      N0L0 = strap(N0L0 - n0l0_n1l0 + n1l0_n0l0)
      N1L0 = strap(N1L0 - n1l0_n0l0 + n0l0_n1l0)
      N0L1 = strap(N0L1 - n0l1_n1l1 + n1l1_n0l1)
      N1L1 = strap(N1L1 - n1l1_n0l1 + n0l1_n1l1)

      : probabilities of making l gate transitions
      P_al = strap(al*dt)
      P_bl  = strap(bl*dt)
      : check that will represent probabilities when used
      ChkProb(P_al)
      ChkProb(P_bl)

      : number making l gate transitions
      n0l0_n0l1 = BnlDev(P_al,N0L0-n0l0_n1l0)
      n1l0_n1l1 = BnlDev(P_al,N1L0-n1l0_n0l0)
      n0l1_n0l0 = BnlDev(P_bl,N0L1-n0l1_n1l1)
      n1l1_n1l0 = BnlDev(P_bl,N1L1-n1l1_n0l1)

      : move the channels
      N0L0 = strap(N0L0 - n0l0_n0l1  + n0l1_n0l0)
      N1L0 = strap(N1L0 - n1l0_n1l1  + n1l1_n1l0)
      N0L1 = strap(N0L1 - n0l1_n0l0  + n0l0_n0l1)
      N1L1 = strap(N1L1 - n1l1_n1l0  + n1l0_n1l1)

    }

    N0L0 = N - N1L1 - N1L0 - N0L1  : put rest into non-conducting state
}

: ----------------------------------------------------------------
: trates - compute rates, using table if possible
PROCEDURE trates(v (mV)) {
    TABLE ntau,ltau,ninf,linf,al,bl,an,bn
    DEPEND dt
    FROM vmin TO vmax WITH 199

    v = v + 10
    linf = 1/(1+exp((-30(mV)-v)/10(mV)))
    ltau = 0.346(ms)*exp(-v/(18.272(mV)))+2.09(ms)

    ninf = 1/(1+exp(0.0878(1/mV)*(v+55.1(mV))))
    ntau = 2.1(ms)*exp(-v/21.2(mV))+4.627(ms)
    v = v - 10

    al = linf/ltau
    bl = 1/ltau - al
    an = ninf/ntau
    bn = 1/ntau - an
}

: ----------------------------------------------------------------
: sign trap - trap for negative values and replace with zero
FUNCTION strap(x) {
    if (x < 0) {
        strap = 0
VERBATIM
        fprintf (stderr,"skv.mod:strap: negative state");
ENDVERBATIM
    } else {
        strap = x
    }
}

: ----------------------------------------------------------------
: ChkProb - Check that number represents a probability
PROCEDURE ChkProb(p) {

  if (p < 0.0 || p > 1.0) {
    VERBATIM
    fprintf(stderr, "StochKv2.mod:ChkProb: argument not a probability.\n");
    ENDVERBATIM
  }

}

PROCEDURE setRNG() {

VERBATIM
    // For compatibility, allow for either MCellRan4 or Random123.  Distinguish by the arg types
    // Object => MCellRan4, seeds (double) => Random123
#ifndef CORENEURON_BUILD
    usingR123 = 0;
    if( ifarg(1) && hoc_is_double_arg(1) ) {
        nrnran123_State** pv = (nrnran123_State**)(&_p_rng);
        uint32_t a2 = 0;
        uint32_t a3 = 0;

        if (*pv) {
            nrnran123_deletestream(*pv);
            *pv = (nrnran123_State*)0;
        }
        if (ifarg(2)) {
            a2 = (uint32_t)*getarg(2);
        }
        if (ifarg(3)) {
            a3 = (uint32_t)*getarg(3);
        }
        *pv = nrnran123_newstream3((uint32_t)*getarg(1), a2, a3);
        usingR123 = 1;
    } else if( ifarg(1) ) {
        void** pv = (void**)(&_p_rng);
        *pv = nrn_random_arg(1);
    } else {
        void** pv = (void**)(&_p_rng);
        *pv = (void*)0;
    }
#endif
ENDVERBATIM
}

FUNCTION urand() {

VERBATIM
    double value;
    if( usingR123 ) {
        value = nrnran123_dblpick((nrnran123_State*)_p_rng);
    } else if (_p_rng) {
#ifndef CORENEURON_BUILD
        value = nrn_random_pick(RANDCAST _p_rng);
#endif
    } else {
        value = 0.5;
    }
    _lurand = value;
ENDVERBATIM
}

VERBATIM
static void bbcore_write(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
    if (d) {
        uint32_t* di = ((uint32_t*)d) + *offset;
      // temporary just enough to see how much space is being used
      if (!_p_rng) {
        di[0] = 0; di[1] = 0, di[2] = 0;
      }else{
        nrnran123_State** pv = (nrnran123_State**)(&_p_rng);
        nrnran123_getids3(*pv, di, di+1, di+2);
        // write stream sequence
        char which;
        nrnran123_getseq(*pv, di+3, &which);
        di[4] = (int)which;
      }
      //printf("StochKv3.mod %p: bbcore_write offset=%d %d %d\n", _p, *offset, d?di[0]:-1, d?di[1]:-1);
    }
    *offset += 5;
}
static void bbcore_read(double* x, int* d, int* xx, int* offset, _threadargsproto_) {
    uint32_t* di = ((uint32_t*)d) + *offset;
        if (di[0] != 0 || di[1] != 0|| di[2] != 0)
        {
      nrnran123_State** pv = (nrnran123_State**)(&_p_rng);
#if !NRNBBCORE
      if(*pv) {
          nrnran123_deletestream(*pv);
      }
#endif
      *pv = nrnran123_newstream3(di[0], di[1], di[2]);
      nrnran123_setseq(*pv, di[3], (char)di[4]);
        }
      //printf("StochKv3.mod %p: bbcore_read offset=%d %d %d\n", _p, *offset, di[0], di[1]);
    *offset += 5;
}
ENDVERBATIM

: Returns random numbers drawn from a binomial distribution
FUNCTION brand(P, N) {

VERBATIM
        /*
        :Supports separate independent but reproducible streams for
        : each instance. However, the corresponding hoc Random
        : distribution MUST be set to Random.uniform(0,1)
        */

        // Should probably be optimized
        double value = 0.0;
        int i;
        for (i = 0; i < _lN; i++) {
           if (urand(_threadargs_) < _lP) {
              value = value + 1;
           }
        }
        return(value);

ENDVERBATIM

        brand = value
}

VERBATIM
#define        PI 3.141592654
#define        r_ia     16807
#define        r_im     2147483647
#define        r_am     (1.0/r_im)
#define        r_iq     127773
#define        r_ir     2836
#define        r_ntab   32
#define        r_ndiv   (1+(r_im-1)/r_ntab)
#define        r_eps    1.2e-7
#define        r_rnmx   (1.0-r_eps)
ENDVERBATIM

VERBATIM
/* ---------------------------------------------------------------- */
/* gammln - compute natural log of gamma function of xx */
static double
gammln(double xx)
{
    double x,tmp,ser;
    static double cof[6]={76.18009173,-86.50532033,24.01409822,
        -1.231739516,0.120858003e-2,-0.536382e-5};
    int j;
    x=xx-1.0;
    tmp=x+5.5;
    tmp -= (x+0.5)*log(tmp);
    ser=1.0;
    for (j=0;j<=5;j++) {
        x += 1.0;
        ser += cof[j]/x;
    }
    return -tmp+log(2.50662827465*ser);
}
ENDVERBATIM


: ----------------------------------------------------------------
: BnlDev - draw a uniform deviate from the generator
FUNCTION BnlDev (ppr, nnr) {

VERBATIM
        int j;
        double am,em,g,angle,p,bnl,sq,bt,y;
        double pc,plog,pclog,en,oldg;

        /* prepare to always ignore errors within this routine */

        p=(_lppr <= 0.5 ? _lppr : 1.0-_lppr);
        am=_lnnr*p;
        if (_lnnr < 25) {
            bnl=0.0;
            for (j=1;j<=_lnnr;j++)
                if (urand(_threadargs_) < p) bnl += 1.0;
        }
        else if (am < 1.0) {
            g=exp(-am);
            bt=1.0;
            for (j=0;j<=_lnnr;j++) {
                bt *= urand(_threadargs_);
                if (bt < g) break;
            }
            bnl=(j <= _lnnr ? j : _lnnr);
        }
        else {
            {
                en=_lnnr;
                oldg=gammln(en+1.0);
            }
            {
                pc=1.0-p;
                plog=log(p);
                pclog=log(pc);
            }
            sq=sqrt(2.0*am*pc);
            do {
                do {
                    angle=PI*urand(_threadargs_);
                    angle=PI*urand(_threadargs_);
                    y=tan(angle);
                    em=sq*y+am;
                } while (em < 0.0 || em >= (en+1.0));
                em=floor(em);
                    bt=1.2*sq*(1.0+y*y)*exp(oldg-gammln(em+1.0) -
                    gammln(en-em+1.0)+em*plog+(en-em)*pclog);
            } while (urand(_threadargs_) > bt);
            bnl=em;
        }
        if (p != _lppr) bnl=_lnnr-bnl;

        /* recover error if changed during this routine, thus ignoring
            any errors during this routine */


        return bnl;

    ENDVERBATIM
    BnlDev = bnl
}

FUNCTION bbsavestate() {
        bbsavestate = 0
VERBATIM
 #ifndef CORENEURON_BUILD
        // TODO: since N0,N1 are no longer state variables, they will need to be written using this callback
        //  provided that it is the version that supports multivalue writing
        /* first arg is direction (-1 get info, 0 save, 1 restore), second is value*/
        double *xdir, *xval;
        #ifndef NRN_VERSION_GTEQ_8_2_0
        double *hoc_pgetarg();
        long nrn_get_random_sequence(void* r);
        void nrn_set_random_sequence(void* r, int val);
        #endif
        xdir = hoc_pgetarg(1);
        xval = hoc_pgetarg(2);
        if (_p_rng) {
                // tell how many items need saving
                if (*xdir == -1.) {
                    if( usingR123 ) {
                        *xdir = 2.0;
                    } else {
                        *xdir = 1.0;
                    }
                    return 0.0;
                }
                else if (*xdir == 0.) {
                    if( usingR123 ) {
                        uint32_t seq;
                        char which;
                        nrnran123_getseq( (nrnran123_State*)_p_rng, &seq, &which );
                        xval[0] = (double) seq;
                        xval[1] = (double) which;
                    } else {
                        xval[0] = (double)nrn_get_random_sequence(RANDCAST _p_rng);
                    }
                } else{
                    if( usingR123 ) {
                        nrnran123_setseq( (nrnran123_State*)_p_rng, (uint32_t)xval[0], (char)xval[1] );
                    } else {
                        nrn_set_random_sequence(RANDCAST _p_rng, (long)(xval[0]));
                    }
                }
        }

        // TODO: check for random123 and get the seq values
#endif
ENDVERBATIM
}
