TITLE high threshold calcium current (L-current)

: From ModelDB, accession: 3808
: Based on the model by McCormick & Huguenard, J Neurophysiol, 1992
: and errata in https://huguenardlab.stanford.edu/reprints/Errata_thalamic_cell_models.pdf

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX TC_iL
	USEION ca READ cai,cao WRITE ica
        RANGE pcabar, m_inf, tau_m, ica, i_rec
}

UNITS {
	(mA)	= (milliamp)
	(mV)	= (millivolt)
	(molar) = (1/liter)
	(mM)	= (millimolar)
        FARADAY = (faraday) (coulomb)
        R       = 8.314 (volt-coul/degC)
}

PARAMETER {
	v			(mV)
	celsius			(degC)
        dt              	(ms)
	cai  = 0.5E-4    	(mM)
	cao  = 2		(mM)
	pcabar= 1e-4	        (cm/s)		
}

STATE {
	m
}

ASSIGNED {
	ica		(mA/cm2)
	i_rec		(mA/cm2)	
	tau_m		(ms)
	m_inf 
	tcorr
}

BREAKPOINT { 
	SOLVE states METHOD cnexp
	ica = pcabar * m*m * ghk(v,cai,cao)
	i_rec = ica
}

DERIVATIVE states {
       rates(v)

       m'= (m_inf-m) / tau_m 
}
  
INITIAL {
	rates(v)
	tcorr = 3^((celsius-23.5)/10)
	m = 0
}

UNITSOFF

FUNCTION ghk( v(mV), ci(mM), co(mM))  (millicoul/cm3) {
        LOCAL z, eci, eco
        z = v * (.001) * 2 *FARADAY / (R*(celsius+273.15))
	eco = co*efun(z)
	eci = ci*efun(-z)
	:high cao charge moves inward
	:negative potential charge moves inward
	ghk = (.001)*2*FARADAY*(eci - eco)
}

FUNCTION efun(z) {
	 if (fabs(z) < 1e-4) {
	    efun = 1 - z/2
	 }else{
	    efun = z/(exp(z) - 1)
         }
}

PROCEDURE rates(v(mV)) { LOCAL a,b
	a = 1.6 / (1+ exp(-0.072*(v-5)))
	b = 0.02 * vtrap( -(v-1.31), 5.36)

	tau_m = 1/(a+b) / tcorr
	m_inf = 1/(1+exp((v+10)/-10))
}

FUNCTION vtrap(x,c) { 
	: Traps for 0 in denominator of rate equations
        if (fabs(x/c) < 1e-6) {
          vtrap = c + x/2 }
        else {
          vtrap = x / (1-exp(-x/c)) }
}
UNITSON








