# Tsodyks-Markram model examples

The Tsodyks-Markram model of short-term plasticity underwent many changes in the last twenty years.
In this folder we provide 2 examples to fit 2 different versions using BluePyOpt.

`tsodyksmarkramstp.ipynb` numerically integrates the "full version" of the TM model and fits a postsynaptic voltage trace:
\begin{equation}
\frac{dR(t)}{dt} = \frac{1-R(t)-E(t)}{D} - U(t)R(t)\delta(t-t_{spike})
\end{equation}
\begin{equation}
\frac{dE(t)}{dt} = \frac{-E}{\tau_{inac}} + U(t)R(t)\delta(t-t_{spike})
\end{equation}
\begin{equation}
\frac{dU(t)}{dt} = \frac{U_{SE}-U(t)}{F} + U_{SE}(1-U(t))\delta(t-t_{spike})
\end{equation}
\begin{equation}
\tau_{mem} \frac{dV(t)}{dt} = -V + R_{inp}I_{syn}(t)
\end{equation}
where $I_{syn}(t)=A_{SE}E(t)$

`tsodyksmarkramstp_multiplefreqs.ipynb` implements the event-based solution of the (reduced, but) more common version of the TM model:
\begin{equation}
R_{n+1} = 1 + (R_n - R_nU_n -1)e^{-\Delta_t/D}
\end{equation}
\begin{equation}
U_{n+1} = U_{SE} + U_n(1-U_{SE})e^{-\Delta_t/F}
\end{equation}
where the $n^{th}$ amplitude is $A_{SE}U_nR_n$. This implementation fits response amplitudes recorded at different stimulation frequencies (10, 20 and 40 Hz) for better generalization.
