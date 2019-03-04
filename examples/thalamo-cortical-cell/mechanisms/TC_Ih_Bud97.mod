: Ih current for thalamo-cortical neurons
: Ref.: Huguenard et al., 1997 (taum), Budde et al., 1997 (minf)

NEURON	{
	SUFFIX TC_ih_Bud97
	NONSPECIFIC_CURRENT ih
	RANGE gh_max, g_h, i_rec 
}

UNITS	{
	(S) = (siemens)
	(mV) = (millivolt)
	(mA) = (milliamp)
}

PARAMETER	{
	gh_max = 2.2e-5 (S/cm2) 
	e_h =  -43.0 (mV)
        celsius (degC)
	q10 = 4 :Santoro et al., 2000
		     
}

ASSIGNED	{
	v	(mV)
	ih	(mA/cm2)
	g_h	(S/cm2)
	mInf
	mTau
	tcorr		:Add temperature correction
	i_rec
}

STATE	{ 
	m
}

BREAKPOINT	{
	SOLVE states METHOD cnexp
	g_h = gh_max*m
	ih = g_h*(v-e_h)
	i_rec = ih
}

DERIVATIVE states	{
	rates()
	m' = (mInf-m)/mTau
}

INITIAL{
	rates()
	m = mInf
	tcorr = q10^((celsius-34)/10)  :EI: Recording temp. 34 C Huguenard
}

UNITSOFF
PROCEDURE rates(){
        mInf = 1/(1+exp((v+86.4)/11.2)) : Budde et al., 1997
        mTau = (1/(exp(-14.59 - 0.086*v) + exp(-1.87 + 0.0701*v )))/tcorr : From Huguenard, 1992, LJP?
}
UNITSON
